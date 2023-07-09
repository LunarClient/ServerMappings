import argparse
import json
import os
from mcstatus import JavaServer
import time

from utils import get_all_servers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=True, type=str)
    parser.add_argument("--inactive_file", required=True, type=str)
    args = parser.parse_args()

    # Load server mappings JSON
    servers = get_all_servers(args.servers_dir, args.inactive_file, False)

    for server in servers:
        # Attempt to ping
        try:
            address = (
                server["primaryAddress"]
                if "primaryAddress" in server
                else server["addresses"][0]
            )
            java_server = JavaServer.lookup(address)
            java_server.status()
            print("\u2705", f"Succesfully pinged {server['name']} at {address}")
        except:
            print("\u274C", f"Failed to ping {server['name']} at {address}")


if __name__ == "__main__":
    main()
