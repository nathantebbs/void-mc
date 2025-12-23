import discord
from itertools import count
import re
from utils.mc import get_server_status

def setup(tree):
    @tree.command(name="status", description="Check void-mc server status")
    async def status(interaction: discord.Interaction):
        # Discord expects a response within 3 sec, but our ping (unrelated to
        # the ping command) might take longer. Therefore, defer() tells Discord
        # to chill tf out — we got this.
        await interaction.response.defer()

        try:
            server_status = get_server_status()
            player_list = server_status.players.sample

            # Replaces each "Anonymous Player" in text with a sequentially
            # numbered bot ([Bot 1], [Bot 2], etc.) while leaving other names
            # unchanged. Uses itertools.count() to keep track of bot number.
            bot_counter = count(1)
            active_players_string = ""

            if player_list:
                active_players_string = re.sub(
                    r'\bAnonymous Player\b',
                    lambda _: f"[Bot {next(bot_counter)}]",
                    ", ".join(p.name for p in player_list)
                )

            msg = (
                f"🟢**Server is online!**\n"
                f"Players: {server_status.players.online}/{server_status.players.max}"
            )

            if active_players_string:
                msg += f"\nOnline: {active_players_string}"

            await interaction.followup.send(msg)

        except Exception:
            await interaction.followup.send(
                "🔴**Server is offline or unreachable.**"
            )