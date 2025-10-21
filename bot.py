import discord
from discord.ext import commands, tasks
import os
import json

# قراءة التوكن من ملف .env (تأكد أن مكتبة python-dotenv منصبة عندك)
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 123456789012345678  # <-- استبدل هذا برقم سيرفرك (Guild ID)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # مهم لصلاحيات الفويس

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
VOICE_CHANNEL_ID = None  # لتخزين القناة الصوتية

# تحميل بيانات حفظ القناة الصوتية (إن وجدت)
def load_data():
    global VOICE_CHANNEL_ID
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            VOICE_CHANNEL_ID = data.get("voice_channel_id")

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"voice_channel_id": VOICE_CHANNEL_ID}, f)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"🌐 Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"⚠️ Failed to sync commands: {e}")

    load_data()
    await reconnect_to_voice()

async def reconnect_to_voice():
    """إعادة الاتصال للقناة الصوتية المحفوظة (إذا موجودة)"""
    if VOICE_CHANNEL_ID is None:
        return

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("⚠️ Guild not found")
        return

    channel = guild.get_channel(VOICE_CHANNEL_ID)
    if channel is None:
        print("⚠️ Voice channel not found")
        return

    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        if voice_client and voice_client.is_connected():
            print("⚠️ Already connected to voice channel")
            return
        await channel.connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        if voice_client:
            voice_client.play(discord.FFmpegPCMAudio("silent.mp3"), after=lambda e: None)
        print(f"🔊 Reconnected to voice channel {channel.name}")
    except Exception as e:
        print(f"⚠️ Failed to reconnect to voice: {e}")

@bot.tree.command(name="join", description="Join the voice channel and stay connected")
async def join(interaction: discord.Interaction):
    """أمر يدخل البوت للقناة الصوتية ويشغّل الصوت الصامت"""
    if interaction.user.voice is None:
        await interaction.response.send_message("❗ لازم تكون في قناة صوتية أولاً!", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    # شغّل الصوت الصامت
    voice_client.play(discord.FFmpegPCMAudio("silent.mp3"), after=lambda e: None)

    global VOICE_CHANNEL_ID
    VOICE_CHANNEL_ID = channel.id
    save_data()

    await interaction.response.send_message(f"✅ دخلت القناة الصوتية: **{channel.name}**")

@bot.tree.command(name="leave", description="Leave the voice channel")
async def leave(interaction: discord.Interaction):
    """أمر يخرج البوت من القناة الصوتية"""
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        global VOICE_CHANNEL_ID
        VOICE_CHANNEL_ID = None
        save_data()
        await interaction.response.send_message("✅ خرجت من القناة الصوتية.")
    else:
        await interaction.response.send_message("❗ البوت مش داخل أي قناة صوتية.", ephemeral=True)

# تشغيل البوت
bot.run()
