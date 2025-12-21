.PHONY: all install-deps setup generate-config server-mods client-mods run-server accept-eula inject-settings clean clean-all help

VENV := venv
PYTHON := $(VENV)/bin/python3
MODS_DIR := server/mods
CLIENT_MODS_DIR := client/mods
SERVER_JAR := server/void-mc-launcher.jar

all: help

help:
	@echo "void-mc Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install-deps    - Create venv and install Python dependencies (run this first)"
	@echo "  setup           - Run interactive configuration wizard to create config.toml"
	@echo "  generate-config - Generate JSON files from config.toml"
	@echo "  server-mods     - Download server-side mods from server-mods.json"
	@echo "  client-mods     - Download client-side mods from client-mods.json"
	@echo "  accept-eula     - Accept Minecraft EULA (required before first server run)"
	@echo "  inject-settings - Inject server-settings.json into server.properties"
	@echo "  run-server      - Download server mods and run the Minecraft server"
	@echo "  clean           - Remove downloaded mods and temporary files"
	@echo "  clean-all       - Remove everything including venv and config files"
	@echo "  help            - Show this help message"

install-deps:
	@echo "Creating virtual environment..."
	@python3 -m venv $(VENV)
	@echo "Installing Python dependencies..."
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -r requirements.txt
	@echo "Dependencies installed successfully"

setup:
	@echo "Running configuration wizard..."
	@$(PYTHON) setup.py

generate-config:
	@echo "Generating configuration files from config.toml..."
	@$(PYTHON) generate-config.py

server-mods:
	@echo "Fetching server-side mods..."
	@$(PYTHON) fetch-mods.py server-mods.json $(MODS_DIR)

client-mods:
	@echo "Fetching client-side mods..."
	@$(PYTHON) fetch-mods.py client-mods.json $(CLIENT_MODS_DIR)

accept-eula:
	@if [ ! -f server/eula.txt ]; then \
		echo "Error: server/eula.txt not found."; \
		echo "Please run 'make run-server' first to generate the EULA file."; \
		exit 1; \
	fi
	@echo "Accepting Minecraft EULA..."
	@sed -i.bak 's/eula=false/eula=true/' server/eula.txt
	@rm -f server/eula.txt.bak
	@echo "✓ EULA accepted"

inject-settings:
	@echo "Injecting server settings from server-settings.json..."
	@$(PYTHON) inject-server-settings.py

run-server: server-mods
	@# Check if this is the first run (no eula.txt exists)
	@if [ ! -f server/eula.txt ]; then \
		echo "First time setup detected..."; \
		echo "Running server to generate configuration files..."; \
		cd server && timeout 10 java -Xmx2G -jar void-mc-launcher.jar nogui || true; \
		echo ""; \
		echo "========================================"; \
		echo "EULA ACCEPTANCE REQUIRED"; \
		echo "========================================"; \
		echo "The Minecraft EULA has been generated at server/eula.txt"; \
		echo ""; \
		echo "To continue, you must:"; \
		echo "  1. Read the EULA at https://aka.ms/MinecraftEULA"; \
		echo "  2. Run 'make accept-eula' to accept the terms"; \
		echo "  3. Run 'make run-server' again to start the server"; \
		echo ""; \
		exit 1; \
	fi
	@# Check if EULA has been accepted
	@if ! grep -q "eula=true" server/eula.txt 2>/dev/null; then \
		echo "========================================"; \
		echo "EULA NOT ACCEPTED"; \
		echo "========================================"; \
		echo "You must accept the Minecraft EULA before running the server."; \
		echo ""; \
		echo "To continue:"; \
		echo "  1. Read the EULA at https://aka.ms/MinecraftEULA"; \
		echo "  2. Run 'make accept-eula' to accept the terms"; \
		echo "  3. Run 'make run-server' again"; \
		echo ""; \
		exit 1; \
	fi
	@# EULA accepted - inject settings and run server
	@echo "EULA accepted ✓"
	@echo ""
	@$(MAKE) inject-settings
	@echo ""
	@echo "Starting Minecraft server..."
	@cd server && java -Xmx2G -jar void-mc-launcher.jar nogui

clean:
	@echo "Cleaning up mods..."
	@rm -rf $(MODS_DIR)
	@rm -rf $(CLIENT_MODS_DIR)/*.jar
	@echo "Clean complete"

clean-all: clean
	@echo "Removing virtual environment and config files..."
	@rm -rf $(VENV)
	@rm -f config.toml .env
	@rm -f client-mods.json server-mods.json server-settings.json
	@echo "All clean"
