#!/usr/bin/env python3
"""
Mod Fetcher Script

Downloads Minecraft mods from a JSON configuration file to a specified directory.
Usage: ./fetch-mods.py <config-file> <output-dir>
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path


def download_file(url: str, destination: Path, description: str = "file"):
    """Download a file with progress indication."""
    print(f"Downloading {description}...")

    try:
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)

            print()
    except Exception as e:
        print(f"\nError downloading {description}: {e}")
        raise


def fetch_mods(config_file: Path, output_dir: Path):
    """Download mods from configuration file to output directory."""
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    mods = config.get('mods', [])
    if not mods:
        print("No mods found in configuration file")
        return

    print(f"Fetching {len(mods)} mod(s) to {output_dir}")
    print()

    for mod in mods:
        mod_name = mod["name"]
        mod_url = mod["url"]

        mod_filename = urllib.parse.unquote(os.path.basename(mod_url))
        mod_path = output_dir / mod_filename

        if mod_path.exists():
            print(f"✓ {mod_name} already exists, skipping")
        else:
            download_file(mod_url, mod_path, mod_name)
            print(f"✓ {mod_name} downloaded")

    print()
    print(f"All mods fetched to {output_dir}")


def main():
    if len(sys.argv) != 3:
        print("Usage: fetch-mods.py <config-file> <output-dir>")
        print()
        print("Example:")
        print("  ./fetch-mods.py server-mods.json mods/")
        sys.exit(1)

    config_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    fetch_mods(config_file, output_dir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
