import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, ButtonStyle
from nextcord.ui import Button, View
import os
from dotenv import load_dotenv
import aiohttp
from datetime import datetime, timedelta

load_dotenv()
bot = commands.Bot(command_prefix="/", intents=nextcord.Intents.default())

restart_interval = timedelta(hours=12)
bot_startup_time = datetime.now()
next_restart_time = bot_startup_time + restart_interval

def calculate_time_until_restart():
    """Calculate the time remaining until the next restart."""
    global next_restart_time
    now = datetime.now()
    if now >= next_restart_time:
        while now >= next_restart_time:
            next_restart_time += restart_interval
    return next_restart_time - now

@tasks.loop(minutes=1)
async def update_presence():
    """Update the bot's rich presence with the time until restart."""
    time_until_restart = calculate_time_until_restart()
    hours, remainder = divmod(int(time_until_restart.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}h {minutes}m until restart"
    await bot.change_presence(activity=nextcord.Game(name=time_str))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()

@bot.slash_command(description="Postpone the server restart by 30 minutes, requires permission.")
async def postpone(interaction: Interaction, extended: bool = SlashOption(description="Extend the postpone to 30 minutes", required=False, default=False)):
    await interaction.response.send_message("Server restart postponed!", ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))