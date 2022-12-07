import argparse
import json
import os
import shutil

from utils import get_all_servers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers_dir', required=True, type=str)
    parser.add_argument('--index_output', required=True, type=str)
    args = parser.parse_args()

    # Collect all servers
    servers = get_all_servers(args.servers_dir, False)

    # Write to index file
    json_object = json.dumps(servers, indent=4)
    with open(args.index_output, "w") as outfile:
        outfile.write(json_object)

    print("Successfully written index file!")
    

if __name__ == '__main__':
    main()