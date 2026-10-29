# Local validation and feedback preview

Use Python 3.10 or newer. From the repository root, install dependencies into a
virtual environment:

```sh
python -m venv .venv
# Activate .venv (Windows PowerShell: .\.venv\Scripts\Activate.ps1)
python -m pip install -r .scripts/requirements.txt
python -B .scripts/validate.py --dry-run --pr-number 6023
```

This runs root, metadata, language and media validation, prints the would-be
`pr_results.json` payload, then previews every proposed GitHub label, blocking
review and warning comment. There are no network calls, tokens, CI environment
requirements, artifact writes, uploads or GitHub mutations. `-B` also prevents
Python from writing bytecode caches. Dependency installation is a separate setup
step that may need network access.

Warnings alone exit successfully (0); validation errors exit 1 and still preview
feedback. CLI/configuration errors exit 2. The PR number is a simulation target,
not a verified GitHub association; it defaults to 1. Existing CI environment
variables cannot turn `--dry-run` into a live run.

Paths default to the checkout containing the script, so it also works from
`.scripts` or another working directory. To validate a different local checkout:

```sh
python -B .scripts/validate.py --dry-run --root /path/to/ServerMappings --pr-number 6023
```

The validator checks all server folders present in that checkout; a sparse
checkout does not constitute validation of the complete repository. The
`--servers_dir`, `--metadata_schema`, `--inactive_file` and `--inactive_schema`
options override individual inputs. Explicit relative paths use the working
directory. `--validate_inactive` includes inactive servers.

GitHub's edited-file lookup is skipped in dry runs. Supply IDs explicitly to test
whether an edited server is inactive (this does not filter validation):

```sh
python -B .scripts/validate.py --dry-run --edited-server hypixel --edited-server example
```

To inspect an existing local artifact independently:

```sh
python -B .scripts/post_pr_feedback.py --dry-run --results-file /path/to/pr_results.json --pr-number 6023
```

The expected PR must match the artifact's `pr_id`; mismatches are rejected. A
missing artifact previews removal of a stale ready label. Malformed JSON fails
without sending anything. `--repository owner/repo` changes only the preview
URL. Local preview arguments are rejected unless `--dry-run` is present.

Without `--dry-run`, feedback retains the privileged CI path: it requires
`GITHUB_TOKEN`, `GITHUB_REPOSITORY`, and `RESULTS_FILE`, checks
`DOWNLOAD_OUTCOME`, and derives trusted PR numbers from `WORKFLOW_RUN_*` metadata
or the head/SHA lookup before applying feedback. Never use that mode as a local
smoke test. Validation's `USE_ARGS=true` invocation and artifact format remain
compatible with the existing workflow.

The local command covers validation and feedback. It does not invoke workflow
artifact upload/download actions, server pings, media/index publishing, Crowdin,
R2 uploads, or Cloudflare cache purging. Those are separate jobs, not required to
test validation. `convert_media.py --dry_upload` is a separate existing option;
it is not the side-effect-free validation preview described here.

## Tests

```sh
python -B -m unittest discover -s .scripts/tests -v
```

Tests use temporary metadata/media fixtures (including the French description),
block network transport for in-process validation and feedback tests, compare
filesystem contents before/after dry runs, and mock real CI API calls. Tests do not alter production server metadata. No tests post comments, modify labels, submit
reviews, or call live mutating APIs.

## Language warning scope and comment updates

CI compares description values with the trusted base checkout. Only newly added
or changed descriptions receive language warnings; other validation still covers
all active servers. A PR run without a base directory skips language warnings
rather than reporting unrelated existing descriptions.

For a local PR-style comparison, use an existing base checkout:

```sh
python -B .scripts/validate.py --dry-run --base-servers-dir /path/to/base/servers
```

Without that option, local dry runs remain full language audits. CI supplies
`BASE_SERVERS_DIR`; dry runs ignore that environment variable.

Warning feedback finds its marked `github-actions[bot]` comment across all pages,
updates it when warnings change, and marks it resolved when none remain. Identical
feedback causes no comment write. Human comments and old unmarked comments are
left alone. Feedback runs for the same source branch are serialized. Dry runs
preview lookup and creation with an empty simulated comment history; update and
resolution paths are covered by offline mocked tests.
