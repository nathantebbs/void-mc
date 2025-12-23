from client import Void
from config import DISCORD_TOKEN
from commands import status, player, ping

client = Void()

status.setup(client.tree)
player.setup(client.tree)
ping.setup(client.tree, client)

client.run(DISCORD_TOKEN)
