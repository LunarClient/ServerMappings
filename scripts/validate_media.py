import os
import argparse
import json
from PIL import Image as image

from utils import get_all_servers

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers_dir', required=True, type=str)
    args = parser.parse_args()

    # Load server mappings JSON
    servers = get_all_servers(args.servers_dir)

    print(f'Validating {len(servers)} server media...')
    background_amount = 0
    banner_amount = 0

    for server in servers:
        server_id = server['id']
        server_name = server['name']

        # Paths
        logo_path = f'{args.servers_dir}/{server_id}/logo.png'
        background_path = f'{args.servers_dir}/{server_id}/background.png'
        banner_path = f'{args.servers_dir}/{server_id}/banner.png'

        validate_logo(logo_path, server_name)
        if validate_background(background_path, server_name):
            background_amount += 1

        if validate_banner(banner_path, server_name):
            banner_amount += 1

        print(f'Successfully validated {server_name}\'s media.')

    print(f'Sucessfully validated {len(servers)} server logos.')
    print(f'Sucessfully validated {background_amount} server backgrounds - ({len(servers) - background_amount} servers did not provide a background).')
    print(f'Sucessfully validated {banner_amount} server banners - ({len(servers) - banner_amount} servers did not provide a banner).')


'''
Validate that server logo meets the following requirements:
  * exists in logos folder
  * is a PNG
  * has a 1:1 aspect ratio
  * is greater than 512 pixels in width / height
'''
def validate_logo(path, server_name):
    # Check image exists
    if not os.path.isfile(path):
        raise ValueError(f'{server_name}\'s server logo does not exist... Please ensure the file name matches the server ID and is a PNG.')

    logo_image = image.open(path)

    # Check image format is a PNG
    if logo_image.format not in ['PNG']:
        raise ValueError(f'{server_name}\'s server logo is not a PNG (currently {logo_image.format})... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are a 1:1 ratio
    if logo_image.width != logo_image.height:
        raise ValueError(f'{server_name}\'s server logo does not have a 1:1 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are at least 512px
    if logo_image.width < 512:
        raise ValueError(f'{server_name}\'s server logo width/height is less than 512px... Please ensure the image meets the requirements before proceeding.')


'''
Validate that server background meets the following requirements:
Note: Servers are recommended to have a background, but not required...
  * is a PNG
  * has a 16:9 aspect ratio
  * is greater than 1920 pixels in width and 1080 pixels in height
'''
def validate_background(path, server_name):
    # Check image exits - silently skip if not (as it is not yet a requirement)
    if not os.path.isfile(path):
        print(f'No background found for {server_name}... skipping.')
        return False

    background_image = image.open(path)

    # Check image format is a PNG
    if background_image.format not in ['PNG']:
        raise ValueError(f'{server_name}\'s server background is not a PNG (currently {background_image.format})... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are a 16:9 ratio
    rounded_ratio = round(background_image.width / background_image.height, 2)
    if rounded_ratio != 1.78:
        raise ValueError(f'{server_name}\'s server background does not have a 16:9 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are at least 512px
    if background_image.width < 1920:
        raise ValueError(f'{server_name}\'s server background resolution is less than 1920x1080... Please ensure the image meets the requirements before proceeding.')
    
    return True

def validate_banner(path, server_name):
    if not os.path.isfile(path):
        print(f'No banner found for {server_name}... skipping.')
        return False

    banner_image = image.open(path)

    if banner_image.format not in {'PNG', 'GIF'}:
        raise ValueError(f'{server_name}\'s server banner is not a PNG or GIF (currently {banner_image.format})... Please ensure the image meets the requirements before proceeding.')

    aspect_ratio = round(banner_image.width / banner_image.height, 3)

    if aspect_ratio != 7.556:
        raise ValueError(f'{server_name}\'s server banner does not have a 68:9 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    if banner_image.width < 340:
        raise ValueError(f'{server_name}\'s server banner is less than 340x45... Please ensure the image meets the requirements before proceeding.')

    return True

if __name__ == '__main__':
    main()
