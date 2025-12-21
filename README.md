# void-mc

A leightweight Fabric Minecraft server connecting users via [Tailscale](https://tailscale.com/)

## Quick Start

### 1. Install Dependencies

```bash
make install-deps
```

This creates a Python virtual environment and installs required packages.

### 2. Run Setup Wizard

```bash
make setup
```

This launches an interactive configuration wizard that will:
- Prompt for Minecraft and Fabric versions
- Ask for server settings (seed, difficulty, gamemode, etc.)
- Request server IP and port (saved to `.env`)
- Migrate existing mod configurations from YAML to TOML
- Generate `config.toml` configuration file

### 3. Generate Configuration Files

```bash
make generate-config
```

This reads `config.toml` and generates JSON files for:
- `client-mods.json` - Client-side mod configuration
- `server-mods.json` - Server-side mod configuration
- `server-settings.json` - Server properties configuration

### 4. Download Mods and Run Server

```bash
# Download server mods
make server-mods

# Download client mods (optional)
make client-mods

# Run the server
make run-server
```

## Configuration

After running `make setup`, you can manually edit `config.toml` to:
- Add or remove mods
- Adjust server settings
- Customize server properties

After making changes, run `make generate-config` to regenerate the JSON files.

## Available Make Targets

- `make install-deps` - Install Python dependencies
- `make setup` - Run interactive configuration wizard
- `make generate-config` - Generate JSON files from config.toml
- `make server-mods` - Download server mods
- `make client-mods` - Download client mods
- `make run-server` - Start the Minecraft server
- `make clean` - Remove downloaded mods
- `make clean-all` - Remove all generated files and venv

## Utilities Versions

- [Minecraft](https://www.minecraft.net/): 1.21.11
- [Fabric Loader](https://fabricmc.net/): 0.18.3
- [Fabric Installer](https://fabricmc.net/use/installer/): 1.1.0

## Mod List

> [!NOTE]
> This list is subject to change before official version of the server is released

- [Sodium](https://modrinth.com/mod/sodium)
- [Lithium](https://modrinth.com/mod/lithium)
- [Chunky](https://modrinth.com/plugin/chunky)
- [Litematica](https://modrinth.com/mod/litematica)

## Seed

**6944174826991112**

![img](./assets/seedshot.png)
