import discord
from dotenv import load_dotenv
from os import environ
from discord.ext import tasks
from datetime import datetime
import pytz  # For timezone handling

class DailyReminder:
    def __init__(self, bot):
        self.bot = bot
        self.girlfriend_id = environ.get("GIRLFRIEND_ID")
        self.london_tz = pytz.timezone("Europe/London")
        self.daily_reminder.start()

    @tasks.loop(minutes=1)  # Check every minute
    async def daily_reminder(self):
        now = datetime.now(self.london_tz)
        if now.hour == 12  and now.minute == 0:
            try:
                girlfriend = await self.bot.fetch_user(self.girlfriend_id)
                await girlfriend.send("Daily reminder that Lilac loves you <3", silent=True)
                print(f"Sent daily reminder to {girlfriend.name} at {now}.")
            except discord.Forbidden:
                print("Could not send DM: User has DMs disabled or blocked the bot.")
            except discord.HTTPException as e:
                print(f"Failed to send DM: {e}")

    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()