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

restart_interval = timedelta(minutes=16)
bot_startup_time = datetime.now()
next_restart_time = bot_startup_time + restart_interval

def calculate_time_until_restart():
    global next_restart_time
    now = datetime.now()
    if now >= next_restart_time:
        while now >= next_restart_time:
            next_restart_time += restart_interval
    return next_restart_time - now

async def restart_pterodactyl_server():
    api_key = os.getenv("PTERODACTYL_API_KEY")
    server_id = os.getenv("PTERODACTYL_SERVER_ID")
    panel_url = os.getenv("PTERODACTYL_PANEL_URL")

    url = f"{panel_url}/api/client/servers/{server_id}/power"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"signal": "restart"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                print("Server restart command sent successfully.")
            else:
                print(f"Failed to send restart command. HTTP status code: {response.status}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()
    send_restart_notification.start()

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

    @nextcord.ui.button(label="Postpone Long (15 mins)", style=ButtonStyle.success)
    async def postpone_long(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=15)
        await interaction.response.send_message("Server restart postponed by 15 minutes!", ephemeral=True)
        update_presence.restart()
        
@tasks.loop(seconds=60)
async def send_restart_notification():
    time_until_restart = calculate_time_until_restart()
    total_seconds = int(time_until_restart.total_seconds())
    print(f"Debug: {total_seconds} seconds until restart")

    notification_times = [15 * 60, 5 * 60, 60]
    if any(time - 60 < total_seconds <= time for time in notification_times):
        minutes = next(time for time in notification_times if time - 60 < total_seconds <= time) // 60
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        role_id = os.getenv("RESTART_NOTIFICATION_ROLE_ID")
        channel = bot.get_channel(channel_id)
        message = f"<@&{role_id}> Palworld server restarting in {minutes} minute{'s' if minutes > 1 else ''}!"
        view = RestartControlView(timeout=180)
        await channel.send(message, view=view)
        
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