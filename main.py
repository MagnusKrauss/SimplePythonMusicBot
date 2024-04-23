# Made by MagnusKrauss @ github.com/MagnusKrauss

from discord.ext import commands
from pytube import YouTube
from asyncio import Queue
import asyncio
import discord

intents = discord.Intents.all()
intents.voice_states = True

bot = commands.Bot(command_prefix='!!', intents=intents)
song_queue = Queue()
first_play = True


async def play_next(ctx):
    global song_queue

    if not song_queue.empty():
        next_url = await song_queue.get()
        channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client is None:
            voice_client = await channel.connect()

        try:
            async with ctx.typing():
                yt = YouTube(next_url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                audio_stream.download(filename="audio.mp3")
                voice_client.play(discord.FFmpegPCMAudio("audio.mp3"), after=lambda f: bot.loop.create_task(play_next(ctx)))
                await ctx.send(f"Now playing: {yt.title}")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    else:
        voice_client = ctx.voice_client
        if voice_client:
            await asyncio.sleep(2)
            if not voice_client.is_playing() and not voice_client.is_paused():
                await voice_client.disconnect()
                if voice_client.is_connected():
                    await ctx.send("Queue is empty. Disconnecting from voice channel.")


@bot.command()
async def play(ctx, url):
    global song_queue

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is None:
        voice_client = await channel.connect()

    if voice_client.is_playing() or voice_client.is_paused():
        await song_queue.put(url)
        await ctx.send("Added to queue.")
    else:
        try:
            async with ctx.typing():
                yt = YouTube(url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                audio_stream.download(filename="audio.mp3")
                voice_client.play(discord.FFmpegPCMAudio("audio.mp3"), after=lambda f: bot.loop.create_task(play_next(ctx)))
                await ctx.send(f"Now playing: {yt.title}")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Playback stopped')


@bot.command()
@commands.has_role("Admin")
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send('Song skipped')
        await play_next(ctx)


@skip.error
async def skip_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use this command.")


@bot.event
async def on_ready():
    print('Bot has logged in via token!')

bot.run('Your application token goes here')
