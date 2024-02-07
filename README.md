# Simple Palworld Restarter-thingy!

## How to use?

Windows:

`.\venv\Scripts\activate`

Linux:

TBA

## Install Nextcord, aiohttp, and python-dotenv

`pip install nextcord aiohttp python-dotenv`

Make a .env, populate it with the following, you will in your own details.

```
DISCORD_TOKEN= # Your Discord bot token
PTERODACTYL_API_KEY= # Your Pterodactyl account API key (NOT APPLICATION API)
PTERODACTYL_PANEL_URL= # Your Pterodactyl's public URL (for API)
PTERODACTYL_SERVER_ID= # Your Pterodactyl server ID, grab from admin area
NOTIFICATION_CHANNEL_ID= # Channel you want to notify users in about the restart
RESTART_NOTIFICATION_ROLE_ID= # Role to ping for the notification
```
