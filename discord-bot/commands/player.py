import asyncio
import discord
from discord import app_commands
from utils.mc import run_mc_command
import asyncio

def setup(tree):
    @tree.command(name="player", description="Run a Carpet /player command")
    @app_commands.describe(name="Bot name", x="X Coordinate", y="Y Coordinate", z="Z Coordinate")
    async def player(interaction: discord.Interaction, name: str, x: float, y: float, z: float):
        await interaction.response.defer()
        mc_command = f"/player {name} spawn at {x} {y} {z}"
        game_mode = f"/gamemode survival {name}"

        try:
            await asyncio.to_thread(run_mc_command, mc_command)
            await asyncio.sleep(1)  # 1 second (20 ticks)
            await asyncio.to_thread(run_mc_command, game_mode)

            await interaction.followup.send(
                f"✅ Command executed:\n"
                f"```\n{mc_command}\n"
                f"{game_mode}\n```"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to run command:\n`{e}`")