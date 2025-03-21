import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path

# Path to the JSON file
SPARKLES_FILE = Path("json/sparkles.json")

def load_sparkles():
    """Load the sparkles data from the JSON file."""
    if SPARKLES_FILE.exists():
        with open(SPARKLES_FILE, "r") as f:
            return json.load(f)
    return {}

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the sparkle leaderboard for this server")
    @app_commands.describe(sparkle_type="The type of sparkle to show the leaderboard for")
    async def leaderboard(self, interaction: discord.Interaction, sparkle_type: str):
        """
        Displays the leaderboard for a specific sparkle type in the current server.
        """
        valid_types = ["epic", "rare", "regular"]
        if sparkle_type.lower() not in valid_types:
            await interaction.response.send_message(
                "Invalid sparkle type. Use `epic`, `rare`, or `regular`.",
                ephemeral=True
            )
            return

        sparkles = load_sparkles()

        # Get the server's sparkle data
        server_id = str(interaction.guild.id)
        if server_id not in sparkles or not sparkles[server_id]:
            await interaction.response.send_message(
                "No sparkles have been awarded yet in this server.",
                ephemeral=True
            )
            return

        # Get the leaderboard for the specified sparkle type
        leaderboard_data = []
        for user_id, counts in sparkles[server_id].items():
            if counts[sparkle_type] > 0:
                leaderboard_data.append((user_id, counts[sparkle_type]))

        # Sort the leaderboard by sparkle count (descending)
        leaderboard_data.sort(key=lambda x: x[1], reverse=True)

        if not leaderboard_data:
            await interaction.response.send_message(
                f"No {sparkle_type} sparkles have been awarded yet in this server.",
                ephemeral=True
            )
            return

        # Format the leaderboard
        leaderboard_text = []
        for user_id, count in leaderboard_data[:10]:  # Top 10 users
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text.append(f"{user.name}: {count}")

        await interaction.response.send_message(
            f"**{sparkle_type.capitalize()} Sparkle Leaderboard:**\n" + "\n".join(leaderboard_text),
            ephemeral=False  # Make the response visible to everyone
        )

    @leaderboard.autocomplete("sparkle_type")
    async def sparkle_type_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        valid_types = ["epic", "rare", "regular"]
        return [
            app_commands.Choice(name=sparkle_type, value=sparkle_type)
            for sparkle_type in valid_types
            if current.lower() in sparkle_type.lower()
        ]

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))