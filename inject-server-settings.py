#!/usr/bin/env python3
"""
Server Settings Injection Script

Reads server-settings.json and injects values into server/server.properties.
This preserves any existing settings while updating configured values.
"""

import json
import sys
from pathlib import Path


def load_server_settings():
    """Load server settings from server-settings.json."""
    settings_path = Path("server-settings.json")
    if not settings_path.exists():
        print("Error: server-settings.json not found.")
        print("Please run 'make generate-config' first.")
        sys.exit(1)

    with open(settings_path, 'r') as f:
        return json.load(f)


def parse_properties_file(properties_path):
    """Parse server.properties file into a dict."""
    properties = {}

    if not properties_path.exists():
        return properties

    with open(properties_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse key=value
            if '=' in line:
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()

    return properties


def write_properties_file(properties_path, properties):
    """Write properties dict to server.properties file."""
    lines = [
        "#Minecraft server properties",
        "#Modified by inject-server-settings.py",
        ""
    ]

    for key, value in sorted(properties.items()):
        lines.append(f"{key}={value}")

    with open(properties_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def convert_value_for_properties(value):
    """Convert Python value to server.properties format."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def main():
    """Main injection function."""
    server_dir = Path("server")
    properties_path = server_dir / "server.properties"

    if not server_dir.exists():
        print("Error: server directory not found.")
        sys.exit(1)

    if not properties_path.exists():
        print("Warning: server.properties not found.")
        print("The server must be run once to generate server.properties.")
        print("The server will generate it on first run (and fail due to EULA).")
        return

    # Load settings from JSON
    settings = load_server_settings()

    # Load existing properties
    properties = parse_properties_file(properties_path)

    # Map JSON keys to server.properties keys
    property_mapping = {
        'level_seed': 'level-seed',
        'difficulty': 'difficulty',
        'gamemode': 'gamemode',
        'max_players': 'max-players',
        'view_distance': 'view-distance',
        'pvp': 'pvp',
        'online_mode': 'online-mode',
        'spawn_protection': 'spawn-protection',
        'motd': 'motd',
    }

    # Update properties with settings
    updated_count = 0
    for json_key, prop_key in property_mapping.items():
        if json_key in settings:
            old_value = properties.get(prop_key)
            new_value = convert_value_for_properties(settings[json_key])

            if old_value != new_value:
                properties[prop_key] = new_value
                updated_count += 1
                print(f"✓ Updated {prop_key}: {old_value} → {new_value}")

    # Handle any additional properties from JSON that aren't in the mapping
    for key, value in settings.items():
        if key not in property_mapping and key != 'minecraft_version':
            # Convert underscores to hyphens for property names
            prop_key = key.replace('_', '-')
            old_value = properties.get(prop_key)
            new_value = convert_value_for_properties(value)

            if old_value != new_value:
                properties[prop_key] = new_value
                updated_count += 1
                print(f"✓ Updated {prop_key}: {old_value} → {new_value}")

    # Write updated properties
    if updated_count > 0:
        write_properties_file(properties_path, properties)
        print(f"\n✓ Injected {updated_count} settings into server.properties")
    else:
        print("✓ No changes needed - server.properties is up to date")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
