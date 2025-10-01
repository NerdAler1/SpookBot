import discord
from discord.ext import tasks
import asyncio
import random
from dotenv import load_dotenv
import os

load_dotenv()
# --------------- CONFIG ----------------
TOKEN=os.getenv("TOKEN")  # Your bot token
GUILD_ID=int(os.getenv("GUILD_ID"))  # Your server ID
VOICE_CHANNEL_ID=int(os.getenv("VOICE_CHANNEL_ID"))  # Your voice channel ID
PLAY_INTERVAL = random.randint(int(os.getenv("MIN")), int(os.getenv("MAX"))) * 60 # Randomize interval
SOUNDS_DIR = "./Screams"
# ---------------------------------------


intents = discord.Intents.default()
client = discord.Client(intents=intents)

voice_client: discord.VoiceClient | None = None

@client.event
async def on_ready():
    print(f"Bot connected as {client.user}")
    await connect_to_channel()
    play_sound.start()

async def connect_to_channel():
    """Ensure the bot is connected to the VC."""
    global voice_client
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(VOICE_CHANNEL_ID)

    if not channel:
        print("Voice channel not found!")
        return

    if not voice_client or not voice_client.is_connected():
        print(f"Connecting to {channel.name}...")
        voice_client = await channel.connect()

@tasks.loop(seconds=PLAY_INTERVAL)
async def play_sound():
    """Plays the sound file every interval."""
    global voice_client
    try:
        if not voice_client or not voice_client.is_connected():
            await connect_to_channel()

        if voice_client.is_playing():
            voice_client.stop()
        
        PLAY_INTERVAL = random.randint(int(os.getenv("MIN")), int(os.getenv("MAX"))) * 60 # Randomize interval
        print(f"Next play in {PLAY_INTERVAL/60} minutes.")
        
        # Get a list of all sound files in the directory
        sound_files = [f for f in os.listdir(SOUNDS_DIR) if os.path.isfile(os.path.join(SOUNDS_DIR, f))]

        SOUND_FILE = os.path.join(SOUNDS_DIR, random.choice(sound_files)) # Random Sound File
        
        # Play the file using ffmpeg
        source = discord.FFmpegPCMAudio(SOUND_FILE)
        voice_client.play(source)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        print("Finished playing sound.")
        

        
    except Exception as e:
        print(f"Error playing sound: {e}")

client.run(TOKEN)
