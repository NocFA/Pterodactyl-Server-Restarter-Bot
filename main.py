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
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
logging.basicConfig(level=logging.INFO, filename='bot_activity.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

restart_interval = timedelta(hours=10)
bot_startup_time = datetime.now()
next_restart_time = bot_startup_time + restart_interval
restart_initiated = False

def calculate_time_until_restart():
    global next_restart_time
    now = datetime.now()
    if now >= next_restart_time:
        while now >= next_restart_time:
            next_restart_time += restart_interval
    return next_restart_time - now

async def restart_pterodactyl_server(initiated_by: str) -> bool:
    logging.info(f"Attempting to restart server initiated by {initiated_by}.")
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
                response_text = await response.text()
                if response.status in [204]:
                    logging.info(f"Server restart command sent successfully by {initiated_by}.")
                    print("Server restart command sent successfully.")
                    now = datetime.now()
                    next_restart_time = now + restart_interval
                    channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"The server has now been restarted, the next restart schedule is reset to {next_restart_time.strftime('%Y-%m-%d %H:%M:%S')}.")
                        return True
                    else:
                        logging.warning(f"Failed to send restart command by {initiated_by}. HTTP status code: {response.status}, Response: {response_text}")
                        print(f"Failed to send restart command. HTTP status code: {response.status}, Response: {response_text}")
                        return False
    except Exception as e:
        logging.error(f"An error occurred during restart attempt by {initiated_by}: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    update_presence.start()
    send_restart_notification.start()

class RestartControlView(View):
    async def disable_buttons(self):
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True

    async def disable_buttons(self):
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True
        self.stop()     

    @nextcord.ui.button(label="Restart Now", style=ButtonStyle.red)
    async def restart_now(self, button: Button, interaction: Interaction):
        global last_notification_message
        await restart_pterodactyl_server(interaction.user.name)
        logging.info(f"Restart Now button pressed by {interaction.user.name}.")
        await self.disable_buttons()
        await interaction.response.edit_message(content="🔄 Restarting the Palworld server now...", view=self)
        last_notification_message = None
        
    @nextcord.ui.button(label="Postpone Short (5 mins)", style=ButtonStyle.blurple)
    async def postpone_short(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=5)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await interaction.response.edit_message(content="⏸️ Server restart postponed by 5 minutes!", view=self)
        update_presence.restart()

    @nextcord.ui.button(label="Postpone Long (15 mins)", style=ButtonStyle.success)
    async def postpone_long(self, button: Button, interaction: Interaction):
        global next_restart_time
        next_restart_time += timedelta(minutes=15)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await interaction.response.edit_message(content="⏸️ Server restart postponed by 15 minutes!", view=self)
        update_presence.restart()

last_notification_message = None

@tasks.loop(seconds=5)
async def send_restart_notification():
    global last_notification_message, restart_initiated
    time_until_restart = calculate_time_until_restart()
    total_seconds = int(time_until_restart.total_seconds())
    fifteen_minute_notification_sent = False
    
    if total_seconds <= 10 and not restart_initiated:
        logging.info("Less than 10 seconds remaining, attempting automatic restart.")
        result = await restart_pterodactyl_server("System")
        restart_initiated = True
        if result:
            logging.info("Restart attempt made and confirmed.")
            if last_notification_message:
                view = RestartControlView(timeout=None)
                await view.disable_buttons()
                await last_notification_message.edit(content="🔄 Palworld server is restarting now...", embed=None, view=view)
                last_notification_message = None
        else:
            logging.error("Restart attempt failed.")

    elif any(time - 60 < total_seconds <= time for time in [15 * 60, 5 * 60, 2 * 60]):
        is_fifteen_minute_mark = total_seconds <= 15 * 60 and total_seconds > 14 * 55 and not fifteen_minute_notification_sent
        role_id = os.getenv("RESTART_NOTIFICATION_ROLE_ID")
        role_mention = f"<@&{role_id}> " if is_fifteen_minute_mark else ""
        if is_fifteen_minute_mark:
            fifteen_minute_notification_sent = True
            
        minutes = next((time for time in [15 * 60, 2 * 60, 2 * 60] if time - 60 < total_seconds <= time), None) // 60 if total_seconds > 60 else 0
        minutes_str = "minute" if minutes == 1 else "minutes"
        action_message = "You can postpone the restart, or, restart the server now using the buttons below."
        embed = nextcord.Embed(title="Server Restart Notification 🚨", description=f"The Palworld server is restarting in {minutes} {minutes_str}!", color=0x3498db)
        embed.add_field(name="Action", value=action_message, inline=False)
        
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        
        message_content = role_mention if role_mention else None

        if last_notification_message:
            await last_notification_message.edit(content=message_content, embed=embed, view=RestartControlView(timeout=180))
        else:
            last_notification_message = await channel.send(content=message_content, embed=embed, view=RestartControlView(timeout=180))

@tasks.loop(seconds=8)
async def update_presence():
    time_until_restart = calculate_time_until_restart()
    hours, remainder = divmod(int(time_until_restart.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}h {minutes}m {seconds}s until restart"
    await bot.change_presence(activity=nextcord.Game(name=time_str))

@bot.slash_command(description="Postpone the server restart by a certain duration, requires permission.")
async def postpone(interaction: Interaction, extended: bool = SlashOption(description="Extend the restart 5 or 15 minutes (true for 15)", required=False, default=False)):
    global next_restart_time
    if extended:
        next_restart_time += timedelta(minutes=15)
        await interaction.response.send_message("Server restart postponed by 15 minutes!", ephemeral=True)
    else:
        next_restart_time += timedelta(minutes=5)
        await interaction.response.send_message("Server restart postponed by 5 minutes!", ephemeral=True)
    update_presence.restart()
    extend_duration = 15 if extended else 5
    logging.info(f"Postpone command used by {interaction.user.name}, extending by {extend_duration} minutes.")

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))