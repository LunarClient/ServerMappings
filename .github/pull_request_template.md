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
  - [ ] `minecraftVersions`: an array with Minecraft versions as strings *(ex. `["1.18", "1.19"]`)*
  - [ ] `primaryMinecraftVersion`: a Minecraft version as a string *(ex. `1.18`)*

### Logo Additions or Updates:
* [ ] My image is a `png` file.
* [ ] I uploaded my image to the `logos` directory.
* [ ] My image has a transparent background and is square (1:1 aspect ratio).
* [ ] My image is `512` pixels in width and height.
* [ ] My image's file name matches its mapping id.
