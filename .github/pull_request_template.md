### General:

-   [ ] The pull request title is descriptive. _(ex. `Added Lunar Network`, not `Updated metadata.json`)_
-   [ ] The pull request does not contain any unrelated commits. _(ex. commits from previous pull requests)_

### Mapping Additions or Updates:

-   [ ] Folder with appropriate name has been created / updated (must not include any non-alpha characters or whitespace).
-   [ ] No changes were made to the file's formatting (4 spaces per tab).
-   [ ] There are no syntax errors.
-   [ ] There is no pre-existing mapping matching my id (check if there is an existing folder).
-   [ ] My field values match your requirements.
-   You can view our patterns here: [metadata.schema.json](https://github.com/LunarClient/ServerMappings/blob/master/metadata.schema.json), or take a look below and complete the field checklist:
    -   [ ] `id`: a lowercase string, which should match the folder name _(ex. `myserver`)_
    -   [ ] `name`: a string _(ex. `MyServerPvP`)_
    -   [ ] `description`: hook between 16 and 80 characters _(ex. `Home of Competitive Minecraft PvP`)_
    -   [ ] `addresses`: an array with lowercase strings _(ex. `["my.server", "your-server.com"]`)_
        -   You do not need to specify subdomains, Lunar Client services automatically detect them.
    -   [ ] `primaryAddress`: the primary address that people connect to with (please include the subdomain if required) _(ex. `mc.my.server`)_
    -   [ ] `minecraftVersions`: an array with Minecraft versions as strings _(ex. `["1.18._", "1.19.2"]` - Must be versions or subversions supported by Lunar Client)\*
    -   [ ] `primaryMinecraftVersion`: a Minecraft version as a string _(ex. `1.19.2` - Must be a subversion supported by Lunar Client)_
    -   [ ] `primaryColor`: a hexademical color code that primarily distinguishes the server _(ex. `#00FFFF`)_
    -   [ ] `secondaryColor`: a hexademical color code that accompanies the `primaryColor` of the server _(ex. `#FF0000`)_
    -   [ ] `primaryRegion`: the primary region where your server operates in _(ex. `NA`)_
    -   [ ] `regions`: a list of regions where you have servers located that service your players _(ex. `["NA", "EU", "AS"]`)_
    -   [ ] `gameTypes`: a list of games that describe the content on your server, must be a max of 3 listed _(ez. `["PVP", "UHC", "HCF"]`)_
    -   [ ] `crossplay`: whether the server has support for Bedrock Edition players (through proxies such as [GeyserMC](https://geysermc.org/))
    -   [ ] (optional) `website`: url of server website, must include URL schema (http:// or https://) _(ex. `https://www.your-server.com`)_
    -   [ ] (optional) `store`: url of server store, must include URL schema (http:// or https://) _(ex. `https://store.your-server.com`)_

### Socials

-   [ ] (optional) `twitter`: username of twitter account without the @ _(ex. MyServer)_
-   [ ] (optional) `discord`: invite link to discord _(ex. https://discord.com/invite/4ceEJuH)_
-   [ ] (optional) `youtube`: slug or username of youtube channel _(ex. MyServer)_
-   [ ] (optional) `instagram`: username of instagram account _(ex. MyServer)_
-   [ ] (optional) `twitch`: username of twitch account _(ex. MyServer)_
-   [ ] (optional) `telegram`: slug of telegram group _(ex. MyServer)_
-   [ ] (optional) `reddit`: slug of subdreddit wtih 'r/' _(ex. MyServer)_
-   [ ] (optional) `tiktok`: username of tiktok account _(ex. MyServer)_
-   [ ] (optional) `facebook`: slug of facebook page _(ex. MyServer)_

### Media:

#### Logo

-   [ ] My logo is a `png` file.
-   [ ] I have uploaded my logo to my server folder _(ex. `lunarnetwork`)_ and named it `logo.png`.
-   [ ] My logo has a transparent background and is square (1:1 aspect ratio).
-   [ ] My logo is `512` pixels in width and height.
-   [ ] My logo is my own property and complies with relevant copyright/privacy laws.

#### Background

-   [ ] My background is a `png` file.
-   [ ] I have uploaded my background to my server folder _(ex. `lunarnetwork`)_ and named it `background.png`.
-   [ ] My background has an aspect ratio of 16:9.
-   [ ] My background is atleast `1920` pixels in width and `1080` pixels in height (can be bigger, but must remain the same aspect ratio).
-   [ ] My background contains relevant content pertaining to the server, is my own property, and complies with relevant copyright/privacy laws.
-   [ ] My background doesn't contain any markings, text, or logos (unless part of a build).
