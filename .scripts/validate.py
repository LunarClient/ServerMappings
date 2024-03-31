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
from utils import get_all_servers, validate_background, validate_banner, validate_logo, validate_wordmark

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
]


def main():
    """
    Main function to parse arguments and validate servers.
    """
    use_args = os.getenv("USE_ARGS") == "true"
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=use_args, type=str)
    parser.add_argument("--metadata_schema", required=use_args, type=str)
    parser.add_argument("--inactive_file", required=use_args, type=str)
    parser.add_argument("--inactive_schema", required=use_args, type=str)
    parser.add_argument("--validate_inactive", action=argparse.BooleanOptionalAction)
    arguments = parser.parse_args()

    # If we don't find the env variable for use args assume we're running this locally
    if not use_args:
        validate_root("..")
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace(
            "\\", "/"
        )
        arguments.inactive_schema = local + "/inactive.schema.json"
        arguments.inactive_file = local + "/inactive.json"
        arguments.metadata_schema = local + "/metadata.schema.json"
        arguments.servers_dir = local + "/servers"
        arguments.validate_inactive = False
    else:
        validate_root()

    metadata_errors = check_metadata(arguments)
    all_errors = check_media(arguments, metadata_errors)

    # If no errors happened for anything above add ready for review tag.
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
        # Remove previously added labels if there is a pull_id
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

        # Post Feedback
        post_comment(all_errors)
        print(all_errors)
        sys.exit(1)


def post_comment(messages: dict[str, list[str]]):
    """
    This method posts the validation errors from the servers as a comment on the pull request with
    the author being LunarClientBot.

    Parameters:
        messages (dict[str, list[str]]): A dictionary containing the validation errors. The keys
                                         are server IDs and the values are lists of error messages.
    """

    # Check for Pull Request ID, wont be present if running locally
    pull_id = os.getenv("PR_ID")
    if not pull_id:
        print("Errors happened but there was no PR_ID found..?")
        print(messages)
        exit(0)

    # Build comment
    comment = ""
    for server_id, errors in messages.items():
        if len(errors) == 0:
            continue

        comment += f"\n\nErrors found for **{server_id}**:\n- " + "\n- ".join(errors)

    # Request changes
    requests.post(
        f"https://api.github.com/repos/LunarClient/ServerMappings/pulls/{pull_id}/reviews",
        json={"body": comment, "event": "REQUEST_CHANGES"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Token {os.getenv('BOT_PAT')}",
        },
        timeout=30,
    )


def check_metadata(args: argparse.Namespace) -> dict[str, list[str]]:
    """
    This function checks all of the json files and validates them with their appropriate schemas.

    Parameters:
        args (argparse.Namespace): The command-line arguments passed to the script.

    Returns:
        dict[str, list[str]]: A dictionary mapping server IDs to lists of validation error messages.
    """
    messages = {"Overall": []}

    # Validate Inactive File
    inactive_schema = {}
    try:
        with open(args.inactive_schema, encoding="UTF-8") as inactive_schema_file:
            try:
                inactive_schema = json.load(inactive_schema_file)
            except json.decoder.JSONDecodeError:
                messages["Overall"].append(
                    "Unable to load the inactive schema file. Please don't mess with this!"
                )
    except Exception:
        messages["Overall"].append(
            "Unable to open the inactive schema file. Please don't mess with this!"
        )

    inactive_file = []
    try:
        with open(args.inactive_file, encoding="UTF-8") as inactive_file_file:
            try:
                inactive_file = json.load(inactive_file_file)
            except json.decoder.JSONDecodeError:
                messages["Overall"].append(
                    "Unable to open inactive.json. Did you modify it?"
                )
    except Exception:
        messages["Overall"].append(
            "Unable to open the inactive.json file. Please don't mess with this!"
        )

    print("Validating inactive.json file...")

    try:
        jsonschema.validate(instance=inactive_file, schema=inactive_schema)
    except jsonschema.ValidationError:
        messages["Overall"].append(
            "inactive.json no longer matches the schema. Did you modify it?"
        )

    print("Successfully validated inactive.json file!")

    # Load server mappings Schema
    metadata_schema = {}
    try:
        with open(args.metadata_schema, encoding="UTF-8") as schema_file:
            try:
                metadata_schema = json.load(schema_file)
            except json.decoder.JSONDecodeError:
                messages["Overall"].append(
                    "Unable to load the metadata schema file. Please don't mess with this!"
                )
    except Exception:
        messages["Overall"].append(
            "Unable to open the metadata schema file. Please don't mess with this!"
        )

    # Looping over each server folder
    for root, _, _ in os.walk(args.servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if (
            not server_id
            or server_id == args.servers_dir
            or not args.validate_inactive
            and server_id in inactive_file
        ):
            continue

        # Open metadata.json
        try:
            with open(
                f"{args.servers_dir}/{server_id}/metadata.json", encoding="UTF-8"
            ) as server_file:
                try:
                    server = json.load(server_file)
                    if server["id"] != server_id:
                        messages[server_id] = [
                            f"The ID field in the metadata.json does not match the file name of {server_id}.json (got {server['id']})"
                        ]
                        continue
                except json.decoder.JSONDecodeError:
                    messages[server_id] = [
                        "metadata.json is malformed, please ensure it is valid json."
                    ]
                    continue  # Don't attempt to verify broken json files.
        except Exception:
            messages["Overall"].append(
                f"Unable to open metadata.json for {server_id} - Did you name the server id correctly?"
            )
            continue  # Don't attempt to verify broken json files.

        print(
            f'Validating {server_id}\'s metadata.json file {"(inactive)" if server_id in inactive_file else ""}...'
        )

        # Validate!
        try:
            jsonschema.validate(instance=server, schema=metadata_schema)
            print(f"Successfully validated {server_id}'s metadata.json file!")
        except jsonschema.ValidationError:
            if server_id not in messages:
                messages[server_id] = []

            # Get all the errors that are in the json and add to messages
            errors = jsonschema.Draft7Validator(metadata_schema).iter_errors(server)
            enumn_errors = {}
            for error in errors:
                # Clean path
                path = error.json_path
                if "$." in path:
                    path = path.split("$.")[1]
                if "[" in path:
                    path = path.split("[")[0]

                if error.validator == "enum":
                    enum = "".join([f"   - {s}\n" for s in error.validator_value])
                    incorrect_values = enumn_errors.get(
                        path,
                        {
                            "incorrect": [],
                            "enum": enum,
                        },
                    )
                    incorrect_values["incorrect"].append(error.instance)
                    enumn_errors[path] = incorrect_values
                elif error.validator == "pattern":
                    messages[server_id].append(
                        f'"{error.instance}" does not match the regex pattern "{error.validator_value}" in '
                        f"`{path}` please use [this](https://regex101.com/) to make sure the regex is valid."
                    )
                elif error.validator == "maxLength":
                    messages[server_id].append(
                        f"`{path}` is too long the max length should be {error.validator_value}."
                    )
                elif error.validator == "minLength":
                    messages[server_id].append(
                        f"`{path}` is too short the minimum length should be {error.validator_value}."
                    )
                elif error.validator == "required":
                    val = error.message.split("'")
                    messages[server_id].append(
                        f"`{val[1]}` is required but wasn't found. Please review the [documentation](https://lunarclient.dev/server-mappings/adding-servers/metadata)."
                    )
                else:  # If the error isn't defined above show the message.
                    messages[server_id].append(error.message)

            for key, value in enumn_errors.items():
                enum = value["enum"]
                incorrect = value["incorrect"]

                messages[server_id].append(
                    f'{", ".join([f"`{s}`" for s in incorrect])} is not an acceptable input for `{key}`:\n{enum}'
                )

    return messages


def check_media(
    args: argparse.Namespace, current_errors: dict[str, list[str]]
) -> dict[str, list[str]]:
    """
    This function checks the media files associated with each server.

    Parameters:
        args (argparse.Namespace): The command-line arguments passed to the script.
        current_errors (dict[str, list[str]]): The current list of validation errors.

    Returns:
        dict[str, list[str]]: A dictionary mapping server IDs to lists of validation error messages.
    """

    # Load server mappings JSON
    servers = get_all_servers(
        args.servers_dir,
        args.inactive_file,
        args.validate_inactive,
    )

    print(f"Validating {len(servers)} server media...")

    for server in servers:
        server_id = server["id"]
        server_name = server["name"]

        # Paths
        logo_path = f"{args.servers_dir}/{server_id}/logo.png"
        background_path = f"{args.servers_dir}/{server_id}/background.png"
        wordmark_path = f"{args.servers_dir}/{server_id}/wordmark.png"

        # Check if a server has a banner
        banner_path = None
        if os.path.exists(f"{args.servers_dir}/{server_id}/banner.png"):
            banner_path = f"{args.servers_dir}/{server_id}/banner.png"
        elif os.path.exists(f"{args.servers_dir}/{server_id}/banner.gif"):
            banner_path = f"{args.servers_dir}/{server_id}/banner.gif"

        # Validate!
        logo_errors = validate_logo(logo_path, server_name)
        background_errors = validate_background(background_path, server_name)
        wordmark_errors = validate_wordmark(wordmark_path, server_name)
        banner_errors = (
            validate_banner(banner_path, server_name) if banner_path is not None else []
        )


        print(f"Validated {server_name}'s media.")

        # if there are no errors for all of the above skip
        if all(
            len(errors) == 0
            for errors in [logo_errors, background_errors, banner_errors, wordmark_errors]
        ):
            continue

        if server_id not in current_errors:
            current_errors[server_id] = []

        current_errors[server_id] += background_errors
        current_errors[server_id] += logo_errors
        current_errors[server_id] += banner_errors
        current_errors[server_id] += wordmark_errors

    print(f"Sucessfully validated {len(servers)} server logos/backgrounds.")
    print(current_errors)
    return current_errors


def validate_root(directory: str = "."):
    """
    This function validates the root directory of the repository doesn't have
    any unwanted files (people will sometimes put their server in the root
    on accident!)

    Args:
        directory (str): The directory to validate. Defaults to ".".
    """
    for file in os.listdir(directory):
        if file not in FILE_WHITELIST:
            post_comment(
                {
                    "Overall": [
                        f"The file '{file}' is in the main directory but not in file whitelist"
                    ]
                }
            )
            print(
                f"The file '{file}' is in the main directory but not in file whitelist"
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
