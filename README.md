# Simple Pterodactyl Game Restart Bot

I set this up for me and my friend's palworld server due to the horrid memory leak.
Do not expect support/updates, provided as-is.
There's a few references to `Palworld` within the code, you can of course modify & change this quite easily.
I would say this is a good foundational bot if you want to add a bunch of features for some kind of pterodactyl interactable bot.

# What do it do?
Very simple bot that has a set interval `restart_interval` which by default is 12 hours.
It counts down from this time and displays such a countdown in its rich presence status, updated every 5 seconds, any lower and you risk discord API hitching.

Once it reaches a predefined amount of time (15 minutes, 5 minutes & 60 seconds) it will send a Discord embed notifying a specified role (.env) that the server is restarting in `x`
The user then has 3 buttons, `restart now` which immediately restarts the server ID defined in the `.env` `Postpone Short (5 mins)` & `Postpone Long (15 mins)`
Upon a user selecting one of these options, it's logged to a file called `bot_activity.log` and prints to the chat what's been selected.

If left untouched, it will just restart the server.

![Sample Screenshot](https://noc.wf/PPpCpoxkh0-XjkUCVdTz8.png?no_redirect=true)

Has the ability of using slash commands to run `/postpone` early to extend it by 5 or 15 minutes, just in case you have 30 mnutes remaining and want a bit more time, ahead of time.

Now, with the latest 0.2, has the ability to use/issue RCON commands to a Palworld server, such as shutdown with a timer, show players, see server details, etc.
![All Commands Image](https://noc.wf/3C6AXsAMzW-rJkwCrXi8b.png?no_redirect=true)

# How to use?

These instructions aren't final, nor will work on everyone's system, things will differ.
This is what works on mine, so, please take it with a pinch of salt.

In most cases, you're best to run any python bot with `venv` for a virtual environment, especially if you've used python elsewhere.

# Commands
- /broadcast [Message] # This broadcasts a message to the whole server. (admin-only)
- /info # This gets the palworld server version & server name
- /save # Saves the current game state, this is also issued on shutdowns.
- /postpone [optional: extended] # this by default postpones the restart by 15 minutes, if extended is choosen, it'll be 30 minutes.
- /showplayers [optiona: include_steamids:True/False] # This gets current list of players on the server, optionally can include their steam UUID for easy kicking, which you can implement, I haven't.
- /shutdown [seconds] [message_text:] # Shuts down the server peacefully, requires time until shutdown & message.

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
DISCORD_TOKEN="" # Your Discord bot token
PTERODACTYL_API_KEY="" # Your Pterodactyl account API key (NOT APPLICATION API)
PTERODACTYL_PANEL_URL="" # Your Pterodactyl's public URL (for API)
PTERODACTYL_SERVER_ID="" # Your Pterodactyl server ID, grab from admin area
NOTIFICATION_CHANNEL_ID="" # Channel you want to notify users in about the restart
RESTART_NOTIFICATION_ROLE_ID="" # Role to ping for the notification
ADMIN_ROLE_ID="" (Optional) # Role for admin RCON commands (broadcast, restart, etc)
SERVER_IP="" # (Optional) Your server's IP address.
RCON_PORT="" # (Optional) Your RCON port, this is separate from main port, default is 25575.
RCON_PASSWORD="" # (Optional) If using RCON, set the server admin password here, yes, you have to have one/.
RESTART_INTERVAL="" # This is what actually defines how often the server should auto-restart, use format of `hours=6`, `minutes=15` etc.
```
