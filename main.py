import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, ButtonStyle
from nextcord.ui import Button, View
import os
import logging
from dotenv import load_dotenv
import aiohttp
from datetime import datetime, timedelta

load_dotenv()
bot = commands.Bot(command_prefix="/", intents=nextcord.Intents.default())

restart_interval = timedelta(minutes=15)
bot_startup_time = datetime.now()
next_restart_time = bot_startup_time + restart_interval

def calculate_time_until_restart():
    global next_restart_time
    now = datetime.now()
    if now >= next_restart_time:
        while now >= next_restart_time:
            next_restart_time += restart_interval
    return next_restart_time - now

async def restart_pterodactyl_server(initiated_by: str):
    global next_restart_time
    api_key = os.getenv("PTERODACTYL_API_KEY")
    server_id = os.getenv("PTERODACTYL_SERVER_ID")
    panel_url = os.getenv("PTERODACTYL_PANEL_URL").rstrip('/')

    url = f"{panel_url}/api/client/servers/{server_id}/power"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"signal": "restart"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status in [204]:
                    logging.info(f"Server restart command sent successfully by {initiated_by}.")
                    print("Server restart command sent successfully.")
                    now = datetime.now()
                    next_restart_time = now + restart_interval
                    channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"The server has now been restarted, the next restart schedule is reset to {next_restart_time.strftime('%Y-%m-%d %H:%M:%S')}.")
                else:
                    logging.warning(f"Failed to send restart command by {initiated_by}. HTTP status code: {response.status}, Response: {response_text}")
                    response_text = await response.text()
                    print(f"Failed to send restart command. HTTP status code: {response.status}, Response: {response_text}")
    except Exception as e:
        print(f"An error occurred: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()
    send_restart_notification.start()

class RestartControlView(View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)

    async def disable_buttons(self):
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True
        self.stop()     

    @nextcord.ui.button(label="Restart Now", style=ButtonStyle.red)
    async def restart_now(self, button: Button, interaction: Interaction):
        await restart_pterodactyl_server(interaction.user.name)
        logging.info(f"Restart Now button pressed by {interaction.user.name}.")
        await self.disable_buttons()
        await interaction.response.edit_message(content="Restarting the Palworld server now...", view=self)
        
    @nextcord.ui.button(label="Postpone Short (5 mins)", style=ButtonStyle.blurple)
    async def postpone_short(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=5)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await channel.send("Server restart postponed by 5 minutes!")
        await interaction.response.edit_message(content="Server restart postponed by 5 minutes!", view=self)
        update_presence.restart()

    @nextcord.ui.button(label="Postpone Long (15 mins)", style=ButtonStyle.success)
    async def postpone_long(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=15)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await channel.send("Server restart postponed by 15 minutes!")
        await interaction.response.edit_message(content="Server restart postponed by 15 minutes!", view=self)
        update_presence.restart()
        
@tasks.loop(seconds=60)
async def send_restart_notification():
    time_until_restart = calculate_time_until_restart()
    total_seconds = int(time_until_restart.total_seconds())

    notification_times = [15 * 60, 5 * 60, 60]
    if any(time - 60 < total_seconds <= time for time in notification_times):
        minutes = next(time for time in notification_times if time - 60 < total_seconds <= time) // 60
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        
        embed = nextcord.Embed(title="🚨 Server Restart Notification 🚨", description=f"The Palworld server is restarting in {minutes} minutes!", color=0x3498db)
        embed.add_field(name="Action", value="You can postpone the restart using the buttons below.", inline=False)
        await channel.send(embed=embed, view=RestartControlView(timeout=180))
    elif total_seconds <= 0:
        await restart_pterodactyl_server()
        await channel.send("🔄 Palworld server is restarting now...")

@tasks.loop(seconds=10)
async def update_presence():
    time_until_restart = calculate_time_until_restart()
    hours, remainder = divmod(int(time_until_restart.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}h {minutes}m {seconds}s until restart"
    await bot.change_presence(activity=nextcord.Game(name=time_str))

@bot.slash_command(description="Postpone the server restart by a certain duration, requires permission.")
async def postpone(interaction: Interaction, extended: bool = SlashOption(description="Extend the postpone to 15 minutes", required=False, default=False)):
    global next_restart_time
    if extended:
        next_restart_time += timedelta(minutes=15)
        await interaction.response.send_message("Server restart postponed by 30 minutes!", ephemeral=True)
    else:
        next_restart_time += timedelta(minutes=5)
        await interaction.response.send_message("Server restart postponed by 15 minutes!", ephemeral=True)
    update_presence.restart()
    extend_duration = 15 if extended else 5
    logging.info(f"Postpone command used by {interaction.user.name}, extending by {extend_duration} minutes.")

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))