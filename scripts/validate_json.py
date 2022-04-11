import argparse
import json
import jsonschema

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers', required=True, type=str)
    parser.add_argument('--servers_schema', required=True, type=str)
    args = parser.parse_args()

    # Load server mappings JSON
    servers = {}
    with open(args.servers) as servers_file:
        servers = json.load(servers_file)

    # Load server mappings Schema
    servers_schema = {}
    with open(args.servers_schema) as servers_file:
        servers = json.load(servers_file)

    print(f'Validating servers JSON.')

    try:
        jsonschema.validate(instance=servers, schema=servers_schema)
    except jsonschema.ValidationError:
        raise ValueError('Servers JSON does not match the schema.')

    print(f'Successfully validated servers JSON.')


if __name__ == '__main__':
    main()