import json
import argparse
import webptools
import shutil
import os

from PIL import Image


def main():
    # Webp Fix.
    webptools.grant_permission()

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, type=str)
    parser.add_argument('--source', required=True, type=str)
    parser.add_argument('--destination', required=True, type=str)
    parser.add_argument('--resize', default='512', type=int)
    parser.add_argument('--lossless', default=False, action='store_true')
    args = parser.parse_args()

    # Load server mappings index.
    servers_file = open(args.input)
    servers = json.load(servers_file)
    servers_file.close()

    # Create logos ouput folder.
    os.makedirs(args.destination, exist_ok=True)

    # Loop through each server in index.
    for server in servers:
        try:
            server_id = server['id']
            server_name = server['name']
            logo_source = '%s/%s.png' % (args.source, server_id)
            logo_destination = '%s/%s.webp' % (args.destination, server_id)

            # Check if server in index has an accompanying logo.
            if not os.path.isfile(logo_source):
                raise ValueError(
                    '%s does not have a server logo... Please ensure the file name matches the server ID and is a PNG.' %
                        server_name
                )

            # Load image and check dimensions.
            server_logo = Image.open(logo_source)
            if server_logo.width != server_logo.height:
                raise ValueError(
                    '%s\'s server logo does not have a 1:1 aspect ratio... Please ensure the image meets the requirements before proceeding.' %
                        server_name
                )
            if server_logo.width < 512:
                raise ValueError(
                        '%s\'s server logo width/height is less than 512px... Please ensure the image meets the requirements before proceeding.' %
                            server_name
                    )
                
            # Convert to Webp.
            output = webptools.cwebp(
                input_image=(logo_source),
                output_image=(logo_destination),
                option=('-lossless ' if args.lossless else '') + f'-resize {args.resize} {args.resize} -metadata none'
            )
            if output['exit_code']:
                raise OSError(f'Failed to run cwebp on {logo_source}: {output}')

            print('Successfully converted %s\'s logo.' % server_name)
        except Exception:
            print('Couldn\'t process %s\'s logo... Skipping.' % server_name)

    print('Done!')
        

if __name__ == '__main__':
    main()