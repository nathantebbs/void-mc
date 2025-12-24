from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("MINECRAFT_PORT")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID", "0"))

RCON_HOST = SERVER_IP
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
