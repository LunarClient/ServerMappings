import os
import json

MAJOR_ALL = {
    "1.7.*": ["1.7.10", "1.7"],
    "1.8.*": ["1.8.9", "1.8"],
    "1.12.*": ["1.12.2", "1.12"],
    "1.16.*": ["1.16.5", "1.16"],
    "1.17.*": ["1.17.1", "1.17"],
    "1.18.*": ["1.18.1", "1.18.2", "1.18"],
    "1.19.*": ["1.19", "1.19.2"]
}


def get_all_servers(servers_dir):
    servers = []

    # Open inactive.json
    inactive = []
    with open(f"inactive.json") as inactive_file:
        inactive = json.load(inactive_file)

    # Looping over each server folder
    for root, _dirs, _files in os.walk(servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id or server_id == servers_dir:
            continue

        # Open metadata.json
        with open(f"{servers_dir}/{server_id}/metadata.json") as server_file:
            server = json.load(server_file)

        # Modify versions
        if "minecraftVersions" in server:
            server["minecraftVersions"] = get_all_versions(server["minecraftVersions"])

        # Enrich server data
        server["inactive"] = server["id"] in inactive
        server["enriched"] = is_enriched(server, server_id, servers_dir)
        # TODO: Add if they are a partnered server

        # Add to list
        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers


def get_all_versions(versions):
    to_return = []

    for version in versions:
        if version in MAJOR_ALL:
            to_return.extend(MAJOR_ALL[version])
        else:
            to_return.append(version)

    return to_return


def is_enriched(server, server_id, servers_dir):
    # Check Images
    logo_path = f"{servers_dir}/{server_id}/logo.png"
    background_path = f"{servers_dir}/{server_id}/background.png"

    if not os.path.isfile(logo_path) or not os.path.isfile(background_path):
        return False

    # Check Primary IP
    if not "primaryAddress" in server:
        return False

    # TODO: add more enriched labels later
    return True
