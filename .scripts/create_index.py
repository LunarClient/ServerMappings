"""
This module creates index files in various formats (JSON, NDJSON, CSV) from server data.
It takes in a directory of server files, an inactive file, and output file paths as arguments.
"""

import argparse
import csv
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
    parser.add_argument("--csv_output", required=True, type=str)
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

    # Write to CSV file
    try:
        with open(args.csv_output, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(
                outfile,
                fieldnames=[
                    "id",
                    "name",
                    "description",
                    "addresses",
                    "primaryAddress",
                    "minecraftVersions",
                    "primaryMinecraftVersion",
                    "primaryColor",
                    "secondaryColor",
                    "primaryLanguage",
                    "languages",
                    "primaryRegion",
                    "regions",
                    "primaryGameType",
                    "gameTypes",
                    "website",
                    "wiki",
                    "merch",
                    "store",
                    "socials",
                    "crossplay",
                    "enriched",
                    "inactive",
                    "discordLogoUploaded",
                    "compliance",
                    "presentationVideo",
                    "modpack",
                    "tebexStore",
                    "images",
                    "votingLinks",
                    "localizedDescriptions",
                ],
            )
            writer.writeheader()
            for server in servers:
                writer.writerow(server)
    except Exception as e:
        print("Error writing to CSV Index: ", e)
        raise

    print("Successfully written index files!")


if __name__ == "__main__":
    main()
