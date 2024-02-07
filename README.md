# Simple Palworld Restarter-thingy!

## How to use?

Windows:

- Install Python - https://www.python.org/downloads/windows/
- Clone/download this repo.
- Extract to folder of your desire, move to dependency installation
- Move to dependency Installation

Linux:


TBA

## Dependency Installation

Windows:

- Open shell in directory you extracted the files in.
- Run `pip install nextcord aiohttp python-dotenv`
- Move to starting the bot

## Configure & start the bot

Windows:

- Open the `.env example` file and add your token, and other details, along with renaming the file to just `.env`
- Use the shell you had opened prior to run the bot with `pythn main.py` the comamnd may differ depending on your verison of python, eg `python3.12.exe main.py`
- Done!

Make a .env, populate it with the following, you will in your own details.

```
DISCORD_TOKEN= # Your Discord bot token
PTERODACTYL_API_KEY= # Your Pterodactyl account API key (NOT APPLICATION API)
PTERODACTYL_PANEL_URL= # Your Pterodactyl's public URL (for API)
PTERODACTYL_SERVER_ID= # Your Pterodactyl server ID, grab from admin area
NOTIFICATION_CHANNEL_ID= # Channel you want to notify users in about the restart
RESTART_NOTIFICATION_ROLE_ID= # Role to ping for the notification
```
