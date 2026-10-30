"""
This module creates a JSON index file from server data.
It takes in a directory of server files, an inactive file, and output file paths as arguments.
"""

import argparse
import os
import json

from utils import get_all_servers, collect_translations


def main():
    """
    Main function to parse arguments and write server data to index files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=True, type=str)
    parser.add_argument("--inactive_file", required=True, type=str)
    parser.add_argument("--json_output", required=True, type=str)
    parser.add_argument("--translations_output", required=True, type=str)
    parser.add_argument("--translations_folder", required=False, type=str)
    parser.add_argument("--include_inactive", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    # Collect all translation files
    translations = {}
    if args.translations_folder:
        # Scan that folder for all translation files
        for file in os.listdir(args.translations_folder):
            if file.endswith(".json") and file != "en_US.json":
                with open(os.path.join(args.translations_folder, file), "r", encoding="utf-8") as f:
                    translations[file[:-5]] = json.load(f)

    # Collect all servers
    servers = get_all_servers(
        args.servers_dir,
        args.inactive_file,
        args.include_inactive,
        translations,
    )

    # Create a new object for translations output
    translations = collect_translations(servers)

    # Write the new JSON object to a file
    try:
        json_object = json.dumps(translations, indent=4)
        with open(args.translations_output, "w", encoding="utf-8") as outfile:
            outfile.write(json_object)
    except Exception as e:
        print("Error writing to Translations: ", e)
        raise

    # Write to JSON file
    try:
        json_object = json.dumps(servers, indent=4)
        with open(args.json_output, "w", encoding="utf-8") as outfile:
            outfile.write(json_object)
    except Exception as e:
        print("Error writing to JSON Index: ", e)
        raise

    print("Successfully written index files!")


if __name__ == "__main__":
    main()
