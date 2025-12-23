from mcstatus import JavaServer
from utils.thread_safe_mcrcon import ThreadSafeMCRcon
from config import SERVER_IP, SERVER_PORT, RCON_HOST, RCON_PASSWORD

# Keeps Discord code and Minecraft code separate
def get_server_status():
    server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
    return server.status()

def run_mc_command(command):
    with ThreadSafeMCRcon(RCON_HOST, RCON_PASSWORD, port=25575) as mcr:
        return mcr.command(command)
