"""
This module is used for validating servers within ServerMappings! It checks metadata, media files,
and ensures no unwanted files are present in the root directory. If there are any validation errors
within a submitters Pull Request, it will submit those as part of a comment on the PR to ensure
they can be fixed before merging.
"""
import argparse
import json
import os
import sys
import jsonschema
import requests
from tld.utils import get_tld
from collections import defaultdict
from utils import (
    get_all_servers,
    get_edited_servers,
    validate_background,
    validate_banner,
    validate_logo,
    validate_wordmark,
    get_all_versions,
)

FILE_WHITELIST = [
    ".DS_Store",
    ".pylintrc",
    ".venv",
    ".git",
    ".github",
    ".gitignore",
    "inactive.json",
    "inactive.schema.json",
    "discord-logo-uploaded.json",
    "LICENSE",
    "metadata.example.json",
    "metadata.schema.json",
    "README.md",
    ".scripts",
    ".vscode",
    "servers",
    "docs",
    "logo.png",
]

HOSTING_DOMAIN_BLACKLIST = [
    "mc.gg",
    "apexmc.co",
    "smp.fan",
    "modpack.lol",
    "minecraft.vodka",
    "minecraft.horse",
]


def main():
    """
    Main function to parse arguments and validate servers.
    """
    use_args = os.getenv("USE_ARGS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=use_args, type=str)
    parser.add_argument("--inactive_schema", required=use_args, type=str)
    parser.add_argument("--inactive_file", required=use_args, type=str)
    parser.add_argument("--metadata_schema", required=use_args, type=str)
    parser.add_argument("--validate_inactive", action=argparse.BooleanOptionalAction)
    arguments = parser.parse_args()

    # If running locally
    if not use_args:
        validate_root("..")
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace(
            "\\", "/"
        )
        arguments.servers_dir = local + "/servers"
        arguments.inactive_schema = local + "/inactive.schema.json"
        arguments.inactive_file = local + "/inactive.json"
        arguments.metadata_schema = local + "/metadata.schema.json"
        arguments.validate_inactive = False

    metadata_errors = check_metadata(arguments)
    all_errors = check_media(arguments, metadata_errors)

    pull_id = os.getenv("PR_ID")

    if all(len(section) == 0 for section in all_errors.values()):
        if pull_id:
            res = requests.post(
                f"https://api.github.com/repos/LunarClient/ServerMappings/issues/{pull_id}/labels",
                json={"labels": ["ready for review"]},
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Token {os.getenv('BOT_PAT')}",
                },
                timeout=30,
            )
            res.raise_for_status()

        print("No errors occured. PR is ready for manual review.")
        sys.exit(0)
    else:
        if pull_id:
            res = requests.delete(
                f"https://api.github.com/repos/LunarClient/ServerMappings/issues/{pull_id}/labels",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"Token {os.getenv('BOT_PAT')}",
                },
                timeout=30,
            )
            res.raise_for_status()

        post_comment(all_errors)
        print(all_errors)
        sys.exit(1)


def post_comment(messages: dict[str, list[str]]):
    """
    Posts validation errors as a PR review comment.
    """
    pull_id = os.getenv("PR_ID")
    if not pull_id:
        print("Errors happened but there was no PR_ID found..?")
        print(messages)
        sys.exit(1)

    comment = ""
    for server_id, errors in messages.items():
        if not errors:
            continue
        comment += f"\n\nErrors found for **{server_id}**:\n- " + "\n- ".join(errors)

    requests.post(
        f"https://api.github.com/repos/LunarClient/ServerMappings/pulls/{pull_id}/reviews",
        json={"body": comment, "event": "REQUEST_CHANGES"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Token {os.getenv('BOT_PAT')}",
        },
        timeout=30,
    )


def check_metadata(args: argparse.Namespace) -> defaultdict[str, list[str]]:
    messages = defaultdict(list)

    # Load inactive schema
    try:
        with open(args.inactive_schema, encoding="UTF-8") as f:
            inactive_schema = json.load(f)
    except Exception:
        messages["Overall"].append("Unable to load inactive schema.")
        inactive_schema = {}

    # Load inactive file
    try:
        with open(args.inactive_file, encoding="UTF-8") as f:
            inactive_file = json.load(f)
    except Exception:
        messages["Overall"].append("Unable to load inactive.json.")
        inactive_file = []

    try:
        jsonschema.validate(instance=inactive_file, schema=inactive_schema)
    except jsonschema.ValidationError:
        messages["Overall"].append("inactive.json does not match schema.")

    # Load metadata schema
    try:
        with open(args.metadata_schema, encoding="UTF-8") as f:
            metadata_schema = json.load(f)
    except Exception:
        messages["Overall"].append("Unable to load metadata schema.")
        metadata_schema = {}

    seen_domains = defaultdict(set)

    for root, _, _ in os.walk(args.servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if (
            not server_id
            or server_id == args.servers_dir
            or (not args.validate_inactive and server_id in inactive_file)
        ):
            continue

        metadata_path = f"{args.servers_dir}/{server_id}/metadata.json"

        try:
            with open(metadata_path, encoding="UTF-8") as f:
                server = json.load(f)
        except Exception:
            messages["Overall"].append(f"Unable to open metadata.json for {server_id}")
            continue

        try:
            jsonschema.validate(instance=server, schema=metadata_schema)
        except jsonschema.ValidationError as e:
            messages[server_id].append(str(e))

        # Domain validation
        for address in server.get("addresses", []):
            domain = get_tld(address, as_object=True, fail_silently=True, fix_protocol=True)
            if domain and domain.fld in HOSTING_DOMAIN_BLACKLIST:
                messages[server_id].append(
                    f"{domain.fld} belongs to a hosting provider."
                )
            elif not domain:
                messages[server_id].append(f"{address} is not a valid domain.")

    return messages


def check_media(args, current_errors):
    servers = get_all_servers(
        args.servers_dir,
        args.inactive_file,
        args.validate_inactive,
    )

    for server in servers:
        server_id = server["id"]
        server_name = server["name"]

        logo_errors = validate_logo(
            f"{args.servers_dir}/{server_id}/logo.png", server_name
        )
        background_errors = validate_background(
            f"{args.servers_dir}/{server_id}/background.png", server_name
        )
        wordmark_errors = validate_wordmark(
            f"{args.servers_dir}/{server_id}/wordmark.png", server_name
        )

        banner_path = None
        if os.path.exists(f"{args.servers_dir}/{server_id}/banner.png"):
            banner_path = f"{args.servers_dir}/{server_id}/banner.png"
        elif os.path.exists(f"{args.servers_dir}/{server_id}/banner.gif"):
            banner_path = f"{args.servers_dir}/{server_id}/banner.gif"

        banner_errors = (
            validate_banner(banner_path, server_name) if banner_path else []
        )

        if any([logo_errors, background_errors, banner_errors, wordmark_errors]):
            current_errors[server_id] += (
                logo_errors + background_errors + banner_errors + wordmark_errors
            )

    return current_errors


def validate_root(directory: str = "."):
    server_dir = directory + "/servers/"
    for file in os.listdir(directory):
        if file not in FILE_WHITELIST:
            print(f"File '{file}' not allowed in root.")
            sys.exit(1)

    for file in os.listdir(server_dir):
        if os.path.isfile(server_dir + file):
            print(f"'{file}' is not a directory in /servers/")
            sys.exit(1)


if __name__ == "__main__":
    main()
