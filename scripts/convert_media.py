import os
import argparse
import shutil
from utils import get_all_servers
import webptools
from PIL import Image as image

# Grant permissions to Webptools
webptools.grant_permission()


def main():
    use_args = os.getenv('USE_ARGS') == "true"
    parser = argparse.ArgumentParser()


    parser.add_argument("--servers_dir", required=use_args, type=str)
    parser.add_argument("--inactive_file", required=use_args, type=str)
    parser.add_argument("--lossless", default=use_args, action="store_true")

    # Logo Args
    parser.add_argument("--servers_logos_output", required=use_args, type=str)
    parser.add_argument("--servers_logos_sizes", nargs="+", type=int, default=[256])

    # Background args
    parser.add_argument("--servers_backgrounds_output", required=use_args, type=str)
    parser.add_argument(
        "--servers_backgrounds_sizes", nargs="+", type=str, default=["1920x1080"]
    )

    # Banner args
    parser.add_argument('--servers_banners_output', required=use_args, type=str)

    args = parser.parse_args()

    # If we don't find the env variable for use args assume we're running this locally
    if not use_args:
        local = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')).replace("\\", "/")

        args.inactive_file = local + "/inactive.json"
        args.servers_dir = local + "/servers"

        args.servers_logos_output = local + "/.out/servers_logos_output"
        args.servers_backgrounds_output = local + "/.out/backgrounds"
        args.servers_banners_output = local + "/.out/banners"
        args.lossless = True

    # Load server mappings JSON
    servers = get_all_servers(args.servers_dir, args.inactive_file, False)

    print(f"Converting {len(servers)} server media...")
    background_amount = 0
    banner_amount = 0

    # Create server media output directory
    os.makedirs(args.servers_logos_output, exist_ok=True)
    os.makedirs(args.servers_backgrounds_output, exist_ok=True)
    os.makedirs(args.servers_banners_output, exist_ok=True)

    for server in servers:
        if server["id"] != "blocksmc":
            print("asd")
            continue
        print('asd2')
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
        f"Sucessfully converted {background_amount} server backgrounds - ({len(servers) - background_amount} servers did not provide a background)."
    )
    print(
        f"Sucessfully converted {banner_amount} server banners - ({len(servers) - banner_amount} servers did not provide a banner)."
    )


def convert_background(path, output, server_id, server_name, sizes, lossless=False):
    if not os.path.isfile(path):
        return False  # Silently skip as it is optional

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

def convert_banner(path, output, server_id, server_name, lossless=False):
    if not os.path.isfile(path):
        return False  # Silently skip as it is optional

    img = image.open(path)

    if img.format == 'PNG':
        # Raw no transformations (PNG)
        shutil.copyfile(path, f"{output}/{server_id}.png")

        # Base full Size (WebP)
        convert_and_resize(
            path,
            f"{output}/{server_id}.webp",
            lossless=lossless,
        )
    elif img.format == 'GIF':
        shutil.copyfile(path, f"{output}/{server_id}.gif")
        gif_to_sprite_sheet(path, output, server_id, lossless)

    print(f"Successfully converted {server_name}'s banner.")
    return True

def gif_to_sprite_sheet(path, output, server_id, lossless=False):
    img = image.open(path)
    sprite_img = image.new('RGBA', (img.width, img.height * img.n_frames))

    for idx in range(0, img.n_frames):
        img.seek(idx)
        sprite_img.paste(img, (0, img.height * idx))

    sprite_img.save(f"{output}/{server_id}.png")
    convert_and_resize(f"{output}/{server_id}.png", f"{output}/{server_id}.webp", lossless=lossless)

def convert_logo(path, output, server_id, server_name, sizes, lossless=False):
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


# Utility to convert and resize images
def convert_and_resize(source, destination, width=None, height=None, lossless=False):
    options = [f"-metadata none"]

    # Only resize if provided
    if width and height:
        options.append(f"-resize {width} {height}")

    if lossless:
        options.append("-lossless")

    output = webptools.cwebp(
        input_image=source, output_image=destination, option=" ".join(options)
    )

    if output.get("exit_code"):
        print(output)
        raise OSError(f"Failed to run Webptools ({source})")


if __name__ == "__main__":
    main()
