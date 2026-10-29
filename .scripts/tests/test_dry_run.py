"""Offline regression coverage for validation and privileged feedback boundaries."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import post_pr_feedback as feedback
import validate
import utils
from PIL import Image


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.network = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.sockets = patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden'))
        self.sockets.start()
        self.addCleanup(self.sockets.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def fixture(self, description='Play the best Minecraft minigames for free!'):
        for name in ('metadata.schema.json', 'inactive.schema.json'):
            shutil.copyfile(SCRIPTS.parent / name, self.root / name)
        (self.root / 'inactive.json').write_text('[]')
        server = self.root / 'servers' / 'hypixel'
        server.mkdir(parents=True)
        metadata = json.loads((SCRIPTS.parent / 'servers/hypixel/metadata.json').read_text())
        metadata['description'] = description
        (server / 'metadata.json').write_text(json.dumps(metadata))
        Image.new('RGBA', (512, 512)).save(server / 'logo.png')
        return server

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def run_validation(self, *args):
        before = self.snapshot()
        result = validate.main(['--dry-run', '--root', str(self.root), *args])
        self.assertEqual(before, self.snapshot(), 'Dry run modified local inputs or wrote artifacts')
        return result

    def test_english_ready_without_environment(self):
        self.fixture()
        self.assertEqual(self.run_validation(), 0)
        self.assertIn('/issues/1/labels', self.output.getvalue())
        self.assertNotIn('[dry-run] POST https://api.github.com/repos/LunarClient/ServerMappings/issues/1/comments', self.output.getvalue())

    def test_french_warning_is_non_blocking(self):
        self.fixture('Jouez gratuitement aux meilleurs mini-jeux Minecraft !')
        self.assertEqual(self.run_validation('--pr-number', '6023'), 0)
        output = self.output.getvalue()
        self.assertIn('/issues/6023/comments', output)
        self.assertIn('detected: `fr`', output)
        self.assertNotIn('REQUEST_CHANGES', output)

    def test_invalid_media_requests_changes_and_keeps_warning(self):
        server = self.fixture('Jouez gratuitement aux meilleurs mini-jeux Minecraft !')
        Image.new('RGB', (32, 16)).save(server / 'logo.png')
        self.assertEqual(self.run_validation(), 1)
        self.assertIn('REQUEST_CHANGES', self.output.getvalue())
        self.assertIn('/comments', self.output.getvalue())
        self.assertIn('DELETE', self.output.getvalue())

    def test_malformed_metadata(self):
        server = self.fixture()
        (server / 'metadata.json').write_text('{')
        self.assertEqual(self.run_validation(), 1)
        self.assertIn('malformed', self.output.getvalue())

    def test_root_failure_previews_feedback(self):
        self.fixture()
        (self.root / 'unwanted.txt').write_text('no')
        self.assertEqual(self.run_validation(), 1)
        self.assertIn('REQUEST_CHANGES', self.output.getvalue())

    def test_ambient_ci_environment_cannot_enable_side_effects(self):
        self.fixture()
        with patch.dict(os.environ, {'PR_ID': '999', 'GITHUB_TOKEN': 'secret', 'USE_ARGS': 'true',
                                    'RESULTS_FILE': 'unwanted.json', 'GITHUB_REPOSITORY': 'wrong/repo'}):
            self.assertEqual(self.run_validation(), 0)
        self.assertNotIn('secret', self.output.getvalue())
        self.assertNotIn('/999/', self.output.getvalue())

    def test_local_edited_inactive_server(self):
        self.fixture()
        (self.root / 'inactive.json').write_text('["hypixel"]')
        self.assertEqual(self.run_validation('--edited-server', 'hypixel'), 1)
        self.assertIn('being edited but is in the inactive file', self.output.getvalue())

    def test_changed_server_helper_dry_run_never_fetches(self):
        with patch.dict(os.environ, {'PR_ID': '1', 'GITHUB_TOKEN': 'secret'}):
            self.assertEqual(utils.get_edited_servers(dry_run=True, edited_servers=['a', 'a']), {'a'})

    def test_standalone_feedback_missing_artifact(self):
        feedback.main(['--dry-run', '--results-file', str(self.root / 'missing.json'), '--pr-number', '6023'])
        self.assertIn('DELETE', self.output.getvalue())
        self.assertIn('would remove', self.output.getvalue())

    def test_standalone_feedback_artifact_and_mismatch(self):
        path = self.root / 'results.json'
        path.write_text(json.dumps({'pr_id': 6023, 'status': 'ready', 'warnings': {'hypixel': ['French']}}))
        feedback.main(['--dry-run', '--results-file', str(path), '--pr-number', '6023'])
        self.assertIn('/comments', self.output.getvalue())
        self.output.seek(0); self.output.truncate()
        feedback.main(['--dry-run', '--results-file', str(path), '--pr-number', '1'])
        self.assertIn('refusing to act', self.output.getvalue())
        self.assertNotIn('[dry-run] POST', self.output.getvalue())

    def test_standalone_malformed_artifact_fails_cleanly(self):
        path = self.root / 'results.json'; path.write_text('{')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            feedback.main(['--dry-run', '--results-file', str(path)])
        self.assertEqual(error.exception.code, 2)

    def test_fork_lookup_dry_run_never_fetches(self):
        self.assertEqual(feedback.resolve_trusted_pr_numbers('owner/repo', 'sha', 'owner', 'branch', [], '', dry_run=True), set())
        self.assertIn('[dry-run] GET', self.output.getvalue())

    def test_corrupt_image_is_a_validation_error(self):
        server = self.fixture()
        (server / 'logo.png').write_bytes(b'not an image')
        self.assertEqual(self.run_validation(), 1)
        self.assertIn('Unable to validate logo.png', self.output.getvalue())

    def test_missing_inactive_file_is_a_validation_error(self):
        self.fixture()
        (self.root / 'inactive.json').unlink()
        self.assertEqual(self.run_validation(), 1)
        self.assertIn('Unable to load media inputs', self.output.getvalue())

    def test_short_description_skips_detection(self):
        self.fixture('Minecraft minigames!')
        with patch.object(validate, 'detect_langs', side_effect=AssertionError('Short text detection')):
            self.assertEqual(self.run_validation(), 0)

    def test_feedback_ignores_ambient_ci_environment(self):
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'secret', 'GITHUB_REPOSITORY': 'wrong/repo',
                                    'RESULTS_FILE': 'wrong.json', 'DOWNLOAD_OUTCOME': 'success',
                                    'WORKFLOW_RUN_PULL_REQUESTS': '[{"number":999}]'}):
            feedback.main(['--dry-run', '--results-file', str(self.root / 'missing.json')])
        self.assertIn('/issues/1/labels/', self.output.getvalue())
        self.assertNotIn('secret', self.output.getvalue())
        self.assertNotIn('wrong/repo', self.output.getvalue())

    def test_cli_from_root_scripts_and_unrelated_directory(self):
        import subprocess
        self.fixture()
        (self.root / '.scripts').mkdir()
        before = self.snapshot()
        for cwd in (self.root, self.root / '.scripts', SCRIPTS.parent.parent):
            process = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'validate.py'),
                                      '--dry-run', '--root', str(self.root)], cwd=cwd,
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertIn('/issues/1/labels', process.stdout)
        self.assertEqual(before, self.snapshot())

    def test_ci_root_error_writes_failed_artifact(self):
        self.fixture()
        (self.root / 'unexpected.txt').write_text('bad')
        artifact = self.root / '.scripts' / 'result.json'
        artifact.parent.mkdir()
        with patch.dict(os.environ, {'PR_ID': '7'}), patch.object(validate, 'RESULTS_FILE', str(artifact)):
            self.assertEqual(validate.main(['--root', str(self.root)]), 1)
        result = json.loads(artifact.read_text())
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Overall', result['errors'])

    def test_real_feedback_request_shapes_with_mocked_transport(self):
        response = Mock(status_code=200)
        response.json.return_value = []
        with patch('requests.request', return_value=response) as request:
            feedback.apply_feedback({'pr_id': 7, 'status': 'failed', 'errors': {'server': ['error']},
                                     'warnings': {'server': ['warning']}}, {7}, 'owner/repo', 'token')
        self.assertEqual([c.args[0] for c in request.call_args_list], ['DELETE', 'POST', 'GET', 'POST'])
        self.assertEqual(request.call_args_list[1].kwargs['json']['event'], 'REQUEST_CHANGES')
        self.assertEqual(request.call_args_list[3].kwargs['json']['body'], feedback.WARNING_MARKER + '\n' + feedback.build_warning_body({'server': ['warning']}))
        self.assertEqual(request.call_args_list[0].kwargs['headers']['Authorization'], 'Bearer token')

    def test_real_ready_and_missing_artifact_with_mocked_transport(self):
        response = Mock(status_code=200)
        response.json.return_value = []
        with patch('requests.request', return_value=response) as request:
            feedback.apply_feedback({'pr_id': 7, 'status': 'ready'}, {7}, 'owner/repo', 'token')
            self.assertEqual(request.call_args_list[0].kwargs['json'], {'labels': ['Ready for review']})
            request.reset_mock()
            feedback.apply_feedback(None, {7, 8}, 'owner/repo', 'token')
            self.assertEqual([c.args[0] for c in request.call_args_list], ['DELETE', 'DELETE'])
            request.reset_mock()
            feedback.apply_feedback({'pr_id': 9, 'status': 'ready'}, {7}, 'owner/repo', 'token')
            request.assert_not_called()

    def test_fork_lookup_requires_matching_sha(self):
        response = Mock(ok=True)
        response.json.return_value = [{'number': 7, 'head': {'sha': 'right'}}, {'number': 8, 'head': {'sha': 'wrong'}}]
        with patch('requests.request', return_value=response):
            self.assertEqual(feedback.resolve_trusted_pr_numbers('owner/repo', 'right', 'owner', 'branch', [], 'token'), {7})

    def test_ci_validation_writes_artifact_and_feedback_reads_it(self):
        self.fixture()
        artifact = self.root / '.scripts' / 'result.json'
        artifact.parent.mkdir()
        with patch.dict(os.environ, {'USE_ARGS': 'true', 'PR_ID': '7'}), \
             patch.object(validate, 'RESULTS_FILE', str(artifact)), \
             patch.object(validate, 'get_edited_servers', return_value=set()):
            result = validate.main(['--root', str(self.root), '--servers_dir', str(self.root / 'servers'),
                                    '--metadata_schema', str(self.root / 'metadata.schema.json'),
                                    '--inactive_file', str(self.root / 'inactive.json'),
                                    '--inactive_schema', str(self.root / 'inactive.schema.json'), '--no-validate_inactive'])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(artifact.read_text())['pr_id'], 7)
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'token', 'GITHUB_REPOSITORY': 'owner/repo',
                                    'RESULTS_FILE': str(artifact), 'DOWNLOAD_OUTCOME': 'success',
                                    'WORKFLOW_RUN_PULL_REQUESTS': '[{"number":7}]'}), \
             patch('requests.request', return_value=Mock(status_code=200, json=Mock(return_value=[]))) as request:
            feedback.main([])
        self.assertEqual(request.call_args_list[0].kwargs['json'], {'labels': ['Ready for review']})

    def test_pr_description_scope(self):
        server = self.fixture('Jouez gratuitement aux meilleurs mini-jeux Minecraft !')
        with tempfile.TemporaryDirectory() as base:
            baseline = Path(base) / 'hypixel'
            baseline.mkdir()
            metadata = json.loads((server / 'metadata.json').read_text())
            # Same description, different unrelated metadata: no language detection.
            metadata['name'] = 'Different name'
            (baseline / 'metadata.json').write_text(json.dumps(metadata))
            with patch.object(validate, 'detect_langs', side_effect=AssertionError('Unchanged description checked')):
                self.assertEqual(self.run_validation('--base-servers-dir', base), 0)
            # A changed description is checked and remains non-blocking.
            metadata['description'] = 'An English description in the base checkout.'
            (baseline / 'metadata.json').write_text(json.dumps(metadata))
            self.assertEqual(self.run_validation('--base-servers-dir', base), 0)
            self.assertIn('detected: `fr`', self.output.getvalue())
            # Newly added server also gets checked.
            (baseline / 'metadata.json').unlink()
            self.output.seek(0); self.output.truncate()
            self.assertEqual(self.run_validation('--base-servers-dir', base), 0)
            self.assertIn('detected: `fr`', self.output.getvalue())

    def test_pr_without_baseline_does_not_warn_about_every_server(self):
        from types import SimpleNamespace
        self.assertFalse(validate.description_needs_check(
            SimpleNamespace(skip_language_warnings=True), 'hypixel', 'French'))

    def comment(self, body, login='github-actions[bot]', kind='Bot'):
        return {'id': 42, 'body': feedback.WARNING_MARKER + '\n' + body,
                'user': {'login': login, 'type': kind}}

    def test_warning_comment_updated_resolved_and_unchanged(self):
        for old, new, should_patch in [('old', 'new', True), ('same', 'same', False), ('old', '', True)]:
            response = Mock(status_code=200)
            response.json.return_value = [self.comment(old)]
            with patch('requests.request', return_value=response) as request:
                feedback.post_comment('owner/repo', 7, new, 'token')
            methods = [call.args[0] for call in request.call_args_list]
            self.assertEqual(methods, ['GET', 'PATCH'] if should_patch else ['GET'])
            if should_patch:
                self.assertTrue(request.call_args.args[1].endswith('/issues/comments/42'))
                self.assertIn(new or 'No language warnings remain', request.call_args.kwargs['json']['body'])

    def test_comment_lookup_paginates_and_ignores_other_authors(self):
        response = Mock(status_code=200)
        response.json.side_effect = [[self.comment('spoof', 'contributor', 'User')] * 100,
                                    [self.comment('old')]]
        with patch('requests.request', return_value=response) as request:
            feedback.post_comment('owner/repo', 7, 'new', 'token')
        self.assertEqual([c.args[0] for c in request.call_args_list], ['GET', 'GET', 'PATCH'])
        self.assertEqual(request.call_args_list[1].kwargs['params']['page'], 2)

    def test_empty_warnings_do_not_create_comment(self):
        response = Mock(status_code=200)
        response.json.return_value = []
        with patch('requests.request', return_value=response) as request:
            feedback.post_comment('owner/repo', 7, '', 'token')
        self.assertEqual([c.args[0] for c in request.call_args_list], ['GET'])

    def test_comment_lookup_failure_never_creates_duplicate(self):
        response = Mock()
        response.raise_for_status.side_effect = RuntimeError('lookup failed')
        with patch('requests.request', return_value=response) as request:
            with self.assertRaises(RuntimeError):
                feedback.post_comment('owner/repo', 7, 'new', 'token')
        self.assertEqual(request.call_count, 1)


if __name__ == '__main__':
    unittest.main()
