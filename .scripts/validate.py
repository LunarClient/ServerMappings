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
from langdetect import DetectorFactory, LangDetectException, detect_langs
from tld.utils import get_tld
from collections import defaultdict
from utils import get_all_servers, get_edited_servers, validate_background, validate_banner, validate_logo, validate_wordmark, get_all_versions

# Make language detection deterministic across runs.
DetectorFactory.seed = 0

RESULTS_FILE = "pr_results.json"

# langdetect is unreliable on short strings - it regularly misreads plain English
# sentences under ~40 characters as Danish, German, etc. at >99% confidence. Below
# this length it's noise more often than not, so skip detection entirely. This is
# always a warning, never a blocking error, since even above this length it still
# occasionally misreads English text.
DESCRIPTION_LANGUAGE_MIN_LENGTH = 40
DESCRIPTION_LANGUAGE_CONFIDENCE_THRESHOLD = 0.85

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

HOSTING_DOMAIN_BLACKLIST = [
    # https://apexminecrafthosting.com/
    "mc.gg",
    "apexmc.co",
    # https://lilypad.gg/
    "smp.fan",
    "modpack.lol",
    "minecraft.vodka",
    "minecraft.horse"
]



def description_needs_check(args, server_id, description):
    """Compare values, so formatting or unrelated metadata edits do not warn."""
    if getattr(args, "skip_language_warnings", False):
        return False
    base = getattr(args, "base_servers_dir", None)
    if not base:
        return True  # Explicit local/full audit, not PR feedback.
    path = os.path.join(base, server_id, "metadata.json")
    try:
        with open(path, encoding="utf-8") as source:
            previous = json.load(source)
        return previous.get("description") != description
    except FileNotFoundError:
        return True  # Newly added server/description.
    except (OSError, ValueError, AttributeError) as exc:
        print(f"Language warning skipped for {server_id}: cannot compare base metadata: {exc}")
        return False


def main(argv=None):
    """Validate local inputs, optionally previewing the complete feedback flow."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and preview feedback without network calls or artifact writes.")
    parser.add_argument("--base-servers-dir", help="Base checkout servers directory; only changed descriptions produce language warnings.")
    parser.add_argument("--root", help="Repository to validate (defaults to this checkout locally).")
    for name in ("servers_dir", "metadata_schema", "inactive_file", "inactive_schema"):
        parser.add_argument("--" + name)
    parser.add_argument("--validate_inactive", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--edited-server", action="append", default=[],
                        help="Locally supplied edited server ID; repeat as needed (dry run only).")
    parser.add_argument("--pr-number", type=int, default=1,
                        help="Simulated feedback PR number (dry run only, default: 1).")
    arguments = parser.parse_args(argv)
    if not arguments.dry_run:
        arguments.base_servers_dir = arguments.base_servers_dir or os.getenv("BASE_SERVERS_DIR")
    if arguments.base_servers_dir and not os.path.isdir(arguments.base_servers_dir):
        parser.error("--base-servers-dir must be an existing servers directory")
    arguments.skip_language_warnings = bool(not arguments.dry_run and os.getenv("PR_ID") and not arguments.base_servers_dir)
    if arguments.skip_language_warnings:
        print("Language warnings skipped: PR base servers directory was not supplied.")
    use_args = os.getenv("USE_ARGS") == "true" and not arguments.dry_run
    if use_args:
        missing = [name for name in ("servers_dir", "metadata_schema", "inactive_file", "inactive_schema")
                   if getattr(arguments, name) is None]
        if missing:
            parser.error("USE_ARGS=true requires: " + ", ".join(missing))
    if arguments.edited_server and not arguments.dry_run:
        parser.error("--edited-server requires --dry-run")
    if arguments.pr_number <= 0:
        parser.error("--pr-number must be positive")
    local = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    root = os.path.abspath(arguments.root or (os.getcwd() if use_args else local))
    for name, filename in (("servers_dir", "servers"), ("metadata_schema", "metadata.schema.json"),
                           ("inactive_file", "inactive.json"), ("inactive_schema", "inactive.schema.json")):
        setattr(arguments, name, os.path.abspath(getattr(arguments, name) or os.path.join(root, filename)))
    if arguments.dry_run:
        print("[dry-run] No network calls or artifact writes. Feedback PR association is simulated.")
        print("[dry-run] Edited servers supplied locally: " + (", ".join(arguments.edited_server) or "none"))
    all_errors = validate_root(root)
    all_warnings = {}
    if not all_errors:
        metadata_errors, all_warnings = check_metadata(arguments)
        all_errors = check_media(arguments, metadata_errors)
    failed = any(all_errors.values())
    write_results(arguments.pr_number if arguments.dry_run else os.getenv("PR_ID"),
                  "failed" if failed else "ready", all_errors if failed else {}, all_warnings,
                  dry_run=arguments.dry_run)
    print(all_errors if failed else "No errors occurred. PR is ready for manual review.")
    if any(all_warnings.values()):
        print(all_warnings)
    return 1 if failed else 0


def write_results(
    pull_id,
    status: str,
    messages: dict[str, list[str]],
    warnings: dict[str, list[str]] | None = None,
    *, dry_run=False,
):
    """
    Persist validation results to a JSON artifact for the post-validation feedback
    workflow to consume. The validation job runs untrusted PR code without secrets,
    so it cannot post to the GitHub API directly — a separate workflow_run-triggered
    job in the trusted base repo context reads this file and posts the comment/label.

    `warnings` are non-blocking: they never affect `status` and never prevent the
    "Ready for review" label, but are still surfaced to the submitter as a comment.
    """
    if not pull_id:
        return

    try:
        pr_id = int(pull_id)
    except (TypeError, ValueError):
        return

    payload = {
        "pr_id": pr_id,
        "status": status,
        "errors": messages,
        "warnings": warnings or {},
    }
    if dry_run:
        from post_pr_feedback import apply_feedback
        print("[dry-run] Validation artifact (not written):")
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        apply_feedback(payload, {pr_id}, "LunarClient/ServerMappings", dry_run=True)
        return
    with open(RESULTS_FILE, "w", encoding="UTF-8") as results_file:
        json.dump(payload, results_file)


def check_metadata(args: argparse.Namespace) -> tuple[defaultdict[str, list[str]], defaultdict[str, list[str]]]:
    """
    This function checks all of the json files and validates them with their appropriate schemas.

    Parameters:
        args (argparse.Namespace): The command-line arguments passed to the script.

    Returns:
        tuple[dict[str, list[str]], dict[str, list[str]]]: A dictionary mapping server IDs to lists
        of blocking validation error messages, and a dictionary mapping server IDs to lists of
        non-blocking warning messages.
    """
    messages = defaultdict(list)
    warnings = defaultdict(list)

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

    # Check if any servers being edited are inactive
    for server_id in get_edited_servers(dry_run=getattr(args, "dry_run", False),
                                        edited_servers=getattr(args, "edited_server", ())):
        if server_id in inactive_file:
            messages[server_id] = [f"{server_id} is being edited but is in the inactive file!"]

    # Looping over each server folder
    seen_domains = defaultdict(set)
    for root, _, _ in os.walk(args.servers_dir):
        server_id = os.path.basename(root)
        if (
            not server_id
            or os.path.abspath(root) == os.path.abspath(args.servers_dir)
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
                        messages[server_id].append(f"The ID field in the metadata.json does not match the folder name of {server_id} (got {server['id']})")

                    primary_domain = get_tld(server.get("primaryAddress", ""), as_object=True, fail_silently=True, fix_protocol=True)
                    if primary_domain is not None and primary_domain.fld not in server["addresses"]:
                        messages[server_id].append(f"The primary address' domain ({primary_domain.fld}) is not in the addresses list. Or the primary address is not a valid domain.")
                    elif primary_domain is None:
                        messages[server_id].append(f"The primary address `{server.get('primaryAddress', '')}` is not a valid domain. Please review the [documentation](https://lunarclient.dev/server-mappings/adding-servers/metadata).")


                    all_versions = get_all_versions(server["minecraftVersions"])
                    if server["primaryMinecraftVersion"] not in all_versions:
                        ver = server["primaryMinecraftVersion"].split(".")
                        wildcard = f"{ver[0]}.*" if len(ver) == 2 else f"{ver[0]}.{ver[1]}.*"
                        messages[server_id].append(f"The primary minecraft version (`{server['primaryMinecraftVersion']}` or `{wildcard}`) is not in the minecraftVersions list.")

                    
                    for address in server["addresses"]:
                        if address == "apollo.lunarclient.com": # Skip this check for the Apollo server 
                            continue

                        domain = get_tld(address, as_object=True, fail_silently=True, fix_protocol=True)

                        if domain is not None and domain.fld in HOSTING_DOMAIN_BLACKLIST:
                            messages[server_id].append(f"The domain {domain.fld} belongs to a hosting provider. You must use a custom domain that you fully own (e.g. myserver.com instead of myserver.hosting.com). Please review the [documentation](https://lunarclient.dev/server-mappings/adding-servers/metadata#addresses).")
                        
                        if domain is not None and domain.subdomain:
                            messages[server_id].append(f"{address} does not follow the [documentation](https://lunarclient.dev/server-mappings/adding-servers/metadata). Please make sure the address is a valid domain, and does not have a subdomain.")
                        
                        if domain is not None and domain.fld in seen_domains:
                            messages[server_id].append(f"The domain {domain.fld} is also present in {', '.join(map(lambda s: f"`{s}`", seen_domains[domain.fld]))}. Please ensure each server has a unique domain(s).")
                        elif domain is not None:
                            seen_domains[domain.fld].add(server_id)
                        else:
                            messages[server_id].append(f"`{address}` is not a valid domain. Please review the [documentation](https://lunarclient.dev/server-mappings/adding-servers/metadata).")
                    
                    if primary_region := server.get("primaryRegion"):
                        if not (regions := server.get("regions")) or primary_region not in regions:
                            messages[server_id].append(f"The primary region ({primary_region}) does not exist in the regions key (or the regions key does not exist).")

                    if primary_lang := server.get("primaryLanguage"):
                        if not (languages := server.get("languages")) or primary_lang not in languages:
                            messages[server_id].append(f"The primary language ({primary_lang}) does not exist in the languages key (or the languages key does not exist).")

                    if (description := server.get("description")) and len(description) >= DESCRIPTION_LANGUAGE_MIN_LENGTH and description_needs_check(args, server_id, description):
                        try:
                            top_language = detect_langs(description)[0]
                            if top_language.lang != "en" and top_language.prob >= DESCRIPTION_LANGUAGE_CONFIDENCE_THRESHOLD:
                                warnings[server_id].append(
                                    f'The `description` ("{description}") looks like it might not be English '
                                    f"(detected: `{top_language.lang}`, {top_language.prob:.0%} confidence). "
                                    "Descriptions must be written in English — the Lunar Client translation team handles "
                                    "translating it to other languages separately. Please double check and update it if needed, "
                                    "or ignore this if it's a false positive (e.g. a brand name confusing the detector)."
                                )
                        except LangDetectException:
                            pass  # Too ambiguous to confidently detect a language; not worth surfacing.

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

    return messages, warnings


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
    try:
        servers = get_all_servers(
            args.servers_dir,
            args.inactive_file,
            args.validate_inactive,
        )
    except (OSError, ValueError) as exc:
        current_errors.setdefault("Overall", []).append(f"Unable to load media inputs: {exc}")
        return current_errors

    print(f"Validating {len(servers)} server media...")

    for server in servers:
        server_id = server["id"]
        server_name = server.get("name", server_id)

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
        def check_image(validator, path):
            if path is None:
                return []
            try:
                return validator(path, server_name)
            except (OSError, ValueError) as exc:
                return [f"Unable to validate {os.path.basename(path)} for {server_name}: {exc}"]

        logo_errors = check_image(validate_logo, logo_path)
        background_errors = check_image(validate_background, background_path)
        wordmark_errors = check_image(validate_wordmark, wordmark_path)
        banner_errors = check_image(validate_banner, banner_path)


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
    This function validates the root/servers directory of the repository doesn't
    have any unwanted files (people will sometimes put their server in the root
    on accident!)

    Args:
        directory (str): The directory to validate. Defaults to ".".
    """
    server_dir = os.path.join(directory, "servers")
    if not os.path.isdir(directory) or not os.path.isdir(server_dir):
        return {"Overall": [f"Expected a repository with a servers directory at {directory}"]}
    for file in os.listdir(directory):
        if file not in FILE_WHITELIST:
            return {"Overall": [f"The file '{file}' is in the main directory but not in file whitelist"]}
    for file in os.listdir(server_dir):
        if os.path.isfile(os.path.join(server_dir, file)):
            return {"Overall": [f"The file '{file}' is not a directory in the /servers/ folder. "
                                "Please make sure you're following the "
                                "[relevant documentation](https://lunarclient.dev/server-mappings/adding-servers/overview)."]}
    return {}


if __name__ == "__main__":
    sys.exit(main())
