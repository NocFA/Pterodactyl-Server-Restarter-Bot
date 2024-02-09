import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption, ButtonStyle
from nextcord.ui import Button, View
import os
import logging
from dotenv import load_dotenv
import aiohttp
import asyncio
import socket
import struct
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


### RCON Initalize, yes, I'm sending raw rcon via asyncio because RCON libraries are horrid
async def rcon_send_command(command):
    SERVER_IP = os.getenv('SERVER_IP')
    RCON_PORT = os.getenv('RCON_PORT')
    RCON_PASSWORD = os.getenv('RCON_PASSWORD')

    # Check for missing RCON configuration
    if not SERVER_IP or not RCON_PORT or not RCON_PASSWORD:
        return "RCON configuration is incomplete. Please check your SERVER_IP, RCON_PORT, and RCON_PASSWORD environment variables."

    try:
        RCON_PORT = int(RCON_PORT)  # Ensure RCON_PORT is an integer
    except ValueError:
        return "Invalid RCON_PORT. Please ensure it's a valid integer."

    try:
        reader, writer = await asyncio.open_connection(SERVER_IP, RCON_PORT)
        packet_id = 1
        packet_type = 3
        auth_packet = struct.pack('<3i', 10 + len(RCON_PASSWORD), packet_id, packet_type) + RCON_PASSWORD.encode('ascii') + b'\x00\x00'
        writer.write(auth_packet)
        await writer.drain()

        auth_response = await reader.read(4096)
        _, response_id, _ = struct.unpack('<3i', auth_response[:12])

        if response_id == -1:
            return "Authentication failed with the RCON server."

        packet_type = 2
        command_packet = struct.pack('<3i', 10 + len(command), packet_id, packet_type) + command.encode('ascii') + b'\x00\x00'
        writer.write(command_packet)
        await writer.drain()

        response = await reader.read(4096)
        response_text = response[12:-2].decode('ascii')

        writer.close()
        await writer.wait_closed()
        return response_text
    except Exception as e:
        return f"Failed to execute RCON command due to an error: {e}"

@bot.slash_command(name="save", description="Saves the current state of the game server.")
async def save(interaction: Interaction):
    save_response = await rcon_send_command("Save")
    if "Complete Save" in save_response:
        embed = nextcord.Embed(title="Save Successful", description="The game server state has been saved successfully.", color=0x00ff00)  # Green color
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"Failed to save game server state: {save_response}", ephemeral=True)

### This was built with my server in mind, obviously, this may not parse your name/version correctly.
@bot.slash_command(name="info", description="Displays information about the game server.")
async def info(interaction: Interaction):
    info_response = await rcon_send_command("info")

    # Check if the response indicates a configuration or connection error
    if "RCON configuration is incomplete" in info_response or "Failed to execute RCON command" in info_response:
        # Send back the error message directly without trying to parse
        await interaction.response.send_message(info_response, ephemeral=True)
        return

    # Proceed with parsing if no configuration or connection error
    try:
        version_start = info_response.find("[v") + 1
        version_end = info_response.find("]", version_start)
        version = info_response[version_start:version_end]
        name = info_response.split("]")[1].strip() if "]" in info_response else "Unknown"
        formatted_response = f"**Version** - {version}\n**Name** - {name}"
    except Exception as e:
        formatted_response = f"Failed to parse info response: {str(e)}"
    
    await interaction.response.send_message(formatted_response, ephemeral=True)
    
### Untested commands, proceed with caution
    
@bot.slash_command(name="shutdown", description="Initiates a server shutdown with a timer and a custom message, untested.")
async def shutdown(interaction: Interaction, seconds: int = SlashOption(description="Delay in seconds before the server shuts down"),
                   message_text: str = SlashOption(description="Custom shutdown message")):
    admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
    if admin_role_id not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    rcon_command = f"Shutdown {seconds} {message_text}"
    shutdown_response = await rcon_send_command(rcon_command)
    
    if "RCON configuration is incomplete" in shutdown_response or "Failed to execute RCON command" in shutdown_response:
        await interaction.response.send_message(shutdown_response, ephemeral=True)
    else:
        await interaction.response.send_message(f"Shutdown command sent successfully. Server will shutdown in {seconds} seconds with message: \"{message_text}\"", ephemeral=True)
        
@bot.slash_command(name="broadcast", description="Broadcasts a message on the server.")
async def broadcast(interaction: Interaction, message: str = SlashOption(description="Message to broadcast")):
    admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
    if admin_role_id not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    # Replace spaces with underscores in the message (otherwise it breaks)
    formatted_message = message.replace(" ", "_")
    
    rcon_command = f"broadcast {formatted_message}"
    broadcast_response = await rcon_send_command(rcon_command)
    
    if "RCON configuration is incomplete" in broadcast_response or "Failed to execute RCON command" in broadcast_response:
        await interaction.response.send_message(broadcast_response, ephemeral=True)
    else:
        await interaction.response.send_message(f"Broadcast message sent successfully: \"{message}\"", ephemeral=True)


### Raw RCON command, uncomment if you want raw rcon access, although, not sure why you would.
#@bot.slash_command(name="rcon", description="Execute an RCON command on the server.")
#async def rcon_command(interaction: nextcord.Interaction, command: str):
    #await interaction.response.defer(ephemeral=True)
    #response = await rcon_send_command(command)
    #await interaction.followup.send(f"RCON response: ```{response}```", ephemeral=True)
    
### Fetch playercount with RCON for Discord RP

async def fetch_player_count():
    player_list_response = await rcon_send_command("ShowPlayers")
    # Split response into lines and remove the header row
    player_list_lines = player_list_response.strip().split('\n')[1:]  # Skip the header
    player_count = len(player_list_lines)  # Count the remaining lines for player count
    return player_count

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
    player_count = await fetch_player_count()
    status_message = f"{player_count}/32 players | {hours}h {minutes}m {seconds}s until restart"
    await bot.change_presence(activity=nextcord.Game(name=status_message))

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