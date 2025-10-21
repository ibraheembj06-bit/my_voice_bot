import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="", intents=intents)
current_volume = 1.0


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كبوت: {bot.user}")


# 🎚️ لوحة التحكم بالأزرار
class MusicControl(discord.ui.View):
    def __init__(self, vc, title, url):
        super().__init__(timeout=None)
        self.vc = vc
        self.title = title
        self.url = url

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.blurple, row=0)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ تم إيقاف التشغيل مؤقتاً.", ephemeral=True)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.green, row=0)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ تم استئناف التشغيل.", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.red, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.stop()
            await interaction.response.send_message("⏹️ تم إيقاف الموسيقى.", ephemeral=True)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.gray, row=1)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_volume
        current_volume = max(0.1, current_volume - 0.1)
        await interaction.response.send_message(f"🔉 تم خفض الصوت إلى {int(current_volume * 100)}%", ephemeral=True)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.gray, row=1)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_volume
        current_volume = min(2.0, current_volume + 0.1)
        await interaction.response.send_message(f"🔊 تم رفع الصوت إلى {int(current_volume * 100)}%", ephemeral=True)

    @discord.ui.button(emoji="👋", style=discord.ButtonStyle.gray, row=1)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.disconnect()
        await interaction.response.send_message("👋 تم مغادرة القناة الصوتية.", ephemeral=True)


# 🟢 الانضمام للقناة
@bot.command(name="ادخل")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"🎧 دخلت القناة الصوتية: **{channel.name}** ✅")
        else:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"🔄 تم الانتقال إلى: **{channel.name}**")
    else:
        await ctx.send("❌ أنت لست في قناة صوتية!")


# 🎵 تشغيل الموسيقى
@bot.command(name="شغل")
async def play(ctx, *, query):
    global current_volume

    vc = ctx.voice_client
    if not vc:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = await channel.connect()
            await ctx.send(f"🎧 دخلت القناة الصوتية: **{channel.name}** ✅")
        else:
            await ctx.send("❌ أدخل قناة صوتية أولاً!")
            return

    msg = await ctx.send(f"🔍 جاري البحث عن **{query}** ...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        url = info['url']
        title = info.get('title', 'أغنية غير معروفة 🎶')
        webpage_url = info.get('webpage_url', None)
        thumbnail = info.get('thumbnail', None)
        duration = info.get('duration', 0)
        mins, secs = divmod(duration, 60)

    # إعداد الصوت باستخدام FFmpeg مع مستوى الصوت الحالي
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': f'-vn -filter:a "volume={current_volume}"'
    }

    source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
    vc.stop()
    vc.play(source)

    # 🎨 Embed احترافي
    embed = discord.Embed(
        title="🎵 يتم الآن التشغيل",
        description=f"**[{title}]({webpage_url})**",
        color=0x1DB954
    )
    embed.add_field(name="⏱️ المدة", value=f"{mins}:{secs:02d}", inline=True)
    embed.add_field(name="🎚️ الصوت", value=f"{int(current_volume * 100)}%", inline=True)
    embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=f"طلب التشغيل بواسطة: {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

    view = MusicControl(vc, title, url)
    await msg.edit(content="", embed=embed, view=view)


# ✅ تنفيذ الأوامر بدون بادئة
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    if ctx.command is not None:
        await bot.invoke(ctx)


# 🔒 ضع توكنك الجديد هنا
bot.run("")
