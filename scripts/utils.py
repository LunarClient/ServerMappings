import os
import json


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

        # Enrich server data
        server["inactive"] = server["id"] in inactive
        server["enriched"] = is_enriched(server, server_id, servers_dir)
        # TODO: Add if they are a partnered server

        # Add to list
        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers


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
