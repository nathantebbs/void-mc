import discord
from discord import app_commands
from utils.status_monitor import ServerStatusMonitor
from config import STATUS_CHANNEL_ID

class Void(discord.Client):
    """
    The super() call will run the original discord.Client setup code,
    and give it the intents it needs. This bot will really only be for slash
    commands, so default() is fine. Removing this line won't allow the bot to
    connect, and will also break other shit

    self.tree is specifically for slash commands. Think of it as a place where
    all slash commands live (for this specific bot, obviously)
    """
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.status_monitor = ServerStatusMonitor(self, STATUS_CHANNEL_ID)

    # Setup code after the client logs in but before it connects to the Discord
    # gateway and starts dispatching events
    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")

        except discord.HTTPException as e:
            print(f"Failed to sync commands: {e}")

        print("Bot logged in and setup hook is running!")
        self.status_monitor.start()
        print("Server status monitoring started")

