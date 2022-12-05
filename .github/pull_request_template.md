### General:
* [ ] The pull request title is descriptive. *(ex. `Added Lunar Network`, not `Updated metadata.json`)*
* [ ] The pull request does not contain any unrelated commits.  *(ex. commits from previous pull requests)*

### Mapping Additions or Updates:
* [ ] Folder with appropriate name has been created / updated (must not include any non-alpha characters or whitespace).
* [ ] No changes were made to the file's formatting (4 spaces per tab).
* [ ] There are no syntax errors.
* [ ] There is no pre-existing mapping matching my id (check if there is an existing folder).
* [ ] My field values match your requirements.
* You can view our patterns here: [metadata.schema.json](https://github.com/LunarClient/ServerMappings/blob/master/metadata.schema.json), or take a look below and complete the field checklist:
  - [ ] `id`: a lowercase string, which should match the folder name *(ex. `myserver`)*
  - [ ] `name`: a string *(ex. `MyServerPvP`)*
  - [ ] `description`: hook between 16 and 80 characters *(ex. `Home of Competitive Minecraft PvP`)* 
  - [ ] `addresses`: an array with lowercase strings *(ex. `["my.server", "your-server.com"]`)*
    - You do not need to specify subdomains, Lunar Client services automatically detect them.
  - [ ] `primaryAddress`: the primary address that people connect to with (please include the subdomain if required) *(ex. `mc.my.server`)*
  - [ ] `minecraftVersions`: an array with Minecraft versions as strings *(ex. `["1.18.*", "1.19.*"]` - Must be versions supported by Lunar Client)*
  - [ ] `primaryMinecraftVersion`: a Minecraft version as a string *(ex. `1.18` - Must be versions supported by Lunar Client)*
  - [ ] `primaryColor`: a hexademical color code that primarily distinguishes the server *(ex. `#00FFFF`)* 
  - [ ] `secondaryColor`: a hexademical color code that accompanies the `primaryColor` of the server *(ex. `#FF0000`)*
  - [ ] `primaryRegion`: the primary region where your server operates in *(ex. `NA`)*
  - [ ] `regions`: a list of regions where you have servers located that service your players *(ex. `["NA", "EU", "AS"]`)*
  - [ ] `gameTypes`: a list of games that describe the content on your server, must be a max of 3 listed *(ez. `["PVP", "UHC", "HCF"]`)*
  - [ ] (optional) `website`: url of server website, must include URL schema (http:// or https://) *(ex. `https://www.your-server.com`)*
  - [ ] (optional) `store`: url of server store, must include URL schema (http:// or https://) *(ex. `https://store.your-server.com`)*

### Socials
* [ ] (optional) `twitter`: username of twitter account without the @ *(ex. MyServer)*
* [ ] (optional) `discord`: invite link to discord *(ex. https://discord.com/invite/4ceEJuH)*
* [ ] (optional) `youtube`: slug or username of youtube channel *(ex. MyServer)*
* [ ] (optional) `instagram`: username of instagram account *(ex. MyServer)*
* [ ] (optional) `twitch`: username of twitch account *(ex. MyServer)*
* [ ] (optional) `telegram`: slug of telegram group *(ex. MyServer)*
* [ ] (optional) `reddit`: slug of subdreddit wtih 'r/' *(ex. MyServer)*
* [ ] (optional) `tiktok`: username of tiktok account *(ex. MyServer)*
* [ ] (optional) `facebook`: slug of facebook page *(ex. MyServer)*

### Media:
#### Logo
* [ ] My logo is a `png` file.
* [ ] I have uploaded my logo to my server folder *(ex. `lunarnetwork`)* and named it `logo.png`.
* [ ] My logo has a transparent background and is square (1:1 aspect ratio).
* [ ] My logo is `512` pixels in width and height.
* [ ] My logo is my own property and complies with relevant copyright/privacy laws.

#### Background
* [ ] My background is a `png` file.
* [ ] I have uploaded my background to my server folder *(ex. `lunarnetwork`)* and named it `background.png`.
* [ ] My background has an aspect ratio of 16:9.
* [ ] My background is atleast `1920` pixels in width and `1080` pixels in height (can be bigger, but must remain the same aspect ratio).
* [ ] My background contains relevant content pertaining to the server, is my own property, and complies with relevant copyright/privacy laws.
* [ ] My background doesn't contain any markings, text, or logos (unless part of a build).
