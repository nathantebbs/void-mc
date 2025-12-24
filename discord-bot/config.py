from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("MINECRAFT_PORT")
NOTIFICATIONS_CHANNEL_ID = int(os.getenv("NOTIFICATIONS_CHANNEL_ID", "0"))
SERVER_LOG_PATH = os.getenv("SERVER_LOG_PATH", "../server/logs/latest.log")

RCON_HOST = SERVER_IP
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
