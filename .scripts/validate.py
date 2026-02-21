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
from utils import get_all_servers, get_edited_servers, validate_background, validate_banner, validate_logo, validate_wordmark, get_all_versions

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
    "minecraft.horse"
]

def main():
    use_args = os.getenv("USE_ARGS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=use_args, type=str)
    parser.add_argument("--metadata_schema", required=use_args, type=str)
    parser.add_argument("--inactive_file", required=use_args, type=str)
    parser.add_argument("--inactive_schema", required=use_args, type=str)
    parser.add_argument("--validate_inactive", action=argparse.BooleanOptionalAction)
    arguments = parser.parse_args()

    if not use_args:
        validate_root("..")
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace("\\", "/")
        arguments.inactive_schema = local + "/inactive.schema.json"
        arguments.inactive_file = local + "/inactive.json"
        arguments.metadata_schema = local + "/metadata.schema.json"
        arguments.servers_dir = local + "/servers"
        arguments.validate_inactive = False
    else:
        validate_root()

    metadata_errors = check_metadata(arguments)
    all_errors = check_media(arguments, metadata_errors)

    pull_id = os.getenv("PR_ID")
    if all(len(section) == 0 for section in all_errors.values()):
        if pull_id:
            res = requests.post(
                f"https://api.github.com/repos/LunarClient/ServerMappings/issues/{pull_id}/labels",
                json={"labels": ["Ready for review"]},
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {os.getenv('BOT_PAT')}",
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
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {os.getenv('BOT_PAT')}",
                },
                timeout=30,
            )
            res.raise_for_status()

        post_comment(all_errors)
        print(all_errors)
        sys.exit(1)

