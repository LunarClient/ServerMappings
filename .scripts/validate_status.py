"""
This module validates the status of Minecraft servers within ServerMappings. It pings each
server and prints whether the ping was successful.
"""

import argparse

from mcstatus import JavaServer
from utils import get_all_servers


def main():
    """
    Main function to parse arguments and ping servers.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--servers_dir", required=True, type=str)
    parser.add_argument("--inactive_file", required=True, type=str)
    parser.add_argument("--discord_logo_uploaded_file", required=True, type=str)
    args = parser.parse_args()

    # Load server mappings JSON
    servers = get_all_servers(args.servers_dir, args.inactive_file, args.discord_logo_uploaded_file, False)

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
        except Exception:
            print("\u274C", f"Failed to ping {server['name']} at {address}")


if __name__ == "__main__":
    main()
