# Simple Palworld Restarter-thingy!

## How to use?

Windows:

- Install Python - https://www.python.org/downloads/windows/
- Clone/download this repo.
- Extract files as needed to the folder you desire.
- Move to dependency Installation

Linux:

- Install python, this will vary based on what distro you have, please check python docks - https://www.python.org/downloads/
- Clone/download this repo.
- Extract files as needed to the folder you desire.
- Move to dependency Installation

## Dependency Installation

Windows:

- Open shell in directory you extracted the files in.
- (Optional) run from virtual env `python -m venv venv` & activate with `.\venv\Scripts\activate`
- Run `pip install -r requirements.txt` to install all dependencies for the bot
- Move to starting the bot

Linux:

- pip install -r requirements.txt

## Configure & start the bot

Windows:

- Open the `.env example` file and add your token, and other details, along with renaming the file to just `.env`
- Use the shell you had opened prior to run the bot with `pythn main.py` the comamnd may differ depending on your verison of python, eg `python3.12.exe main.py`
(If you used the venv, it'll always be `python` for the launch executable, so, use `python main.py`)
- Done!

Linux:

### The PM2 way

- pm2 start main.py --interpreter=python3

### The not PM2 way

- In the directory, run `python3 main.py` (your version/executable may differ)

Make a .env, populate it with the following, you will in your own details.

```
DISCORD_TOKEN= # Your Discord bot token
PTERODACTYL_API_KEY= # Your Pterodactyl account API key (NOT APPLICATION API)
PTERODACTYL_PANEL_URL= # Your Pterodactyl's public URL (for API)
PTERODACTYL_SERVER_ID= # Your Pterodactyl server ID, grab from admin area
NOTIFICATION_CHANNEL_ID= # Channel you want to notify users in about the restart
RESTART_NOTIFICATION_ROLE_ID= # Role to ping for the notification
```
