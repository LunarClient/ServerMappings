import argparse
import json
import os
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers_dir', required=True, type=str)
    parser.add_argument('--index_output', required=True, type=str)
    args = parser.parse_args()

    servers = []

    # Looping over each server folder
    for root, _dirs, _files in os.walk(args.servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id:
            continue

        # Open metadata.json
        with open(f"{args.servers_dir}{server_id}/metadata.json") as server_file:
            server = json.load(server_file)

        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    # Write to index file
    json_object = json.dumps(servers, indent=4)
    with open(args.index_output, "w") as outfile:
        outfile.write(json_object)

    print("Successfully written index file!")
    

if __name__ == '__main__':
    main()