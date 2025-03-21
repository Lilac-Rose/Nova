import discord
from discord.ext import commands
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MY_USER_ID = 252130669919076352

class SendMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def send_message(self, ctx, server_id: int, channel_id: int, message_id: str, *, message_content: str):
        # Log command usage
        logger.info(f"Command 'send_message' invoked by {ctx.author} (ID: {ctx.author.id}) with server_id={server_id}, channel_id={channel_id}, message_content='{message_content}'")

        if ctx.author.id != MY_USER_ID:
            feedback = "You do not have permission to use this command."
            await ctx.send(feedback)
            logger.warning(f"Permission denied for {ctx.author} (ID: {ctx.author.id})")
            return

        # Find the server
        server = self.bot.get_guild(server_id)
        if server is None:
            feedback = "Server not found."
            await ctx.send(feedback)
            logger.error(f"Server not found: server_id={server_id}")
            return

        # Find the channel
        channel = server.get_channel(channel_id)
        if channel is None:
            feedback = "Channel not found."
            await ctx.send(feedback)
            logger.error(f"Channel not found: channel_id={channel_id} in server_id={server_id}")
            return

        try:
            if message_id != "none": 
                message = await channel.fetch_message(message_id)
                await message.reply(message_content)
                feedback = f"Message sent to {server.name} in channel {channel.name}."
                await ctx.send(feedback)
            else:
                await channel.send(message_content)
                feedback = f"Message sent to {server.name} in channel {channel.name}."
                await ctx.send(feedback)
                logger.info(f"Message sent to server_id={server_id}, channel_id={channel_id}, content='{message_content}'")
        except discord.Forbidden:
            feedback = "I do not have permission to send messages in that channel."
            await ctx.send(feedback)
            logger.error(f"Permission denied for sending message in channel_id={channel_id} in server_id={server_id}")
        except discord.HTTPException as e:
            feedback = f"Failed to send message: {e}"
            await ctx.send(feedback)
            logger.error(f"Failed to send message: {e}")

async def setup(bot):
    await bot.add_cog(SendMessage(bot))