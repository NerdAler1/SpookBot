import discord
import asyncio
import random
from dotenv import load_dotenv
import os
import logging

load_dotenv()
# --------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
MIN_INTERVAL = int(os.getenv("MIN"))
MAX_INTERVAL = int(os.getenv("MAX"))
SOUNDS_DIR = "./Screams"
# ---------------------------------------

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
client = discord.Client(intents=intents)
voice_client: discord.VoiceClient | None = None
play_task: asyncio.Task | None = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

async def connect_to_channel():
    """Connect bot to VC."""
    global voice_client
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        print("Voice channel not found!")
        return None
    if voice_client and voice_client.is_connected():
        print("Already connected to a voice channel.")
        return voice_client
    print(f"Connecting to {channel.name}...")
    voice_client = await channel.connect()
    return voice_client

async def disconnect_from_channel():
    """Disconnect bot from VC."""
    global voice_client, play_task
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        voice_client = None
        if play_task:
            play_task.cancel()
            play_task = None
        print("Disconnected from voice channel.")

async def play_sounds_loop():
    """Loop that plays random sounds."""
    global voice_client
    while True:
        try:
            if not voice_client or not voice_client.is_connected():
                return
            if voice_client.is_playing():
                voice_client.stop()

            interval = random.randint(MIN_INTERVAL, MAX_INTERVAL) * 60
            logging.info(f"Next play in {interval / 60:.1f} minutes.")

            sound_files = [f for f in os.listdir(SOUNDS_DIR) if os.path.isfile(os.path.join(SOUNDS_DIR, f))]
            if not sound_files:
                print("No sound files found.")
                await asyncio.sleep(interval)
                continue

            sound_file = os.path.join(SOUNDS_DIR, random.choice(sound_files))
            source = discord.FFmpegPCMAudio(sound_file)
            voice_client.play(source)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            logging.info("Finished playing sound.")
            await asyncio.sleep(interval)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error playing sound: {e}")
            await asyncio.sleep(5)

@client.event
async def on_ready():
    global play_task
    print(f"Bot connected as {client.user}")
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)

    if not channel:
        print("Voice channel not found on startup.")
        return

    # Check if any non-bot members are in the voice channel
    non_bots_present = any(not m.bot for m in channel.members)
    if non_bots_present:
        print("Non-bot members already in voice channel. Connecting...")
        await connect_to_channel()
        if not play_task:
            play_task = asyncio.create_task(play_sounds_loop())
    else:
        print("No members in voice channel at startup.")

@client.event
async def on_voice_state_update(member, before, after):
    global play_task
    if member.bot:
        return

    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        return

    # Someone joined
    if after.channel == channel and before.channel != channel:
        if not voice_client or not voice_client.is_connected():
            await asyncio.sleep(10)
            await connect_to_channel()
            if not play_task:
                play_task = asyncio.create_task(play_sounds_loop())

    # Someone left
    if before.channel == channel and after.channel != channel:
        if len([m for m in channel.members if not m.bot]) == 0:
            await disconnect_from_channel()

client.run(TOKEN)