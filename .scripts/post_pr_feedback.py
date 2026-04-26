"""
Post-validation feedback for ServerMappings PRs.

Triggered by the workflow_run job in the trusted base-repo context. Reads
pr_results.json (uploaded by the validate-servers job that ran in the
untrusted PR context) and either applies a "Ready for review" label or
posts a review with the validation errors.

Because pr_results.json is produced by code controlled by the PR author,
its pr_id field cannot be trusted. The trusted PR number is derived from
the workflow_run payload (with a head-SHA lookup as a fallback for fork
PRs, whose pull_requests array is empty) and the artifact's pr_id is
rejected if it doesn't match one of those numbers.
"""

import json
import os

import requests

API_ROOT = "https://api.github.com"
READY_LABEL = "Ready for review"
RESULTS_FILE = "pr_results.json"


def gh_request(method: str, path: str, token: str, **kwargs) -> requests.Response:
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
    repo: str, head_sha: str, pr_payload: list, token: str
) -> set[int]:
    """Return PR numbers that are safe to act on with the privileged token."""
    numbers: set[int] = set()
    for pr in pr_payload or []:
        if isinstance(pr, dict) and isinstance(pr.get("number"), int):
            numbers.add(pr["number"])

    if numbers or not head_sha:
        return numbers

    res = gh_request("GET", f"/repos/{repo}/commits/{head_sha}/pulls", token)
    if not res.ok:
        print(
            f"::warning::Failed to look up PRs for head SHA {head_sha}: "
            f"{res.status_code} {res.text}"
        )
        return numbers

    for pr in res.json():
        if pr.get("state") == "open":
            numbers.add(int(pr["number"]))
    return numbers


def remove_ready_label(repo: str, pr_number: int, token: str) -> None:
    encoded = requests.utils.quote(READY_LABEL, safe="")
    res = gh_request(
        "DELETE", f"/repos/{repo}/issues/{pr_number}/labels/{encoded}", token
    )
    if res.status_code not in (200, 204, 404):
        res.raise_for_status()


def add_ready_label(repo: str, pr_number: int, token: str) -> None:
    res = gh_request(
        "POST",
        f"/repos/{repo}/issues/{pr_number}/labels",
        token,
        json={"labels": [READY_LABEL]},
    )
    res.raise_for_status()


def request_changes(repo: str, pr_number: int, body: str, token: str) -> None:
    res = gh_request(
        "POST",
        f"/repos/{repo}/pulls/{pr_number}/reviews",
        token,
        json={"event": "REQUEST_CHANGES", "body": body},
    )
    res.raise_for_status()


def build_review_body(errors: dict) -> str:
    body = ""
    for server_id, msgs in (errors or {}).items():
        if not msgs:
            continue
        joined = "\n- ".join(msgs)
        body += f"\n\nErrors found for **{server_id}**:\n- {joined}"
    return body


def main() -> None:
    token = os.environ["BOT_PAT"]
    repo = os.environ["GITHUB_REPOSITORY"]
    head_sha = os.environ.get("WORKFLOW_RUN_HEAD_SHA", "")
    conclusion = os.environ.get("WORKFLOW_RUN_CONCLUSION", "")
    download_outcome = os.environ.get("DOWNLOAD_OUTCOME", "")

    try:
        pr_payload = json.loads(os.environ.get("WORKFLOW_RUN_PULL_REQUESTS") or "[]")
    except json.JSONDecodeError:
        pr_payload = []

    trusted = resolve_trusted_pr_numbers(repo, head_sha, pr_payload, token)
    if not trusted:
        print("No PR could be associated with this workflow run; nothing to do.")
        return

    artifact_present = (
        conclusion == "success"
        and download_outcome == "success"
        and os.path.isfile(RESULTS_FILE)
    )

    if not artifact_present:
        for n in trusted:
            remove_ready_label(repo, n, token)
        print(
            "Upstream did not succeed or artifact missing — "
            "removed stale ready label."
        )
        return

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    pr_id = data.get("pr_id")
    if not isinstance(pr_id, int) or pr_id not in trusted:
        print(
            f"::warning::Artifact pr_id ({pr_id!r}) does not match trusted "
            f"PR number(s) {sorted(trusted)}; refusing to act on it."
        )
        return

    if data.get("status") == "ready":
        add_ready_label(repo, pr_id, token)
        return

    remove_ready_label(repo, pr_id, token)

    body = build_review_body(data.get("errors") or {})
    if not body:
        return

    request_changes(repo, pr_id, body, token)


if __name__ == "__main__":
    main()
