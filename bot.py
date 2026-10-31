import os
import discord
import asyncio
import math
import soundfile as sf
import numpy
import io
from faster_whisper import WhisperModel
from scipy.signal import resample_poly
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()

@bot.event
async def on_ready():
    print("bot login complete")

@lru_cache(maxsize=1)
def load_model():
    return WhisperModel("base", device="cpu", compute_type="int8")
def transcribe_audio(way_bytes):
    audio, sample_rate = sf.read(io.BytesIO(way_bytes), dtype="float32")
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sample_rate != 16000:
        divisor = math.gcd(sample_rate, 16000)
        audio = resample_poly(audio, 16000// divisor, sample_rate // divisor)

    audio = numpy.asarray(audio, dtype="float32")

    if len(audio) < 16000:
        return ""

    model = load_model()
    segments, info = model.transcribe(
        audio,
        language="ko",
        beam_size=5,
        vad_filter=True
    )

    text = " ".join(segments.text.strip() for segments in segments)
    return text.strip()


@bot.slash_command(name="start", description="enter audio channel")
async def start(ctx: discord.ApplicationContext):
    if ctx.author.voice is None:
        await ctx.respond("please enter audio channel")
        return
    if ctx.guild.voice_client is None:
        await ctx.respond("bot already came here")

    await ctx.author.voice.channel.connect()

    sink = discord.sinks.WaveSink
    text_channel = ctx.channel
    async def recording_finished(error):
        try:
            if error:
                await text_channel.send("record error")
                return

            if not sink.audio_data:
                await text_channel.send("there is no audio data")
                return

            await text_channel.send("record finished")

            for user_id, recorded_audio in sink.audio_data.items():
                try:
                    recorded_audio.file.seek(0)
                    way_bytes = recorded_audio.file.read()
                    text = await asyncio.to_thread(transcribe_audio, way_bytes)
                    if text:
                        for i in range(0, len(text), 1700):
                            chunk = text[i:i + 1700]
                        else:


    await ctx.respond("bot connected")



if __name__ == "__main__":
    bot.run(TOKEN)
