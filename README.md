# Simple Pterodactyl Game Restart Bot

I set this up for me and my friend's palworld server due to the horrid memory leak.
Do not expect support/updates, provided as-is.

# How to use?

These instructions aren't final, nor will work on everyone's system, things will differ.
This is what works on mine, so, please take it with a pinch of salt.

In most cases, you're best to run any python bot with `venv` for a virtual environment, especially if you've used python elsewhere.

## Requirments
- Requires Python 3.9 or above.
- Requires Pterodactyl panel with API access

## Windows:

- Install Python - https://www.python.org/downloads/windows/
- Clone/download this repo.
- Extract files as needed to the folder you desire.
- Move to dependency Installation

## Linux:

- Install python, this will vary based on what distro you have, please check python docks - https://www.python.org/downloads/
- Clone/download this repo.
- Extract files as needed to the folder you desire.
- Move to dependency Installation

# Dependency Installation

## Windows:

- Open shell in directory you extracted the files in.
- (Optional) run from virtual env `python -m venv venv` & activate with `.\venv\Scripts\activate`
- Run `pip install -r requirements.txt` to install all dependencies for the bot
- Move to starting the bot

## Linux:

- Open the `.env example` file and add your token, and other details, along with renaming the file to just `.env`
- pip install -r requirements.txt
- (Optional) Do this in venv with 

# Configure & start the bot

## Windows:

- Open the `.env example` file and add your token, and other details, along with renaming the file to just `.env`
- Use the shell you had opened prior to run the bot with `pythn main.py` the comamnd may differ depending on your verison of python, eg `python3.12.exe main.py`
(If you used the venv, it'll always be `python` for the launch executable, so, use `python main.py`)
- Done!

## Linux:

### The PM2 way

- pm2 start main.py --interpreter=python3 (Your may need to hardcode the correct path depending on what python your pip installed to, use venv to make life easier)

### The not PM2 way

- (Optional) Run in a screen `dnf/apt install screen` to ensure it runs without you needing to be logged in.
- In the directory, run `python3 main.py` (your version/executable may differ)
Do note, with the latter option, if you exit the shell, the bot will also exit, you need to use PM2/screen/tmux to keep a shell instance alive, or, run it in the background or as a service.

## Will this work on x or y host?

- Likely, yes, but, support won't be provided for it, the bot is as-is.

## Default .env requirements:

```
DISCORD_TOKEN= # Your Discord bot token
PTERODACTYL_API_KEY= # Your Pterodactyl account API key (NOT APPLICATION API)
PTERODACTYL_PANEL_URL= # Your Pterodactyl's public URL (for API)
PTERODACTYL_SERVER_ID= # Your Pterodactyl server ID, grab from admin area
NOTIFICATION_CHANNEL_ID= # Channel you want to notify users in about the restart
RESTART_NOTIFICATION_ROLE_ID= # Role to ping for the notification
```