# void-mc TODO

## Pending Tasks

### Server Setup
- [ ] Automatically edit eula, and server.properties with secrets post server files being created
- [ ] Officialize release
- [ ] Datapack script integration
  - [x] Datapacks downloaded server-side
  - [ ] YAML config files
  - [ ] New makefile target

### Documentation
- [ ] Enhance README with connection instructions and server details
- [ ] docs/ github pages
  - [ ] custom theme or something else

### Other
- [ ] Discord bot?

## Completed
- [x] Does the new makefile system work as expected?
- [x] server_setup.py? servermodlist.toml?
- [x] Add server-compatible mods (Lithium, Phosphor, Chunky) to /mods
- [x] Create .gitignore file for runtime files
- [x] Remove Starlight from README (replaced by Phosphor)
- [x] Make initial git commit
- [x] Create Linux client setup script
- [x] Create Windows client setup script
- [x] Migrate to TOML -> JSON configuration pipeline
  - [x] root/config.toml sets basic project settings, seed, difficulty, ip etc (saved as secrets?)
  - [x] python script generates JSON which utility scripts use as input for fetching
  - [x] top level setup CLI which generates the basic config.toml which the user then can text edit based
  on automatically generated comments explaining the file.

