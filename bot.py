import discord
from discord.ext import commands, tasks
import json
from datetime import time
import pytz
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    try:
        with open("reactions.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("reactions.json", "w") as f:
        json.dump(data, f)

reaction_counts = load_data()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    uid = str(user.id)
    reaction_counts[uid] = reaction_counts.get(uid, 0) + 1
    save_data(reaction_counts)

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
        user = await bot.fetch_user(int(uid))
        message += f"**{i}. {user.name}** — {count} reactions\n"

    await channel.send(message)

    reaction_counts.clear()
    save_data(reaction_counts)

@bot.event
async def on_ready():
    daily_leaderboard.start()
    print("Bot is online!")

bot.run(TOKEN)
