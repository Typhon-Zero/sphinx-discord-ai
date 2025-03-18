# Python 3.13.2
import os
import re
import vosk
import json
import time
import asyncio
import discord
import aiohttp
import configparser
from io import BytesIO
from discord.ext import voice_recv, commands
from ollama import AsyncClient, ChatResponse

ollama_host = "localhost"
tts_host = "http://localhost:8880/v1/audio/speech"

#### Speech model settings ####
# num_keep = 5
# num_predict = 20
# top_k = 20
# top_p = .9
# min_p  = .0
# typical_p = .7
# repeat_last_n = 33
temperature = .7
repeat_penalty = 1.2
# presence_penalty = 1.5 
# frequency_penalty = 1.0
# mirostat = 1
# mirostat_tau = .8
# mirostat_eta = .6
# penalize_newline = True
# stop = ["\n", "user:"]
# numa = False
# num_ctx = 1024
# num_batch = 2
# num_gpu = 1
# main_gpu = 0
# low_vram = False
# vocab_only = False
# use_mmap = True
# use_mlock = False
# num_thread = 8

ollama_options = {'temperature': temperature, 'repeat_penalty': repeat_penalty}
ollama_client = AsyncClient(host=ollama_host)

# TTS Speed
speed = 1.0

# Vosk bitrate
rate = 96000

config = configparser.ConfigParser()
if os.path.exists("config.ini"):
    config.read("config.ini")
else:
    input = input("config.ini not found, please copy and edit config-default.ini")
    exit()

TOKEN = config['DISCORD']['DISCORD_TOKEN']
text_id = config.getint('DISCORD', 'text_id')
voice_id = config.getint('DISCORD', 'voice_id')
command_prefix = config['OTHER']['command_prefix']
text_model = config['OTHER']['text_model']

speaking = False
audio_processing = False
text_output = False
trigger_phrase_state = False

pcm_buffer = []
user_list = []
history = []
voice_client = ""

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
help_command = commands.DefaultHelpCommand(no_category = 'Commands')
bot = commands.Bot(intents=intents, command_prefix=f"{command_prefix}", help_command=help_command)

def callback(user, data: voice_recv.VoiceData):
    global pcm_buffer, last_audio_time, user_list, audio_processing
    voice_user = data.source.global_name
    if voice_user not in user_list:
        user_list.append(voice_user)
        pcm_buffer.append(b"")
    user_index = user_list.index(voice_user)
    pcm_buffer[user_index] += data.pcm
    last_audio_time = time.time()
    audio_processing = True

async def process_audio():
    global pcm_buffer, audio_processing
    message_queue = ""
    partial_result = {'partial': ''}
    while True:
        if audio_processing:
            for index, element in enumerate(pcm_buffer):
                same_user = True
                while same_user:
                    if len(pcm_buffer[index]) > 16000:
                        selected_user = user_list[index]
                        if rec.AcceptWaveform(pcm_buffer[index]):
                            result = json.loads(rec.Result())
                            recognized_text = result['text']
                            user_message = (str(selected_user) + " says: " + recognized_text)
                            same_user = False
                            await write_history("user", user_message)
                            message_queue += user_message
                            
                        else:
                            partial_result = json.loads(rec.PartialResult())
                            # print(partial_result)
                            # if partial_result['partial']:
                            #     print(f"(Partial) {str(selected_user)} might be saying: {partial_result['partial']}")
                        pcm_buffer[index] = b""
                    elif (time.time() - last_audio_time > .02) and not partial_result['partial']:
                        same_user = False
                        # break
                    elif (time.time() - last_audio_time > .4) and partial_result['partial']:
                        silence = b"\x00" * 4000
                        pcm_buffer[index] += silence
                    await asyncio.sleep(0)
            if message_queue and not any(len(item) > 16000 for item in pcm_buffer):
                if trigger_phrase in message_queue or not trigger_phrase_state:
                    try:
                        response_message = await get_ollama_response()
                        try:
                            await get_tts_response(voice, response_message)
                        except:
                            print("Unable to connect to TTS, check that docker is running")
                    except:
                        print("Unable to connect to ollama, check that the service is running")

                message_queue = ""
        await asyncio.sleep(0)

async def get_ollama_response():
    temp_history = history.copy()
    temp_history.insert(0, {"role": "system", "content": system_prompt})
    if len(temp_history) > 8000:
        print(f"histroy length is {len(temp_history)} system prompt is probably getting cut")
    response: ChatResponse = await ollama_client.chat(model=text_model, messages=temp_history, keep_alive='10m', options=ollama_options)
    cleaned_message = re.sub(r"\*.*?\*", "", re.sub(r"\[.*?\]", "", response.message.content))
    await write_history("assistant", cleaned_message)
    return cleaned_message

async def get_tts_response(voice, text):
    global voice_client
    async with aiohttp.ClientSession() as session:
        async with session.post(
            tts_host,
            json={
                "model": "kokoro",
                "input": text,
                "voice": voice,
                "response_format": "wav",
                "speed": speed
            }
        ) as response:
            audio_data = await response.read()
            audio_buffer = BytesIO(audio_data)
    while voice_client.is_playing():
        await asyncio.sleep(.1)
    source = discord.FFmpegPCMAudio(audio_buffer, pipe=True)
    voice_client.play(source)


async def load_character():
    global character, voice, system_prompt, trigger_phrase
    with open(f"character.json", 'r') as file:
        card = json.load(file)
    character = card["name"]
    voice = card["voice"]
    system_prompt = card["system_prompt"]
    trigger_phrase = card["trigger_phrase"]

async def initialize_vosk(rate):
    global rec
    # Small model (faster loading)
    model = vosk.Model(model_name="vosk-model-small-en-us-0.15")
    # Normal model
    # model = vosk.Model(model_name="vosk-model-en-us-0.22")
    rec = vosk.KaldiRecognizer(model, rate)

async def write_history(role, message):
    print(message)
    global history, text_channel
    history.append({"role": role, "content": message})
    if text_output:
        if role == "assistant":
            await text_channel.send(f"{message}")
        else:
            await text_channel.send(f"{role} says: {message}")


#### DISCORD ####
@bot.event
async def on_ready():
    global text_channel, voice_channel
    text_channel = bot.get_channel(text_id)
    voice_channel = bot.get_channel(voice_id)
    await load_character()
    await initialize_vosk(rate)
    asyncio.create_task(process_audio())
    print("Discord Client Ready")

@bot.event
async def on_voice_state_update(member, before, after):
    global voice_channel
    if member == bot.user:
        return
    if before.channel != voice_channel and after.channel == voice_channel:
        connection_message = f"{member.global_name} Connected to voice"
        await write_history("user", connection_message)
    if before.channel == voice_channel and after.channel != voice_channel:
        disconnect_message = f"{member.global_name} Disconnected from voice"
        await write_history("user", disconnect_message)

@bot.command(name="connect", help="connect to the voice channel")
async def connect(ctx):
    global voice_channel, voice_client
    voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
    voice_client.listen(voice_recv.BasicSink(callback))

@bot.command(name="disconnect", help="disconnect from the voice channel")
async def disconnect(ctx):
    global voice_client
    await voice_client.disconnect()

@bot.command(name="refresh", help="load changes to system prompt or voice")
async def refresh_character(ctx):
    await load_character()
    await ctx.send("character refreshed")

@bot.command(name="text_log", help="log all voice messages to text channel")
async def text_logging(ctx):
    global text_output
    if text_output:
        text_output = False
        await ctx.send("text logging disabled")
    else:
        text_output = True
        await ctx.send("text logging enabled")

@bot.command(name="trigger_phrase", help="prevent responses unless trigger phrase is spoken")
async def gui_trigger_phrase(ctx):
    global trigger_phrase_state
    if trigger_phrase_state:
        trigger_phrase_state = False
        await ctx.send("trigger phrase disabled")
    else:
        trigger_phrase_state = True
        await ctx.send("trigger phrase enabled")

@bot.command(name="memory_reset", help="clears current memory")
async def delete_history(ctx):
    global history
    await ctx.send("memory reset")
    history = []


bot.run(TOKEN)