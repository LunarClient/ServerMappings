"""
This module is used to convert media files for servers. It supports conversion of logos,
backgrounds, and banners with different sizes for different placements across Lunar Client.
"""

import argparse
import json
import os
import shutil

import webptools
from PIL import Image as image
from utils import get_all_servers

# Grant permissions to Webptools
webptools.grant_permission()


def main():
    """
    Main function to parse arguments and convert server media.
    """
    use_args = os.getenv("USE_ARGS") == "true"
    parser = argparse.ArgumentParser()

    # General Args
    parser.add_argument("--servers_dir", required=use_args, type=str)
    parser.add_argument("--inactive_file", required=use_args, type=str)
    parser.add_argument("--discord_logo_uploaded_file", required=use_args, type=str)
    parser.add_argument("--lossless", default=False, action="store_true")
    parser.add_argument("--changed_files", required=False, type=str)
    parser.add_argument("--dry_upload", default="false", type=str)

    # Logo Args
    parser.add_argument("--servers_logos_output", required=use_args, type=str)
    parser.add_argument("--servers_logos_sizes", nargs="+", type=int, default=[256])

    # Background args
    parser.add_argument("--servers_backgrounds_output", required=use_args, type=str)
    parser.add_argument(
        "--servers_backgrounds_sizes", nargs="+", type=str, default=["1920x1080"]
    )

    # Banner args
    parser.add_argument("--servers_banners_output", required=use_args, type=str)

    args = parser.parse_args()
    args.dry_upload = args.dry_upload.lower() in ["true", "1", "t", "y", "yes"]

    # If we don't find the env variable for use args assume we're running this locally
    if not use_args:
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace(
            "\\", "/"
        )

        args.inactive_file = local + "/inactive.json"
        args.discord_logo_uploaded_file = local + "/discord-logo-uploaded.json"
        args.servers_dir = local + "/servers"

        args.servers_logos_output = local + "/.out/servers_logos_output"
        args.servers_backgrounds_output = local + "/.out/backgrounds"
        args.servers_banners_output = local + "/.out/banners"
        args.lossless = False

    # Load server mappings JSON
    servers = get_all_servers(
        args.servers_dir, args.inactive_file, args.discord_logo_uploaded_file, False
    )

    if args.dry_upload:
        print(f"Dry run detected. Converting {len(servers)} server media...")
    else:
        changed_files = (
            list(json.loads(args.changed_files)) if args.changed_files else []
        )
        changed_servers = list(set(file.split("/")[1] for file in changed_files))

        print(
            f"Converting {len(changed_servers)} server media from the following servers:"
        )
        print(changed_servers)

        # Filter servers array
        servers = [server for server in servers if server["id"] in changed_servers]

    background_amount = 0
    banner_amount = 0

    # Create server media output directories
    os.makedirs(args.servers_logos_output, exist_ok=True)
    os.makedirs(args.servers_backgrounds_output, exist_ok=True)
    os.makedirs(args.servers_banners_output, exist_ok=True)

    for server in servers:
        server_id = server["id"]
        server_name = server["name"]

        # Paths
        logo_path = f"{args.servers_dir}/{server_id}/logo.png"
        background_path = f"{args.servers_dir}/{server_id}/background.png"
        static_banner_path = f"{args.servers_dir}/{server_id}/banner.png"
        animated_banner_path = f"{args.servers_dir}/{server_id}/banner.gif"

        convert_logo(
            logo_path,
            args.servers_logos_output,
            server_id,
            server_name,
            args.servers_logos_sizes,
            args.lossless,
        )
        if convert_background(
            background_path,
            args.servers_backgrounds_output,
            server_id,
            server_name,
            args.servers_backgrounds_sizes,
            args.lossless,
        ):
            background_amount += 1

        # convert only the first banner that exists, because either can exist.
        for banner_path in [static_banner_path, animated_banner_path]:
            if convert_banner(
                banner_path,
                args.servers_banners_output,
                server_id,
                server_name,
                args.lossless,
            ):
                banner_amount += 1
                break

    print(f"Sucessfully converted {len(servers)} server logos.")
    print(
        f"Successfully converted {background_amount} server backgrounds - "
        f"({len(servers) - background_amount} servers did not provide a background)."
    )
    print(
        f"Successfully converted {banner_amount} server banners - "
        f"({len(servers) - banner_amount} servers did not provide a banner)."
    )


def convert_background(
    path: str,
    output: str,
    server_id: str,
    server_name: str,
    sizes: list,
    lossless: bool = False,
) -> bool:
    """
    Convert the background image to different sizes and formats.

    The original PNG file is kept for environments that do not support WEBP.

    Args:
        path (str): The path to the source image file.
        output (str): The path where the converted image will be saved.
        server_id (str): The ID of the server.
        server_name (str): The name of the server.
        sizes (list): The list of sizes to resize the image to.
        lossless (bool, optional): If set to True, the image will be converted
                                   without any loss in quality. Default is False.

    Returns:
        bool: True if the background image was successfully converted, False otherwise.
    """

    # Silently skip if not present as it is optional
    if not os.path.isfile(path):
        return False

    # Raw no transformations (PNG)
    shutil.copyfile(path, f"{output}/{server_id}.png")

    # Base 1920x1080 Size (WebP)
    convert_and_resize(
        path,
        f"{output}/{server_id}.webp",
        lossless=lossless,
    )

    # Background Size-based destination name
    for size in sizes:
        convert_and_resize(
            path,
            f"{output}/{server_id}-{size.split('x')[1]}.webp",
            lossless=lossless,
            width=size.split("x")[0],
            height=size.split("x")[1],
        )

    print(f"Successfully converted {server_name}'s background.")
    return True


def convert_banner(
    path: str, output: str, server_id: str, server_name: str, lossless: bool = False
) -> bool:
    """
    Convert the banner image to different formats.

    If the file is already a PNG, we assume it's already a spritemap or just a static banner.
    If it's a GIF, we convert it to a spritemap and save the GIF as well.

    Additionally, both formats create a metadata json file with the frame durations.

    Args:
        path (str): The path to the source image file.
        output (str): The path where the converted image will be saved.
        server_id (str): The ID of the server.
        server_name (str): The name of the server.
        lossless (bool, optional): If set to True, the image will be converted
                                   without any loss in quality. Default is False.

    Returns:
        bool: True if the banner image was successfully converted, False otherwise.
    """

    # Silently skip if not present as it is optional
    if not os.path.isfile(path):
        return False

    img = image.open(path)

    if img.format == "PNG":
        # Raw no transformations (PNG)
        shutil.copyfile(path, f"{output}/{server_id}.png")

        # Base full Size (WebP)
        convert_and_resize(
            path,
            f"{output}/{server_id}.webp",
            lossless=lossless,
        )
    elif img.format == "GIF":
        # Raw no transformation (GIF)
        shutil.copyfile(path, f"{output}/{server_id}.gif")

        # Convert to sprite sheet (WEBP)
        gif_to_sprite_sheet(path, output, server_id, lossless)

    # Create metadata for banner
    make_banner_metadata(path, output, server_id)

    print(f"Successfully converted {server_name}'s banner.")
    return True


def make_banner_metadata(path: str, output: str, server_id: str):
    """
    This function creates a metadata JSON file for the banner image.

    The metadata includes the duration of each frame in the image. This is particularly
    useful for animated GIFs that are converted to sprite sheets. Not particularly useful
    for static banners where there is only one frame.

    Args:
        path (str): The path to the source image file.
        output (str): The path where the metadata JSON file will be saved.
        server_id (str): The ID of the server.
    """
    img = image.open(path)
    frame_durations = []

    # Get frame durations from frame info
    if img.n_frames > 1:
        for idx in range(0, img.n_frames):
            img.seek(idx)
            frame_durations.append(img.info["duration"])

    # Write to json file
    with open(f"{output}/{server_id}.json", "w", encoding="UTF-8") as fp:
        json.dump({"frame_durations": frame_durations}, fp)


def gif_to_sprite_sheet(path: str, output: str, server_id: str, lossless: bool = False):
    """
    This function converts a GIF image into a sprite sheet.

    The sprite sheet is saved in the original PNG format and then converted to WEBP.
    Each frame of the GIF is pasted into the sprite sheet.

    Args:
        path (str): The path to the source GIF file.
        output (str): The path where the sprite sheet will be saved.
        server_id (str): The ID of the server.
        lossless (bool, optional): If set to True, the sprite sheet will be converted without
                                   any loss in quality. Default is False.
    """

    img = image.open(path)
    sprite_img = image.new("RGBA", (img.width, img.height * img.n_frames))

    # Convert every frame and paste it into the sprite sheet
    for idx in range(0, img.n_frames):
        img.seek(idx)
        sprite_img.paste(img, (0, img.height * idx))

    # Save the sprite sheet in our original format (PNG)
    sprite_img.save(f"{output}/{server_id}.png")

    # Convert the sprite sheet to WEBP
    convert_and_resize(
        f"{output}/{server_id}.png", f"{output}/{server_id}.webp", lossless=lossless
    )


def convert_logo(
    path: str,
    output: str,
    server_id: str,
    server_name: str,
    sizes: list,
    lossless: bool = False,
):
    """
    This function converts the server logo into different sizes and formats.

    The logo is kept in the original PNG format for environments that do not support WEBP.
    It is also resized into different sizes as specified in the 'sizes' parameter.

    Parameters:
        path (str): The path to the source logo file.
        output (str): The path where the converted logos will be saved.
        server_id (str): The ID of the server.
        server_name (str): The name of the server.
        sizes (list): A list of sizes to which the logo will be resized.
        lossless (bool, optional): If set to True, the logo will be converted without any loss
                                   in quality. Default is False.
    """

    # Raw no transformations (PNG)
    shutil.copyfile(path, f"{output}/{server_id}.png")

    # Base 512 Size Logo (WebP)
    convert_and_resize(
        path, f"{output}/{server_id}.webp", lossless=lossless, width=512, height=512
    )

    # Logo Size-based destination name
    for size in sizes:
        convert_and_resize(
            path,
            f"{output}/{server_id}-{size}.webp",
            lossless=lossless,
            width=size,
            height=size,
        )

    print(f"Successfully converted {server_name}'s logo.")


def convert_and_resize(
    source: str,
    destination: str,
    width: int = None,
    height: int = None,
    lossless: bool = False,
):
    """
    This function converts and resizes an image.

    Parameters:
        source (str): The path to the source image file.
        destination (str): The path where the converted image will be saved.
        width (int, optional): The width to resize the image to. If not provided,
                               the original image width is used.
        height (int, optional): The height to resize the image to. If not provided,
                                the original image height is used.
        lossless (bool, optional): If set to True, the image will be converted
                                   without any loss in quality. Default is False.
    """

    # Always strip out the metadata
    options = ["-metadata none"]

    # Only resize if provided
    if width and height:
        options.append(f"-resize {width} {height}")

    # Apply lossless
    if lossless:
        options.append("-lossless")

    output = webptools.cwebp(
        input_image=source, output_image=destination, option=" ".join(options)
    )

    # An error occured
    if output.get("exit_code"):
        print(output)
        raise OSError(f"Failed to run Webptools ({source})")


if __name__ == "__main__":
    main()
