### General:
* [ ] The pull request title is descriptive. *(ex. `Added Lunar Network`, not `Updated servers.json`)*
* [ ] The pull request does not contain any unrelated commits.  *(ex. commits from previous pull requests)*

### Mapping Additions or Updates:
* [ ] No changes were made to the file's formatting.
* [ ] There are no syntax errors.
* [ ] There is no pre-existing mapping matching my id.
* [ ] My field values match your requirements.
* You can view our patterns here: [servers.schema.json](https://github.com/LunarClient/ServerMappings/blob/master/servers.schema.json), or take a look below and complete the field checklist:
  - [ ] `id`: a lowercase string *(ex. `myserver`)*
  - [ ] `name`: a string *(ex. `MyServerPvP`)*
  - [ ] `addresses`: an array with lowercase strings *(ex. `["my.server", "your-server.com"]`)*
    - You do not need to specify subdomains, Lunar Client services automatically detect them.
  - [ ] `primaryAddress`: an address *(ex. `my.server`)*
  - [ ] `minecraftVersions`: an array with Minecraft versions as strings *(ex. `["1.18", "1.19"]` - Must be versions supported by Lunar Client)*
  - [ ] `primaryMinecraftVersion`: a Minecraft version as a string *(ex. `1.18` - Must be versions supported by Lunar Client)*
  - [ ] `primaryColor`: a hexademical color code that primarily distiguishes the server *(ex. `#00FFFF`)* 
  - [ ] `secondaryColor`: a hexademical color code that accompanies the `primaryColor` of the server *(ex. `#FF0000`)*

### Media:
#### Logo
* [ ] My logo is a `png` file.
* [ ] I uploaded my logo to the `logos` directory.
* [ ] My logo has a transparent background and is square (1:1 aspect ratio).
* [ ] My logo is `512` pixels in width and height.
* [ ] My logo's file name matches its mapping id.
* [ ] My logo is my own property and complies with relevant copyright/privacy laws.

#### Background
* [ ] My background is a `png` file.
* [ ] I uploaded my background to the `backgrounds` directory.
* [ ] My background has an aspect ratio of 16:9.
* [ ] My background is atleast `1920` pixels in width and `1080` pixels in height (can be bigger, but must remain the same aspect ratio).
* [ ] My background's file name matches its mapping id.
* [ ] My background contains relevant content pertaining to the server, is my own property, and complies with relevant copyright/privacy laws.