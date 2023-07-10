# Server Mappings

## Summary

Server Mappings is a collection of mappings for Minecraft servers, including the most popular servers such as Hypixel, Mineplex, and more. Server Mappings provides information such as server name, server icon and more.

For a full overview of the information which can be found in Server Mappings, [check out our documentation](https://lunarclient.dev/server-mappings/introduction).

## How do I add/update/remove a server?

Each server in Server Mappings is represented by a folder with an accompanying `metadata.json` and `logo.png`. Open a pull request in this repository whilst following the steps below, and we'll review it as soon as possible. Once merged, Lunar Client services will update over the next 20 minutes. Check out `metadata.example.json` as an example of how to structure your metadata file.

## IP Addresses

The `addresses` array in each server object is actually an array of IP _suffixes_. For example, `"addresses": ["lunar.gg", "other.domain"]` will match `lunar.gg`, `na.lunar.gg`, `play.other.domain`, and so on. The `primaryAddress` field is where you can include the desired subdomain (`na.lunar.gg`, `play.lunar.gg`) for users to connect to your server on and is required to be resolvable. This primary address will be used to ensure that the server remains online and active.

## Primary Info & Minecraft Versions

We also require your server's primary connection information and allowed client versions. The `primaryAddress` field should be an address included** in the `addresses` array.

The `minecraftVersions` field must be an array of client versions allowed on your Minecraft server. *(ie. 1.18.1, 1.19.2)*; The `primaryMinecraftVersion` field must be a subversion of a major version included in the `minecraftVersions` array. **The versions you include must be versions that are directly offered in Lunar Client**, which can be found in the version selector of the Lunar Client Launcher.

If your server supports all of the subversions within a major version, you can list the version in `minecraftVersions` as `1.19.*`, but you will still need to specify the specific subversion in the `primaryMinecraftVersion` as this is the specific version that the client uses to Launch you into the game for Quick Joining.

## Logos

In addition to the data that you will need to provide in your `metadata.json`, you will need to upload a `.png` version of your logo into the same folder. All images are to be _transparent_, _square (1:1 aspect ratio)_, and _a minimum of 512px in width and height_. The file name should be `logo.png`. We require the logo to be large as we perform a number of different transformations for all the various places in Lunar Client!

## Backgrounds

Servers are also required to provide background image, you will need to upload a `.png` version of the background into the same folder as your `metadata.json`. Images should represent either the artistic style or the content of the server, with images needing to be _a minimum of 1920px in width and 1080px in height, resulting in a 16:9 aspect ratio_. The file name should be `background.png`. Backgrounds should be free of marketing, text, and/or any logos (that isn't part of a build).

## Banners

Servers may also provide a server banner - you will be made aware if this is a requirement for your server. If a banner is provided, it must be uploaded as either a `.png` version named `banner.png` (for static banners,) or a `.gif` version named `banner.gif` (for animated banners,) in the same folder as your `metadata.json`. Banners should represent the content of the server, and prominently feature the server's name and/or IP. All banners must be _a minimum of 340 pixels wide and 45 pixels high, resulting in a 68:9 aspect ratio._ Additionally, animated (GIF) banners must play at _20 frames per second_, and be no more than _10 seconds in duration_.

## Regions

In your `metadata.json`, you can define both a `primaryRegion` and `regions` which your server supports. Below is a table of the regions.

| Region Code | Name |
| --- | --- |
| AF | Africa |
| AS | Asia |
| EU | Europe |
| NA | North America |
| OC | Oceania |
| SA | South America |

## Game Types

Game types help identify the style of games that your server will offer to player. The following are games you may include: `PvP`, `PvE`, `HCF`, `Factions`, `Minigames`, `Skyblock`, `Parkour`, `UHC`, `Hardcore`, `Survival`, `Open World`, `Prison`, `Creative`, `Roleplay`, and `Adventure`.

You can add up to 3 unique types on the `gameTypes` field in your `metadata.json`.

## Restrictions

We ask that this repository is only used to store mappings for *public* Minecraft servers. Some server IPs, such as private SMPs, tournament servers, etc. should not be listed in this repository, out of respect for privacy.

Lunar Client also reserves the right to omit any servers that do not comply with our [Terms of Service](https://www.lunarclient.com/terms).

## Inactive Server Policy

If a server has closed down or has not been joinable for at least 3 months, we will add it to the `inactive.json`. This just flags our internal systems to not include the server in various place, but still retains all of the branding and other metadata you submit.

If you think your server has been added to this list by mistake, please make a support ticket at the link below.

## Can I use this data for ___?

Go for it!

## Any other questions?

Please contact us at [support.lunarclient.com](https://support.lunarclient.com) for any additional questions.
