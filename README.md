# Server Mappings

## Summary

This is a public mapping of server IPs <-> a pretty display name. This data is used extensively around Lunar Client, most notably when displaying server names (or "Private Server", if unknown) on the friends list. Historically, this mapping was handled internally, and server owners did not have a good way to manage data for their server.

## How do I add/update/remove a server?

Please feel free to open a PR against `servers.json` in this repository, and we'll review it as soon as possible. Once merged, Lunar Client services will update over the next 20 minutes.

## IP Addresses

The `addresses` array in each server object is actually an array of IP _suffixes_. For example, `"addresses": ["lunar.gg", "other.domain"]` will match `lunar.gg`, `na.lunar.gg`, `play.other.domain`, and so on.

## Primary Info & Minecraft Versions
We also require your server's primary connection information and allowed client versions. The `primaryAddress` field should be an address included** in the `addresses` array. The `minecraftVersions` field must be an array of client versions allowed on your Minecraft server. *(ie. 1.18, 1.19)*; The `primaryMinecraftVersion` field must be a version included in the `minecraftVersions` array.

## Logos
In addition to the entry that you will need to provide in the `servers.json`, you will need to upload a `.png` version of your logo into the `/logos` directory in this repository. All images are to be _transparent_, _square (1:1 aspect ratio)_, and _a minimum of 512px in width and height_. The file name should match the server ID in the `servers.json` (for example: `lunarnetwork.png`).

## Backgrounds
Servers are also required to provide background image, you will need to upload a `.png` version of the background into the `/backgrounds` directory in this repository. Images should represent either the artistic style or the content of the server, with images needing to be _a minimum of 1920px in width and 1080px in height, resulting in a 16:9 aspect ratio_. The file name should match the server ID in the `servers.json` (for example: `lunarnetwork.png`).

## Restrictions

We ask that this repository is only used to store mappings for *public* Minecraft servers. Some server IPs, such as private SMPs, tournament servers, etc. should not be listed in this repository, out of respect for privacy.

Lunar Client also reserves the right to omit any servers that do not comply with our [Terms of Service](https://www.lunarclient.com/terms).

## Can I use this data for ___?

Go for it.

## Any other questions?

Please contact us at [support.lunarclient.com](https://support.lunarclient.com) for any additional questions.
