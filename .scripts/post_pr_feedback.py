"""
Post-validation feedback for ServerMappings PRs.

Triggered by the workflow_run job in the trusted base-repo context. Reads
pr_results.json (uploaded by the validate-servers job that ran in the
untrusted PR context) and either applies a "Ready for review" label or
posts a review with the validation errors.

Because pr_results.json is produced by code controlled by the PR author,
its pr_id field cannot be trusted. The trusted PR number is derived from
the workflow_run payload (with a head-branch lookup as a fallback for
fork PRs, whose pull_requests array is empty) and the artifact's pr_id
is rejected if it doesn't match one of those numbers.
"""

import argparse
import json
import os

import requests

API_ROOT = "https://api.github.com"
READY_LABEL = "Ready for review"
WARNING_MARKER = "<!-- servermappings-language-warnings -->"


def gh_request(method: str, path: str, token: str, *, dry_run=False, **kwargs) -> requests.Response:
    if dry_run:
        print(f"[dry-run] {method} {API_ROOT}{path}")
        print(json.dumps(kwargs, indent=2, ensure_ascii=True))
        response = requests.Response()
        response.status_code = 200
        response._content = b"[]"
        return response
    return requests.request(
        method,
        f"{API_ROOT}{path}",
        headers={
            "accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
        **kwargs,
    )


def resolve_trusted_pr_numbers(
    repo: str,
    head_sha: str,
    head_owner: str,
    head_branch: str,
    pr_payload: list,
    token: str,
    *, dry_run=False,
) -> set[int]:
    """Return PR numbers that are safe to act on with the privileged token."""
    numbers: set[int] = set()
    for pr in pr_payload or []:
        if isinstance(pr, dict) and isinstance(pr.get("number"), int):
            numbers.add(pr["number"])

    if numbers or not head_sha or not head_owner or not head_branch:
        return numbers

    res = gh_request(
        "GET",
        f"/repos/{repo}/pulls",
        token,
        dry_run=dry_run,
        params={"head": f"{head_owner}:{head_branch}", "state": "open"},
    )
    if not res.ok:
        print(
            f"::warning::Failed to look up PRs for {head_owner}:{head_branch}: "
            f"{res.status_code} {res.text}"
        )
        return numbers

    for pr in res.json():
        if pr.get("head", {}).get("sha") == head_sha:
            numbers.add(int(pr["number"]))
    return numbers


def remove_ready_label(repo: str, pr_number: int, token: str, *, dry_run=False) -> None:
    encoded = requests.utils.quote(READY_LABEL, safe="")
    res = gh_request(
        "DELETE", f"/repos/{repo}/issues/{pr_number}/labels/{encoded}", token,
        dry_run=dry_run,
    )
    if res.status_code not in (200, 204, 404):
        res.raise_for_status()


def add_ready_label(repo: str, pr_number: int, token: str, *, dry_run=False) -> None:
    res = gh_request(
        "POST",
        f"/repos/{repo}/issues/{pr_number}/labels",
        token,
        json={"labels": [READY_LABEL]},
        dry_run=dry_run,
    )
    res.raise_for_status()


def request_changes(repo: str, pr_number: int, body: str, token: str, *, dry_run=False) -> None:
    res = gh_request(
        "POST",
        f"/repos/{repo}/pulls/{pr_number}/reviews",
        token,
        json={"event": "REQUEST_CHANGES", "body": body},
        dry_run=dry_run,
    )
    res.raise_for_status()


def post_comment(repo: str, pr_number: int, body: str, token: str, *, dry_run=False) -> None:
    """Maintain a single marked GitHub Actions comment, including resolution."""
    existing = None
    page = 1
    while True:
        res = gh_request("GET", f"/repos/{repo}/issues/{pr_number}/comments", token,
                         params={"per_page": 100, "page": page}, dry_run=dry_run)
        res.raise_for_status()
        comments = res.json()
        for comment in comments:
            author = comment.get("user") or {}
            if (author.get("login") == "github-actions[bot]" and author.get("type") == "Bot"
                    and (comment.get("body") or "").startswith(WARNING_MARKER)):
                existing = comment
                break
        if existing or len(comments) < 100:
            break
        page += 1
    if not body and not existing:
        return
    desired = WARNING_MARKER + "\n" + (body or "No language warnings remain for descriptions changed in this PR.")
    if existing:
        if existing.get("body") == desired:
            return
        method = "PATCH"
        path = f"/repos/{repo}/issues/comments/{existing['id']}"
    else:
        method = "POST"
        path = f"/repos/{repo}/issues/{pr_number}/comments"
    res = gh_request(method, path, token, json={"body": desired}, dry_run=dry_run)
    res.raise_for_status()


def build_review_body(errors: dict) -> str:
    body = ""
    for server_id, msgs in (errors or {}).items():
        if not msgs:
            continue
        joined = "\n- ".join(msgs)
        body += f"\n\nErrors found for **{server_id}**:\n- {joined}"
    return body


def build_warning_body(warnings: dict) -> str:
    """
    Non-blocking warnings (e.g. a description that looks like it might not be
    English) are posted as a plain comment rather than a review, so they never
    affect the "Ready for review" label or block merging on their own.
    """
    body = ""
    for server_id, msgs in (warnings or {}).items():
        if not msgs:
            continue
        joined = "\n- ".join(msgs)
        body += f"\n\nFor **{server_id}**:\n- {joined}"
    if not body:
        return ""
    return (
        "⚠️ A few things worth double-checking (these don't block this PR):"
        + body
    )


def apply_feedback(data, trusted, repo, token="", *, dry_run=False):
    """Apply or preview feedback; never trust the artifact's PR number alone."""
    if data is None:
        for number in sorted(trusted):
            remove_ready_label(repo, number, token, dry_run=dry_run)
        print("Validation artifact missing - " +
              ("would remove stale ready label." if dry_run else "removed stale ready label."))
        return

    pr_id = data.get("pr_id")
    if not isinstance(pr_id, int) or pr_id not in trusted:
        print(
            f"::warning::Artifact pr_id ({pr_id!r}) does not match trusted "
            f"PR number(s) {sorted(trusted)}; refusing to act on it."
        )
        return

    if data.get("status") == "ready":
        add_ready_label(repo, pr_id, token, dry_run=dry_run)
    else:
        remove_ready_label(repo, pr_id, token, dry_run=dry_run)

        body = build_review_body(data.get("errors") or {})
        if body:
            request_changes(repo, pr_id, body, token, dry_run=dry_run)

    warning_body = build_warning_body(data.get("warnings") or {})
    post_comment(repo, pr_id, warning_body, token, dry_run=dry_run)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview requests without network access or writes; ignores CI environment.")
    parser.add_argument("--results-file", help="Local validation JSON (dry run only).")
    parser.add_argument("--pr-number", type=int, help="Expected PR for local preview (default: 1).")
    parser.add_argument("--repository", help="Preview target (default: LunarClient/ServerMappings).")
    args = parser.parse_args(argv)
    if args.dry_run:
        print("[dry-run] No network requests or writes. PR association is simulated locally.")
        token = ""
        repo = args.repository or "LunarClient/ServerMappings"
        trusted = {args.pr_number if args.pr_number is not None else 1}
        if min(trusted) <= 0:
            parser.error("--pr-number must be positive")
        results_file = args.results_file or "pr_results.json"
        artifact_present = os.path.isfile(results_file)
    else:
        if any(value is not None for value in (args.results_file, args.pr_number, args.repository)):
            parser.error("local preview arguments require --dry-run")
        required = ("GITHUB_TOKEN", "GITHUB_REPOSITORY", "RESULTS_FILE")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            parser.error("Missing CI environment: " + ", ".join(missing) + "; use --dry-run locally")
        token = os.environ["GITHUB_TOKEN"]
        repo = os.environ["GITHUB_REPOSITORY"]
        results_file = os.environ["RESULTS_FILE"]
        try:
            pr_payload = json.loads(os.environ.get("WORKFLOW_RUN_PULL_REQUESTS") or "[]")
        except json.JSONDecodeError:
            pr_payload = []
        trusted = resolve_trusted_pr_numbers(
            repo, os.environ.get("WORKFLOW_RUN_HEAD_SHA", ""),
            os.environ.get("WORKFLOW_RUN_HEAD_OWNER", ""),
            os.environ.get("WORKFLOW_RUN_HEAD_BRANCH", ""), pr_payload, token,
        )
        artifact_present = os.environ.get("DOWNLOAD_OUTCOME") == "success" and os.path.isfile(results_file)
    if not trusted:
        print("No PR could be associated with this workflow run; nothing to do.")
        return
    data = None
    if artifact_present:
        try:
            with open(results_file, encoding="utf-8") as results:
                data = json.load(results)
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
        except (OSError, ValueError) as exc:
            parser.error(f"Cannot read validation artifact: {exc}")
    apply_feedback(data, trusted, repo, token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
