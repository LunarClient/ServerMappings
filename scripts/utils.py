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

        # Images
        logo_path = f'{servers_dir}/{server_id}/logo.png'
        background_path = f'{servers_dir}/{server_id}/background.png'

        # Enrich server data
        server["inactive"] = server["id"] in inactive
        server["enriched"] = os.path.isfile(logo_path) and os.path.isfile(background_path)

        # Add to list
        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers