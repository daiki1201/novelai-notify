import json
import os

import discord
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_IDS = [
    837068173009223711,
    1081002553099157524,
]
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
STATE_FILE = "discord_last_messages.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}],
    }
    response = requests.post(url, headers=headers, json=data, timeout=10)
    if response.status_code != 200:
        print(f"LINE message error: {response.status_code} {response.text}")


def format_message(message):
    content = message.content.strip() or "(textなし)"
    channel_name = getattr(message.channel, "name", str(message.channel.id))
    guild_name = getattr(message.guild, "name", "DM")
    return (
        "[Discord通知]\n"
        f"{guild_name} / #{channel_name}\n"
        f"{message.author.display_name}: {content}"
    )


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def process_channel(channel_id, state):
    state_key = str(channel_id)
    last_seen_id = int(state[state_key]) if state_key in state else None
    channel = client.get_channel(channel_id)
    if channel is None:
        channel = await client.fetch_channel(channel_id)

    if last_seen_id is None:
        latest_messages = [message async for message in channel.history(limit=1)]
        if latest_messages:
            state[state_key] = latest_messages[0].id
            print(f"Initialized channel {channel_id} with {latest_messages[0].id}")
        else:
            print(f"No messages found in channel {channel_id}")
        return

    after = discord.Object(id=last_seen_id)
    new_messages = [
        message
        async for message in channel.history(limit=None, after=after, oldest_first=True)
    ]
    if not new_messages:
        print(f"No new messages in channel {channel_id}")
        return

    for message in new_messages:
        if message.author.bot:
            continue
        send_line_message(format_message(message))
        print(f"LINE sent for channel {channel_id}: {message.id}")

    state[state_key] = new_messages[-1].id


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    state = load_state()
    try:
        for channel_id in DISCORD_CHANNEL_IDS:
            await process_channel(channel_id, state)
        save_state(state)
    finally:
        await client.close()


client.run(DISCORD_TOKEN)
