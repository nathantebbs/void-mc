.PHONY: all setup server-mods client-mods run-server clean clean-all help

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
	@echo "  setup         - Create venv and install Python dependencies (run this first)"
	@echo "  server-mods   - Download server-side mods from server-mods.yaml"
	@echo "  client-mods   - Download client-side mods from client-mods.yaml"
	@echo "  run-server    - Download server mods and run the Minecraft server"
	@echo "  clean         - Remove downloaded mods and temporary files"
	@echo "  clean-all     - Remove everything including venv"
	@echo "  help          - Show this help message"

setup:
	@echo "Creating virtual environment..."
	@python3 -m venv $(VENV)
	@echo "Installing Python dependencies..."
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -r requirements.txt
	@echo "Setup complete"

server-mods:
	@echo "Fetching server-side mods..."
	@$(PYTHON) fetch-mods.py server/server-mods.yaml $(MODS_DIR)

client-mods:
	@echo "Fetching client-side mods..."
	@$(PYTHON) fetch-mods.py client/client-mods.yaml $(CLIENT_MODS_DIR)

run-server: server-mods
	@echo "Starting Minecraft server..."
	@cd server && java -Xmx2G -jar void-mc-launcher.jar nogui

clean:
	@echo "Cleaning up mods..."
	@rm -rf $(MODS_DIR)
	@rm -rf $(CLIENT_MODS_DIR)/*.jar
	@echo "Clean complete"

clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf $(VENV)
	@echo "All clean"
