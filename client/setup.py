#!/usr/bin/env python3
"""
void-mc Cross-Platform Client Setup

Automatically installs and configures Minecraft Fabric client with mods.
"""

import os
import sys
import platform
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: tomllib not available. Please install tomli for Python < 3.11:")
        print("  pip install tomli")
        sys.exit(1)


def get_minecraft_dir() -> Path:
    """Get the Minecraft directory based on the current OS."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "minecraft"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA environment variable not found")
        return Path(appdata) / ".minecraft"
    elif system == "Linux":
        return Path.home() / ".minecraft"
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")


def check_minecraft_launcher() -> bool:
    """Check if Minecraft Launcher is installed."""
    system = platform.system()

    if system == "Darwin":
        return Path("/Applications/Minecraft.app").exists()
    elif system == "Windows":
        launcher_paths = [
            Path(os.getenv("PROGRAMFILES", "")) / "Minecraft Launcher" / "MinecraftLauncher.exe",
            Path(os.getenv("PROGRAMFILES(X86)", "")) / "Minecraft Launcher" / "MinecraftLauncher.exe",
        ]
        return any(p.exists() for p in launcher_paths)
    elif system == "Linux":
        minecraft_dir = get_minecraft_dir()
        return minecraft_dir.exists() or subprocess.run(
            ["which", "minecraft-launcher"],
            capture_output=True
        ).returncode == 0

    return False


def check_tailscale() -> tuple[bool, bool]:
    """Check if Tailscale is installed and connected.

    Returns:
        (installed, connected) tuple
    """
    try:
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            text=True
        )
        return (True, result.returncode == 0)
    except FileNotFoundError:
        return (False, False)


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

            print()  # New line after progress
    except Exception as e:
        print(f"\nError downloading {description}: {e}")
        raise


def install_fabric(minecraft_dir: Path, mc_version: str, loader_version: str, installer_url: str):
    """Install Fabric loader if not already installed."""
    fabric_version_dir = minecraft_dir / "versions" / f"fabric-loader-{loader_version}-{mc_version}"

    if fabric_version_dir.exists():
        print("✓ Fabric already installed")
        return

    print("✗ Fabric not found, installing...")

    installer_path = Path("/tmp" if platform.system() != "Windows" else os.getenv("TEMP", ".")) / "fabric-installer.jar"
    download_file(installer_url, installer_path, "Fabric installer")

    print("Running Fabric installer...")
    result = subprocess.run([
        "java", "-jar", str(installer_path),
        "client",
        "-dir", str(minecraft_dir),
        "-mcversion", mc_version,
        "-loader", loader_version,
        "-noprofile"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error installing Fabric: {result.stderr}")
        sys.exit(1)

    print("✓ Fabric installed successfully")


def install_mods(minecraft_dir: Path, mods: list[dict]):
    """Download and install mods."""
    mods_dir = minecraft_dir / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)

    for mod in mods:
        mod_name = mod["name"]
        mod_url = mod["url"]

        # Decode URL-encoded filename
        mod_filename = urllib.parse.unquote(os.path.basename(mod_url))
        mod_path = mods_dir / mod_filename

        if mod_path.exists():
            print(f"✓ {mod_name} already installed")
        else:
            download_file(mod_url, mod_path, mod_name)
            print(f"✓ {mod_name} installed")


def main():
    print("=" * 40)
    print("void-mc Client Setup")
    print("=" * 40)
    print()

    # Load configuration
    config_path = Path(__file__).parent / "clientmodlist.toml"

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    minecraft_dir = get_minecraft_dir()
    print(f"Minecraft directory: {minecraft_dir}")
    print()

    # Check for Minecraft Launcher
    print("[1/4] Checking for Minecraft Launcher...")
    if check_minecraft_launcher():
        print("✓ Minecraft Launcher found")
    else:
        print("✗ Minecraft Launcher not found")
        print()
        print("Please install the Minecraft Launcher from:")
        print("https://www.minecraft.net/en-us/download")
        print()
        input("Press Enter once you've installed the Minecraft Launcher...")

        if not check_minecraft_launcher():
            print("Error: Minecraft Launcher still not found. Exiting.")
            sys.exit(1)
        print("✓ Minecraft Launcher found")

    print()

    # Check for Fabric
    print("[2/4] Checking for Fabric installation...")
    install_fabric(
        minecraft_dir,
        config["minecraft"]["version"],
        config["fabric"]["loader"],
        config["fabric"]["installer_url"]
    )

    print()

    # Check for Tailscale
    print("[3/4] Checking for Tailscale...")
    installed, connected = check_tailscale()

    if installed:
        print("✓ Tailscale found")
        if connected:
            print("✓ Tailscale is connected")
        else:
            print("⚠ Tailscale is installed but not connected")
            print("Please run: tailscale up")
    else:
        print("✗ Tailscale not found")
        print()
        print("Please install Tailscale from: https://tailscale.com/download")

        system = platform.system()
        if system == "Darwin" and subprocess.run(["which", "brew"], capture_output=True).returncode == 0:
            print("You can install it via Homebrew:")
            print("  brew install tailscale")
        elif system == "Linux":
            print("On most Linux distributions:")
            print("  curl -fsSL https://tailscale.com/install.sh | sh")

        print()
        input("Press Enter once you've installed and connected to Tailscale...")

        installed, _ = check_tailscale()
        if not installed:
            print("Error: Tailscale still not found. Exiting.")
            sys.exit(1)
        print("✓ Tailscale found")

    print()

    # Install mods
    print("[4/4] Installing mod pack...")
    install_mods(minecraft_dir, config["mods"])

    print()
    print("=" * 40)
    print("Setup complete!")
    print("=" * 40)
    print()
    print("Next steps:")
    print("1. Launch Minecraft")
    print("2. Select the Fabric profile")
    print("3. Join the server via Tailscale")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
