import os
import json

from PIL import Image as image

MAJOR_ALL = {
    "1.7.*": ["1.7.10", "1.7"],
    "1.8.*": ["1.8.9", "1.8"],
    "1.12.*": ["1.12.2", "1.12"],
    "1.16.*": ["1.16.5", "1.16"],
    "1.17.*": ["1.17.1", "1.17"],
    "1.18.*": ["1.18.1", "1.18.2", "1.18"],
    "1.19.*": ["1.19", "1.19.2", "1.19.3"]
}


def get_all_servers(servers_dir, inactive_file, include_inactive=True):
    servers = []

    # Open inactive.json
    inactive = []
    with open(inactive_file) as inactive_f:
        inactive = json.load(inactive_f)

    # Looping over each server folder
    for root, _dirs, _files in os.walk(servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id or server_id == servers_dir:
            continue

        # Open metadata.json
        with open(f"{servers_dir}/{server_id}/metadata.json") as server_file:
            server = json.load(server_file)

        # Modify versions
        if "minecraftVersions" in server:
            server["minecraftVersions"] = get_all_versions(server["minecraftVersions"])

        # Enrich server data
        if "id" not in server:
            print(f"Skipping {server_id} as it's missing 'id'")
            continue
        server["inactive"] = server["id"] in inactive
        server["enriched"] = is_enriched(server, server_id, servers_dir)

        if not include_inactive and server["inactive"]:
            continue

        # Add to list
        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers


def get_all_versions(versions):
    to_return = []

    for version in versions:
        if version in MAJOR_ALL:
            to_return.extend(MAJOR_ALL[version])
        else:
            to_return.append(version)

    return to_return


def is_enriched(server, server_id, servers_dir):
    # Check Images
    logo_path = f"{servers_dir}/{server_id}/logo.png"
    background_path = f"{servers_dir}/{server_id}/background.png"

    if not os.path.isfile(logo_path) or not os.path.isfile(background_path):
        return False

    # Check Primary IP
    if not "primaryAddress" in server:
        return False

    # TODO: add more enriched labels later
    return True


'''
Validate that server logo meets the following requirements:
  * exists in logos folder
  * is a PNG
  * has a 1:1 aspect ratio
  * is greater than 512 pixels in width / height
'''
def validate_logo(path, server_name) -> list:
    # Check image exists

    if not os.path.isfile(path):
        return [
            f'{server_name}\'s server logo does not exist... Please ensure the file name matches the server ID and is a PNG.']

    errors = []
    logo_image = image.open(path)

    # Check image format is a PNG
    if logo_image.format not in ['PNG']:
        errors.append(
            f'{server_name}\'s server logo is not a PNG (currently {logo_image.format})... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are a 1:1 ratio
    if logo_image.width != logo_image.height:
        errors.append(
            f'{server_name}\'s server logo does not have a 1:1 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are at least 512px
    if logo_image.width < 512:
        errors.append(
            f'{server_name}\'s server logo width/height is less than 512px... Please ensure the image meets the requirements before proceeding.')

    return errors


'''
Validate that server background meets the following requirements:
  * is a PNG
  * has a 16:9 aspect ratio
  * is greater than 1920 pixels in width and 1080 pixels in height
'''
def validate_background(path, server_name) -> list:
    # Check image exits - silently skip if not (as it is not yet a requirement)
    if not os.path.isfile(path):
        print(f'No background found for {server_name}... skipping.')
        return []

    errors = []
    background_image = image.open(path)

    # Check image format is a PNG
    if background_image.format not in ['PNG']:
        errors.append(
            f'{server_name}\'s server background is not a PNG (currently {background_image.format})... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are a 16:9 ratio
    rounded_ratio = round(background_image.width / background_image.height, 2)
    if rounded_ratio != 1.78:
        errors.append(
            f'{server_name}\'s server background does not have a 16:9 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    # Check image dimensions are at least 512px
    if background_image.width < 1920:
        errors.append(
            f'{server_name}\'s server background resolution is less than 1920x1080... Please ensure the image meets the requirements before proceeding.')

    return errors

'''
Validate that server banner meets the following requirements:
  * is a PNG or GIF
  * has a 39:5 aspect ratio
  * is greater than 340 pixels in width and 45 pixels in height
'''
def validate_banner(path, server_name):
    if not os.path.isfile(path):
        print(f'No banner found for {server_name}... skipping.')
        return []

    banner_image = image.open(path)
    errors = []

    if banner_image.format not in {'PNG', 'GIF'}:
        errors.append(f'{server_name}\'s server banner is not a PNG or GIF (currently {banner_image.format})... Please ensure the image meets the requirements before proceeding.')

    if banner_image.format == 'GIF' and banner_image.n_frames > 1:
        duration = banner_image.info['duration']
        total_duration = duration
        # loop through all the frames, rather than just do duration * n_frames, because GIF can have different duration for each frame.
        for idx in range(1, banner_image.n_frames):
            banner_image.seek(idx)
            if banner_image.info['duration'] != duration:
                errors.append(f'{server_name}\'s server banner does not have the same duration for all frames... Please ensure the image meets the requirements before proceeding.')

            total_duration += duration

        if total_duration > 10000:
            errors.append(f'{server_name}\'s server banner is more than 3 seconds long (currently {total_duration / 1000})... Please ensure the image meets the requirements before proceeding.')

        fps = (banner_image.n_frames / (total_duration / 1000.0))

        if fps != 20.0:
            errors.append(f'{server_name}\'s server banner is not exactly 20 FPS (currently {fps})... Please ensure the image meets the requirements before proceeding.')

    aspect_ratio = round(banner_image.width / banner_image.height, 3)

    if aspect_ratio != 7.8:
        errors.append(f'{server_name}\'s server banner does not have a 39:5 aspect ratio... Please ensure the image meets the requirements before proceeding.')

    if banner_image.width < 351:
        errors.append(f'{server_name}\'s server banner is less than 351x45... Please ensure the image meets the requirements before proceeding.')

    return errors