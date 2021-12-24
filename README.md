# Server Mappings

## Summary

This is a public mapping of server IPs <-> a pretty display name. This data is used extensively around Lunar Client, most notably when displaying server names (or "Private Server", if unknown) on the friends list. Historically, this mapping was handled internally, and server owners did not have a good way to manage data for their server.

## How do I add/update/remove a server?

Please feel free to open a PR against `servers.json` in this repository, and we'll review it as soon as possible. Once merged, Lunar Client services will update over the next 20 minutes.

## IP Addresses

The `addresses` array in each server object is actually an array of IP _suffixes_. For example, `"addresses": ["lunar.gg", "other.domain"]` will match `lunar.gg`, `na.lunar.gg`, `play.other.domain`, and so on.

## Logos
In addition to the entry that you will need to provide in the `servers.json`, you will need to upload a `.png` version of your logo into the `/logos` directory in this repository. All images are to be _transparent_, _square (1:1 aspect ratio)_, and _a minimum of 512px in width and height_. The file name should match the server ID in the `servers.json` (for example: `lunarnetwork.png`).

## Restrictions

We ask that this repository is only used to store mappings for *public* Minecraft servers. Some server IPs, such as private SMPs, tournament servers, etc. should not be listed in this repository, out of respect for privacy.

## Can I use this data for ___?

Go for it.

## Any other questions?

Please contact us at https://support.lunarclient.com for any additional questions.
