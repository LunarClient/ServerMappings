import os
import argparse
import json
from PIL import Image as image

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers', required=True, type=str)
    parser.add_argument('--servers_logos_source', required=True, type=str)
    args = parser.parse_args()

    # Load server mappings JSON
    servers = {}
    with open(args.servers) as servers_file:
        servers = json.load(servers_file)

    print(f'Validating {len(servers)} server logos.')

    for server in servers:
        server_id = server['id']
        server_name = server['name']

        logo_path = f'{args.servers_logos_source}/{server_id}.png'
        
        # Check image exists
        if not os.path.isfile(logo_path):
            raise ValueError(f'{server_name}\'s server logo does not exist... Please ensure the file name matches the server ID and is a PNG.')

        logo_image = image.open(logo_path)

        # Check image format is a PNG
        if logo_image.format not in ['PNG']:
            raise ValueError(f'{server_name}\'s server logo is not a PNG... Please ensure the image meets the requirements before proceeding.')

        # Check image dimensions are a 1:1 ratio
        if logo_image.width != logo_image.height:
            raise ValueError(f'{server_name}\'s server logo does not have a 1:1 aspect ratio... Please ensure the image meets the requirements before proceeding.')

        # Check image dimensions are at least 512px
        if logo_image.width < 512:
            raise ValueError(f'{server_name}\'s server logo width/height is less than 512px... Please ensure the image meets the requirements before proceeding.')

        print(f'Successfully validated {server_name}\'s logo.')

    print(f'Sucessfully validated {len(servers)} server logos.')



if __name__ == '__main__':
    main()