import os
import argparse
import json
import webptools

# Grant permissions to Webptools
webptools.grant_permission()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--servers', required=True, type=str)
    parser.add_argument('--servers_logos_source', required=True, type=str)
    parser.add_argument('--servers_logos_output', required=True, type=str)
    parser.add_argument('--sizes', nargs='+', type=int, default=[256])
    parser.add_argument('--lossless', default=False, action='store_true')
    args = parser.parse_args()

    # Load server mappings JSON
    servers = {}
    with open(args.servers) as servers_file:
        servers = json.load(servers_file)

    print(f'Converting {len(servers)} server logos.')
    
    # Create server logos output directory
    os.makedirs(args.servers_logos_output, exist_ok=True)

    for server in servers:
        server_id = server['id']
        server_name = server['name']

        logo_path = f'{args.servers_logos_source}/{server_id}.png'

        # Base 512 Size
        convert_and_resize(
            logo_path,
            f'{args.servers_logos_output}/{server_id}.webp',
            lossless=args.lossless
        )

        # Size-based destination name
        for size in args.sizes:
            convert_and_resize(
                logo_path,
                f'{args.servers_logos_output}/{server_id}-{size}.webp',
                lossless=args.lossless,
                size=size,
            )

        print(f'Successfully converted {server_name}\'s logo.')

    print(f'Sucessfully converted {len(servers)} server logos.')

# Utility to convert and resize images
def convert_and_resize(source, destination, lossless=False, size=512):
    options = [
        f'-metadata none',
        f'-resize {size} {size}'
    ]

    if lossless:
        options.append('-lossless')

    output = webptools.cwebp(
        input_image=source,
        output_image=destination,
        option=' '.join(options)
    )

    print(output)

    if output.get('exit_code'):
        raise OSError(f'Failed to run Webptools ({source})')


if __name__ == '__main__':
    main()