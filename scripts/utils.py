import os
import json

def get_all_servers(servers_dir):
    servers = []

    # Looping over each server folder
    for root, _dirs, _files in os.walk(servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id or server_id == servers_dir:
            continue

        # Open metadata.json
        with open(f"{servers_dir}/{server_id}/metadata.json") as server_file:
            server = json.load(server_file)

        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers