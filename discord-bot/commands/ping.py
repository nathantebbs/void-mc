import discord

def setup(tree, client):
    @tree.command(name="ping", description="Check bot's latency")
    async def ping(interaction: discord.Interaction):
        # Since ping is instant (< 3 sec.), we won’t defer — just respond normally
        latency = round(client.latency * 1000)  # Convert to ms
        await interaction.response.send_message(f"🏓 Pongg! `{latency}ms`")