import argparse
import json
import jsonschema
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers_dir', required=True, type=str)
    parser.add_argument('--metadata_schema', required=True, type=str)
    args = parser.parse_args()

    # Load server mappings Schema
    metadata_schema = {}
    with open(args.metadata_schema) as schema_file:
        metadata_schema = json.load(schema_file)

    # Looping over each server folder
    for root, _dirs, _files in os.walk(args.servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id or server_id == args.servers_dir:
            continue

        # Open metadata.json
        with open(f"{args.servers_dir}/{server_id}/metadata.json") as server_file:
            server = json.load(server_file)

        print(f'Validating {server_id}\'s metadata.json file...')

        # Validate!
        try:
            jsonschema.validate(instance=server, schema=metadata_schema)
        except jsonschema.ValidationError:
            raise ValueError(f'{server_id}\'s metadata.json does not match the schema.')

        print(f'Successfully validated {server_id}\'s metadata.json file!')


if __name__ == '__main__':
    main()