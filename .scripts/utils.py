"""
This is a utility module that provides various functions for handling server data,
validating images, and converting gif images to sprite sheets.
"""

import json
import requests
import os

from PIL import Image as image

# Mapping of major versions to currently available subversions
MAJOR_ALL: dict[str, list[str]] = {
    "1.7.*": ["1.7.10", "1.7"],
    "1.8.*": ["1.8.9", "1.8"],
    "1.12.*": ["1.12.2", "1.12"],
    "1.16.*": ["1.16.5", "1.16"],
    "1.17.*": ["1.17.1", "1.17"],
    "1.18.*": ["1.18.1", "1.18.2", "1.18"],
    "1.19.*": ["1.19", "1.19.2", "1.19.3", "1.19.4"],
    "1.20.*": ["1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4"],
}


def get_all_servers(
    servers_dir: str, inactive_file: str, include_inactive: bool = True
) -> list:
    """
    This function retrieves all ServerMappings servers within the servers folder

    Args:
        servers_dir (str): The directory where the servers are located.
        inactive_file (str): The file containing the inactive servers.
        include_inactive (bool, optional): Whether to include inactive servers. Defaults to True.

    Returns:
        list: A list of all servers.
    """
    servers: list = []

    # Open inactive.json
    inactive = []
    with open(inactive_file, encoding="utf-8") as inactive_f:
        inactive = json.load(inactive_f)

    # Looping over each server folder
    for root, _, _ in os.walk(servers_dir):
        server_id = root.split(os.path.sep)[-1]
        if not server_id or server_id == servers_dir:
            continue

        # Open metadata.json
        try:
            with open(
                f"{servers_dir}/{server_id}/metadata.json", encoding="utf-8"
            ) as server_file:
                server = json.load(server_file)
        except Exception:
            continue  # Already added to errors in validate.py

        # Modify versions
        if "minecraftVersions" in server:
            server["minecraftVersions"] = get_all_versions(server["minecraftVersions"])

        # Enrich server data
        if "id" not in server:
            print(f"Skipping {server_id} as it's missing 'id'")
            continue
        server["inactive"] = server["id"] in inactive
        server["enriched"] = is_enriched(server, server_id, servers_dir)
        
        # Discard inactive servers if not including inactive (by default we do)
        if not include_inactive and server["inactive"]:
            continue

        # Generate image URLS
        server["images"] = {}
        if os.path.isfile(f"{servers_dir}/{server_id}/logo.png"):
            server["images"]["logo"] = f"https://servermappings.lunarclientcdn.com/logos/{server_id}.png"
        if os.path.isfile(f"{servers_dir}/{server_id}/background.png"):
            server["images"]["background"] = f"https://servermappings.lunarclientcdn.com/backgrounds/{server_id}.png"
        if os.path.isfile(f"{servers_dir}/{server_id}/banner.png"):
            server["images"]["banner"] = f"https://servermappings.lunarclientcdn.com/banners/{server_id}.png"
        if os.path.isfile(f"{servers_dir}/{server_id}/wordmark.png"):
            server["images"]["wordmark"] = f"https://servermappings.lunarclientcdn.com/wordmarks/{server_id}.png"

        # Add to list
        servers.append(server)

    # Sort A-Z
    servers.sort(key=lambda x: x["id"])

    return servers


def get_all_versions(versions) -> list[str]:
    """
    This function takes a list of versions that could be either subversions or
    major versions, and if it is a major version (denoted by the astrix), it
    will include all of the subversions from that major version.

    Parameters:
        versions (list): The list of versions.

    Returns:
        list: The list of all versions.
    """
    to_return: list[str] = []

    for version in versions:
        if version in MAJOR_ALL:
            to_return.extend(MAJOR_ALL[version])
        else:
            to_return.append(version)

    return to_return


def is_enriched(server: dict, server_id: str, servers_dir: str) -> bool:
    """
    This function checks though different criteria to determine whether a
    server is "enriched". A server within ServerMappings being deemed "enriched"
    allows the listing to show up in more visible placements within Lunar Client.

    Parameters:
        server (dict): The server data.
        server_id (str): The server id.
        servers_dir (str): The directory where the server data is stored.

    Returns:
        bool: Whether the server is deemed "enriched".
    """

    # Check Images
    logo_path = f"{servers_dir}/{server_id}/logo.png"
    background_path = f"{servers_dir}/{server_id}/background.png"

    # Check if valid files / paths
    if not os.path.isfile(logo_path) or not os.path.isfile(background_path):
        return False

    # Check Primary IP
    if not "primaryAddress" in server:
        return False

    return True


def get_edited_servers():
    """
    This gets all the edited servers in this pull request

    Returns:
        set[str]: A set of server IDs that have been edited in this pull request.
    """
    pull_id = os.getenv("PR_ID")
    edited_server_ids = set() # 4 files in a server can be edited

    if not pull_id:
        print("No pull request id found. Unable to get edited servers")
        return edited_server_ids

    res = requests.get(
            f"https://api.github.com/repos/LunarClient/ServerMappings/pulls/{pull_id}/files",
            headers={
                "accept": "application/vnd.github+json",
                "Authorization": f"Bearer {os.getenv('BOT_PAT')}",
            }
        )
    
    for file in res.json():
        file_name: str = file['filename']
        if not file_name.startswith("servers/"):
            continue
        split_path = file_name.split("/")
        edited_server_ids.add(split_path[1])
    return edited_server_ids


def gif_to_sprite_sheet(path):
    """
    This function converts a gif image to a sprite sheet.

    Parameters:
        path (str): The path to the gif image.

    Returns:
        Image: A sprite sheet image.
    """
    img = image.open(path)
    sprite_img = image.new("RGBA", (img.width, img.height * img.n_frames))

    for idx in range(0, img.n_frames):
        img.seek(idx)
        sprite_img.paste(img, (0, img.height * idx))
    return sprite_img


def validate_logo(path, server_name) -> list[str]:
    """
    Validate that server logo meets the following requirements:
      * exists in logos folder
      * is a PNG
      * has a 1:1 aspect ratio
      * is greater than 512 pixels in width / height

    Parameters:
        path (str): The path to the server logo.
        server_name (str): The name of the server.

    Returns:
        list: A list of error messages if the logo does not meet the requirements. If the
              logo meets all the requirements, an empty list is returned.
    """

    # Check image exists
    if not os.path.isfile(path):
        return [
            f"{server_name}'s server logo does not exist... Please ensure the file name matches the server ID and is a PNG."
        ]

    errors = []
    logo_image = image.open(path)

    # Check image format is a PNG
    if logo_image.format not in ["PNG"]:
        errors.append(
            f"{server_name}'s server logo is not a PNG (currently {logo_image.format})..."
        )

    # Check image dimensions are a 1:1 ratio
    if logo_image.width != logo_image.height:
        errors.append(
            f"{server_name}'s server logo does not have a 1:1 aspect ratio..."
        )

    # Check image dimensions are at least 512px
    if logo_image.width < 512:
        errors.append(
            f"{server_name}'s server logo width/height is less than 512px..."
        )

    return errors


def validate_background(path, server_name) -> list[str]:
    """
    Validate that server background meets the following requirements:
      * is a PNG
      * has a 16:9 aspect ratio
      * is greater than 1920 pixels in width and 1080 pixels in height

    Parameters:
        path (str): The path to the server background.
        server_name (str): The name of the server.

    Returns:
        list: A list of error messages if the background does not meet the requirements. If the
              background meets all the requirements, an empty list is returned.
    """

    # Check image exits - silently skip if not (as it is not yet a requirement)
    if not os.path.isfile(path):
        print(f"No background found for {server_name}... skipping.")
        return []

    errors = []
    background_image = image.open(path)

    # Check image format is a PNG
    if background_image.format not in ["PNG"]:
        errors.append(
            f"{server_name}'s server background is not a PNG (currently {background_image.format})..."
        )

    # Check image dimensions are a 16:9 ratio
    aspect_ratio = round(background_image.width / background_image.height, 2)
    if aspect_ratio != 1.78:
        errors.append(
            f"{server_name}'s server background does not have a 16:9 aspect ratio..."
        )

    # Check image dimensions are at least 512px
    if background_image.width < 1920:
        errors.append(
            f"{server_name}'s server background resolution is less than 1920x1080..."
        )

    return errors


def validate_banner(path: str, server_name: str) -> list[str]:
    """
    Validate that server banner meets the following requirements:
      * is a PNG or GIF
      * has a 35:5 aspect ratio
      * is greater than 340 pixels in width and 45 pixels in height
      * we can convert it to a sprite image without it erroring.

    Parameters:
        path (str): The path to the server banner.
        server_name (str): The name of the server.

    Returns:
        list: A list of error messages if the banner does not meet the requirements. If the
              banner meets all the requirements, an empty list is returned.
    """

    if not os.path.isfile(path):
        print(f"No banner found for {server_name}... skipping.")
        return []

    banner_image = image.open(path)
    errors = []

    # Incorrect input format
    if banner_image.format not in {"PNG", "GIF"}:
        errors.append(
            f"{server_name}'s server banner is not a PNG or GIF (currently {banner_image.format})..."
        )

    # Process GIF properties
    if banner_image.format == "GIF" and banner_image.n_frames > 1:
        duration = banner_image.info["duration"]
        total_duration = duration
        # Loop through all the frames, rather than just do duration * n_frames, because GIF
        # files can have different durations for each frame.
        for idx in range(1, banner_image.n_frames):
            banner_image.seek(idx)
            total_duration += duration

        # GIF too long
        if total_duration > 15_000:
            errors.append(
                f"{server_name}'s server banner is more than 15 seconds long (currently {total_duration / 1000})..."
            )

        # No duration found
        if total_duration == 0:
            errors.append(
                f"{server_name}'s server gif server banner seems to not have any duration associated with it..."
            )

    aspect_ratio = round(banner_image.width / banner_image.height, 3)

    sprite = gif_to_sprite_sheet(path)

    # Too big
    if sprite.height > 16383 or sprite.width > 16383:
        errors.append(
            f"{server_name}'s server banner is either too tall as a sprite image, or too wide. we're unable to convert this later..."
        )

    # Incorrect aspect ratio
    if aspect_ratio != 7.8:
        errors.append(
            f"{server_name}'s server banner does not have a 16:9 aspect ratio..."
        )

    # Width too small
    if banner_image.width < 351:
        errors.append(
            f"{server_name}'s server banner is less than 351x45..."
        )

    return errors

def validate_wordmark(path: str, server_name: str) -> list[str]:
    """
    Validate that server wordmark meets the following requirements:
      * is a PNG
      * has a 16:9 aspect ratio
      * is greater than 854 pixels in width and 480 pixels in height

    Parameters:
        path (str): The path to the server wordmark.
        server_name (str): The name of the server.

    Returns:
        list: A list of error messages if the wordmark does not meet the requirements. If the
              banner meets all the requirements, an empty list is returned.
    """

    if not os.path.isfile(path):
        print(f"No wordmark found for {server_name}... skipping.")
        return []
    
    wordmark_image = image.open(path)
    errors = []

    # Check image format is a PNG
    if wordmark_image.format not in ["PNG"]:
        errors.append(
            f"{server_name}'s server wordmark is not a PNG (currently {wordmark_image.format})..."
        )
    

    # Width or height too small
    if wordmark_image.width < 854 or wordmark_image.height < 480:
        errors.append(
            f"{server_name}'s server wordmark is less than 854x480..."
        )
    

    aspect_ratio = round(wordmark_image.width / wordmark_image.height, 2)
    # Incorrect aspect ratio
    if aspect_ratio != 1.78:
        errors.append(
            f"{server_name}'s server wordmark does not have a 16:9 aspect ratio..."
        )

    
    return errors