#!/usr/bin/env python3
"""
Configuration Generator Script

Reads config.toml and generates JSON configuration files for:
- client-mods.json (client mod fetching)
- server-mods.json (server mod fetching)
- server-settings.json (server.properties generation)
"""

import sys
import json
from pathlib import Path

# Handle TOML library imports (Python 3.11+ has tomllib built-in)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: tomli not installed. Please run 'make install-deps' first.")
        sys.exit(1)


def load_config():
    """Load configuration from config.toml."""
    config_path = Path("config.toml")
    if not config_path.exists():
        print("Error: config.toml not found.")
        print("Please run 'python setup.py' to generate the configuration file.")
        sys.exit(1)

    with open(config_path, 'rb') as f:
        return tomllib.load(f)


def extract_mods_from_toml(config, mod_type):
    """Extract mod list from TOML config."""
    mods = []
    mod_section = config.get(mod_type, [])

    # Handle the nested structure [[client_mods]] -> [[client_mods.mod]]
    if isinstance(mod_section, list) and len(mod_section) > 0:
        for section in mod_section:
            if 'mod' in section:
                mod_list = section['mod']
                if isinstance(mod_list, list):
                    mods.extend(mod_list)
                else:
                    mods.append(mod_list)

    return mods


def generate_mod_json(config, mod_type, output_file):
    """Generate JSON file for mod fetching."""
    versions = config.get('versions', {})
    mods = extract_mods_from_toml(config, mod_type)

    mod_config = {
        'minecraft': {
            'version': versions.get('minecraft', '1.21.1')
        },
        'fabric': {
            'loader': versions.get('fabric_loader', '0.18.3')
        },
        'mods': mods
    }

    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(mod_config, f, indent=2)

    print(f"✓ Generated {output_file} ({len(mods)} mods)")


def generate_server_settings_json(config, output_file):
    """Generate JSON file for server.properties."""
    server = config.get('server', {})
    versions = config.get('versions', {})

    # Build server settings dict
    server_settings = {
        'minecraft_version': versions.get('minecraft', '1.21.1'),
        'level_seed': server.get('seed', ''),
        'difficulty': server.get('difficulty', 'normal'),
        'gamemode': server.get('gamemode', 'survival'),
        'max_players': server.get('max_players', 20),
        'view_distance': server.get('view_distance', 10),
        'pvp': server.get('pvp', True),
        'online_mode': server.get('online_mode', True),
        'spawn_protection': server.get('spawn_protection', 16),
        'motd': server.get('motd', 'A Minecraft Server'),
    }

    # Add any additional properties from the server section
    for key, value in server.items():
        if key not in ['seed', 'difficulty', 'gamemode', 'max_players',
                       'view_distance', 'pvp', 'online_mode', 'spawn_protection', 'motd']:
            # Convert Python booleans to strings for server.properties
            if isinstance(value, bool):
                server_settings[key] = value
            else:
                server_settings[key] = value

    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(server_settings, f, indent=2)

    print(f"✓ Generated {output_file}")


def main():
    """Main generator function."""
    print("Generating configuration files from config.toml...")
    print()

    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config.toml: {e}")
        sys.exit(1)

    try:
        # Generate client mods JSON
        generate_mod_json(config, 'client_mods', 'client-mods.json')

        # Generate server mods JSON
        generate_mod_json(config, 'server_mods', 'server-mods.json')

        # Generate server settings JSON
        generate_server_settings_json(config, 'server-settings.json')

        print()
        print("Configuration files generated successfully!")
        print()
        print("Next steps:")
        print("  - Run 'make server-mods' to download server mods")
        print("  - Run 'make client-mods' to download client mods")
        print("  - Run 'make run-server' to start the server")

    except Exception as e:
        print(f"Error generating configuration files: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
