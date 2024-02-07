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
class RestartControlView(View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)

    @nextcord.ui.button(label="Restart Now", style=ButtonStyle.red)
    async def restart_now(self, button: Button, interaction: Interaction):
        # Placeholder for restart functionality
        await interaction.response.send_message("Restarting now...", ephemeral=False)

    @nextcord.ui.button(label="Postpone Short (5 mins)", style=ButtonStyle.blurple)
    async def postpone_short(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=5)
        await interaction.response.send_message("Server restart postponed by 5 minutes!", ephemeral=True)
        update_presence.restart()

    @nextcord.ui.button(label="Postpone Long (15 mins)", style=ButtonStyle.grey)
    async def postpone_long(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=15)
        await interaction.response.send_message("Server restart postponed by 15 minutes!", ephemeral=True)
        update_presence.restart()
        
@tasks.loop(seconds=60)
async def send_restart_notification():
    time_until_restart = calculate_time_until_restart()
    total_seconds = int(time_until_restart.total_seconds())
    
    notification_times = [15 * 60, 5 * 60, 60]
    if total_seconds in notification_times:
        minutes = total_seconds // 60
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        role_id = os.getenv("RESTART_NOTIFICATION_ROLE_ID")
        channel = bot.get_channel(channel_id)
        message = f"<@&{role_id}> Palworld server restarting in {minutes} minute{'s' if minutes > 1 else ''}!"
        view = RestartControlView(timeout=180)
        await channel.send(message, view=view)
        
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()
    send_restart_notification.start()
        
def calculate_time_until_restart():
    global next_restart_time
    now = datetime.now()
    if now >= next_restart_time:
        while now >= next_restart_time:
            next_restart_time += restart_interval
    return next_restart_time - now

@tasks.loop(seconds=10)
async def update_presence():
    time_until_restart = calculate_time_until_restart()
    hours, remainder = divmod(int(time_until_restart.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}h {minutes}m {seconds}s until restart"
    await bot.change_presence(activity=nextcord.Game(name=time_str))


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()

@bot.slash_command(description="Postpone the server restart by a certain duration, requires permission.")
async def postpone(interaction: Interaction, extended: bool = SlashOption(description="Extend the postpone to 30 minutes", required=False, default=False)):
    global next_restart_time
    if extended:
        next_restart_time += timedelta(minutes=15)
        await interaction.response.send_message("Server restart postponed by 15 minutes!", ephemeral=True)
    else:
        next_restart_time += timedelta(minutes=5)
        await interaction.response.send_message("Server restart postponed by 5 minutes!", ephemeral=True)
    update_presence.restart()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))