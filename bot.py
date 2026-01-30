import discord
from discord.ext import commands, tasks
import json
from datetime import time
import pytz
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import time as _time

# =============================
# Render keep-alive web server
# =============================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# =============================
# Discord bot setup
# =============================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =============================
# Data storage
# =============================
DATA_FILE = "reactions.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

reaction_counts = load_data()

# =============================
# Reaction tracking (RELIABLE)
# =============================
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    uid = str(payload.user_id)
    reaction_counts[uid] = reaction_counts.get(uid, 0) + 1
    save_data(reaction_counts)

# =============================
# Daily leaderboard task
# =============================
@tasks.loop(time=time(23, 59, tzinfo=pytz.timezone("Asia/Kolkata")))
async def daily_leaderboard():
    if not reaction_counts:
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    sorted_users = sorted(
        reaction_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    message = "🏆 **Daily Reaction Leaderboard**\n\n"

    for i, (uid, count) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(uid))
            message += f"**{i}. {user.name}** — {count} reactions\n"
        except:
            continue

    await channel.send(message)

    reaction_counts.clear()
    save_data(reaction_counts)

# =============================
# Startup
# =============================
@bot.event
async def on_ready():
    if not daily_leaderboard.is_running():
        daily_leaderboard.start()
    print(f"Bot is online as {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)
