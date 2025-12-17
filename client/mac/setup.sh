#!/usr/bin/env bash

set -xe

echo "===================================="
echo "void-mc macOS Client Setup"
echo "===================================="
echo ""

# Check for Minecraft Launcher
echo "[1/4] Checking for Minecraft Launcher..."
if [ -d "/Applications/Minecraft.app" ]; then
    echo "✓ Minecraft Launcher found"
else
    echo "✗ Minecraft Launcher not found"
    echo ""
    echo "Please install the Minecraft Launcher from:"
    echo "https://www.minecraft.net/en-us/download"
    echo ""
    read -p "Press Enter once you've installed the Minecraft Launcher..."

    if [ ! -d "/Applications/Minecraft.app" ]; then
        echo "Error: Minecraft Launcher still not found. Exiting."
        exit 1
    fi
    echo "✓ Minecraft Launcher found"
fi

echo ""

# Check for Fabric
echo "[2/4] Checking for Fabric installation..."
MINECRAFT_DIR="$HOME/Library/Application Support/minecraft"
FABRIC_VERSION="1.21.1"
FABRIC_LOADER="0.18.3"

if [ -d "$MINECRAFT_DIR/versions/fabric-loader-$FABRIC_LOADER-$FABRIC_VERSION" ]; then
    echo "✓ Fabric already installed"
else
    echo "✗ Fabric not found, installing..."

    # Download Fabric installer
    INSTALLER_URL="https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.0/fabric-installer-1.1.0.jar"
    INSTALLER_PATH="/tmp/fabric-installer.jar"

    echo "Downloading Fabric installer..."
    curl -L -o "$INSTALLER_PATH" "$INSTALLER_URL"

    echo "Running Fabric installer..."
    java -jar "$INSTALLER_PATH" client -dir "$MINECRAFT_DIR" -mcversion "$FABRIC_VERSION" -loader "$FABRIC_LOADER" -noprofile

    echo "✓ Fabric installed successfully"
fi

echo ""

# Check for Tailscale
echo "[3/4] Checking for Tailscale..."
if command -v tailscale &> /dev/null; then
    echo "✓ Tailscale found"

    # Check if connected
    if tailscale status &> /dev/null; then
        echo "✓ Tailscale is connected"
    else
        echo "⚠ Tailscale is installed but not connected"
        echo "Please run: tailscale up"
    fi
else
    echo "✗ Tailscale not found"
    echo ""
    echo "Please install Tailscale:"

    # Check if Homebrew is available
    if command -v brew &> /dev/null; then
        echo "You can install it via Homebrew:"
        echo "  brew install tailscale"
        echo ""
    fi

    echo "Or download from: https://tailscale.com/download/mac"
    echo ""
    read -p "Press Enter once you've installed and connected to Tailscale..."

    if ! command -v tailscale &> /dev/null; then
        echo "Error: Tailscale still not found. Exiting."
        exit 1
    fi
    echo "✓ Tailscale found"
fi

echo ""

# Install mod pack
echo "[4/4] Installing mod pack..."
MODS_DIR="$MINECRAFT_DIR/mods"
mkdir -p "$MODS_DIR"

# Mod versions for Minecraft 1.21.1
declare -A MODS=(
    ["sodium"]="https://cdn.modrinth.com/data/AANobbMI/versions/4OZL6q5h/sodium-fabric-0.6.0-beta.2%2Bmc1.21.jar"
    ["lithium"]="https://cdn.modrinth.com/data/gvQqBUqZ/versions/ZSNsJrPI/lithium-fabric-mc1.21.1-0.13.0.jar"
    ["phosphor"]="https://cdn.modrinth.com/data/hEOCdOgW/versions/rEIndJQI/phosphor-fabric-mc1.21-0.8.1.jar"
)

for mod_name in "${!MODS[@]}"; do
    mod_url="${MODS[$mod_name]}"
    mod_filename=$(basename "$mod_url" | sed 's/%2B/+/g')

    if [ -f "$MODS_DIR/$mod_filename" ]; then
        echo "✓ $mod_name already installed"
    else
        echo "Downloading $mod_name..."
        curl -L -o "$MODS_DIR/$mod_filename" "$mod_url"
        echo "✓ $mod_name installed"
    fi
done

echo ""
echo "===================================="
echo "Setup complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Launch Minecraft"
echo "2. Select the Fabric profile"
echo "3. Join the server via Tailscale"
