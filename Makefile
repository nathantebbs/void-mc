.PHONY: all install-deps setup generate-config server-mods client-mods run-server clean clean-all help

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

run-server: server-mods
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
