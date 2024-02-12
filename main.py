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
import time
from datetime import datetime, timedelta

load_dotenv()
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
logging.basicConfig(level=logging.INFO, filename='bot_activity.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

restart_interval = timedelta(hours=6)
bot_startup_time = datetime.now()
next_restart_time = bot_startup_time + restart_interval
restart_initiated = False


### RCON Initalize, yes, I'm sending raw rcon via asyncio because RCON libraries are horrid
async def rcon_send_command(command):
    SERVER_IP = os.getenv('SERVER_IP')
    RCON_PORT = os.getenv('RCON_PORT')
    RCON_PASSWORD = os.getenv('RCON_PASSWORD')

    if not SERVER_IP or not RCON_PORT or not RCON_PASSWORD:
        return "RCON configuration is incomplete. Please check your SERVER_IP, RCON_PORT, and RCON_PASSWORD environment variables."

    try:
        RCON_PORT = int(RCON_PORT)
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
        logging.info(f"Game saved by {interaction.user.name}.")
        embed = nextcord.Embed(title="Save Successful", description="The game server state has been saved successfully.", color=0x00ff00)
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        await interaction.response.send_message(f"Failed to save game server state: {save_response}", ephemeral=True)

### This was built with my server in mind, obviously, this may not parse your name/version correctly.
@bot.slash_command(name="info", description="Displays information about the game server.")
async def info(interaction: Interaction):
    info_response = await rcon_send_command("info")

    if "RCON configuration is incomplete" in info_response or "Failed to execute RCON command" in info_response:
        await interaction.response.send_message(info_response, ephemeral=True)
        return
    try:
        version_start = info_response.find("[v") + 1
        version_end = info_response.find("]", version_start)
        version = info_response[version_start:version_end]
        name = info_response.split("]")[1].strip() if "]" in info_response else "Unknown"
        formatted_response = f"**Version** - {version}\n**Name** - {name}"
    except Exception as e:
        formatted_response = f"Failed to parse info response: {str(e)}"
    logging.info(f"Info requested by {interaction.user.name}.")
    await interaction.response.send_message(formatted_response, ephemeral=False)
    
@bot.slash_command(name="broadcast", description="Broadcasts a message on the server.")
async def broadcast(interaction: Interaction, message: str = SlashOption(description="Message to broadcast")):
    admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
    if admin_role_id not in [role.id for role in interaction.user.roles]:
        logging.info(f"Attempt to broadcast without permission issued by {interaction.user.name}.")
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    formatted_message = message.replace(" ", "_")
    
    logging.info(f"Broadcast request issued by {interaction.user.name}.")
    rcon_command = f"broadcast {formatted_message}"
    broadcast_response = await rcon_send_command(rcon_command)
    
    if "RCON configuration is incomplete" in broadcast_response or "Failed to execute RCON command" in broadcast_response:
        await interaction.response.send_message(broadcast_response, ephemeral=True)
    else:
        logging.info(f"Broadcast sent: [{message}] by {interaction.user.name}.")
        await interaction.response.send_message(f"Broadcast message sent successfully: \"{message}\"", ephemeral=True)
    
### Untested commands, proceed with caution
    
@bot.slash_command(name="shutdown", description="Initiates a server shutdown with a timer and a custom message, untested.")
async def shutdown(interaction: Interaction, seconds: int = SlashOption(description="Delay in seconds before the server shuts down"),
                   message_text: str = SlashOption(description="Custom shutdown message")):
    admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
    if admin_role_id not in [role.id for role in interaction.user.roles]:
        logging.info(f"Shutdown was attempted without permission by {interaction.user.name}.")
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    logging.info(f"Shutdown has been issued by {interaction.user.name}.")
    rcon_command = f"Shutdown {seconds} {message_text}"
    shutdown_response = await rcon_send_command(rcon_command)
    
    if "RCON configuration is incomplete" in shutdown_response or "Failed to execute RCON command" in shutdown_response:
        await interaction.response.send_message(shutdown_response, ephemeral=True)
    else:
        logging.info(f"Shutdown attempt was successful, issued by {interaction.user.name}.")
        await interaction.response.send_message(f"Shutdown command sent successfully. Server will shutdown in {seconds} seconds with message: \"{message_text}\"", ephemeral=True)
        time.sleep(5.5)
        await restart_pterodactyl_server("System")

@bot.slash_command(name="showplayers", description="Shows the current list of players on the server, optionally with Steam IDs.")
async def showplayers(interaction: Interaction, include_steamids: bool = SlashOption(description="Include Steam IDs in the output", required=False, default=False)):
    if include_steamids:
        admin_role_id = int(os.getenv("ADMIN_ROLE_ID"))
        if admin_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You do not have permission to view Steam IDs.", ephemeral=True)
            return

    show_players_response = await rcon_send_command("ShowPlayers")

    if "RCON configuration is incomplete" in show_players_response or "Failed to execute RCON command" in show_players_response:
        await interaction.response.send_message(show_players_response, ephemeral=True)
    else:
        players = [line.split(',') for line in show_players_response.strip().split('\n')]
        players = players[1:]

        messages = []
        for player in players:
            if include_steamids:
                messages.append(f"```yml\n{player[0]}\nSteamID: {player[2]}\n```")
            else:
                messages.append(f"```yml\n{player[0]}\n```")

        message = '\n'.join(messages)

        if len(message) >= 2000:
            message = "The list is too long to display here. Please narrow down your criteria."

        await interaction.response.send_message(f"### Players:\n{message}", ephemeral=True)

### Raw RCON command, uncomment if you want raw rcon access, although, not sure why you would.
#@bot.slash_command(name="rcon", description="Execute an RCON command on the server.")
#async def rcon_command(interaction: nextcord.Interaction, command: str):
    #await interaction.response.defer(ephemeral=True)
    #response = await rcon_send_command(command)
    #await interaction.followup.send(f"RCON response: ```{response}```", ephemeral=True)
    
### Fetch playercount with RCON for Discord RP

async def fetch_player_count():
    player_list_response = await rcon_send_command("ShowPlayers")
    player_list_lines = player_list_response.strip().split('\n')[1:]
    player_count = len(player_list_lines)
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
        await rcon_send_command("Save")        
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
    if not update_presence.is_running():
        update_presence.start()
    if not send_restart_notification.is_running():
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
        global last_notification_message, notification_sent, restart_initiated
        await restart_pterodactyl_server(interaction.user.name)
        logging.info(f"Restart Now button pressed by {interaction.user.name}.")
        await self.disable_buttons()
        await interaction.response.edit_message(content="🔄 Restarting the Palworld server now...", view=self)
        last_notification_message = None
        restart_initiated = True
        notification_sent = {900: False, 300: False, 120: False}
        
    @nextcord.ui.button(label="Postpone Short (15 mins)", style=ButtonStyle.blurple)
    async def postpone_short(self, button: Button, interaction: Interaction):
        global next_restart_time, notification_sent, last_notification_message
        next_restart_time += timedelta(minutes=1)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await interaction.response.edit_message(content="⏸️ Server restart postponed by 15 minutes!", view=self)
        update_presence.restart()
        await self.disable_buttons()
        last_notification_message = None
        notification_sent = {900: False, 300: False, 120: False}
        logging.info(f"Restart postponed for 15 minutes by {interaction.user.name}.")

    @nextcord.ui.button(label="Postpone Long (30 mins)", style=ButtonStyle.success)
    async def postpone_long(self, button: Button, interaction: Interaction):
        global next_restart_time, notification_sent, last_notification_message
        next_restart_time += timedelta(minutes=30)
        channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
        channel = bot.get_channel(channel_id)
        await interaction.response.edit_message(content="⏸️ Server restart postponed by 30 minutes!", view=self)
        update_presence.restart()
        await self.disable_buttons()
        last_notification_message = None
        notification_sent = {900: False, 300: False, 120: False}
        logging.info(f"Restart postponed for 30 minutes by {interaction.user.name}.")

last_notification_message = None
notification_sent = {900: False, 300: False, 120: False}

@tasks.loop(seconds=5)
async def send_restart_notification():
    global last_notification_message, restart_initiated, notification_sent
    time_until_restart = calculate_time_until_restart()
    total_seconds = int(time_until_restart.total_seconds())

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

    else:
        notification_times = {900: "15 minutes", 300: "5 minutes", 120: "2 minutes"}
        for notify_time, notify_message in notification_times.items():
            if total_seconds <= notify_time and not notification_sent[notify_time]:
                player_count = await fetch_player_count()
                logging.info(f"Player count at {notify_message} mark: {player_count}")
                minutes_str = notify_message
                logging.info("Embed updated")
                action_message = "You can postpone the restart, or, restart the server now using the buttons below."
                embed = nextcord.Embed(title="Server Restart Notification 🚨", description=f"The Palworld server is restarting in {minutes_str}!", color=0x3498db)
                embed.add_field(name="Action", value=action_message, inline=False)
                
                channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
                channel = bot.get_channel(channel_id)
                message_content = None

                if notify_time == 900 and not notification_sent[notify_time]:
                    player_count = await fetch_player_count()
                    logging.info(f"Player count at {notify_message} mark: {player_count}")
                    if player_count > 0:
                        role_id = os.getenv("RESTART_NOTIFICATION_ROLE_ID")
                        message_content = f"<@&{role_id}> " if role_id else ""
                        logging.info("Sent ping message with player count check")
                    notification_sent[notify_time] = True

                if last_notification_message and notify_time != 900:
                    await last_notification_message.edit(content=message_content, embed=embed, view=RestartControlView(timeout=180))
                else:
                    last_notification_message = await channel.send(content=message_content, embed=embed, view=RestartControlView(timeout=180))

                notification_sent[notify_time] = True

    if total_seconds <= 10 and restart_initiated:
        for key in notification_sent.keys():
            notification_sent[key] = False
        restart_initiated = False

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