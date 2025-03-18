# Installation (Windows)

## Install Docker (Docker Desktop)
https://www.docker.com/products/docker-desktop/

## Install Ollama
https://ollama.com/download

## Set Up Kokoro
  https://github.com/remsky/Kokoro-FastAPI
  
  In Docker Desktop, open a terminal and run one of the two f ollowing commands (or follow setup instructions at the link):

CPU:

    docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.2
    
NVIDIA GPU:

    docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:v0.2.2

## Run setup.bat:
  This installs python (conda) and the required python modules.
  
  You can install manually from requirements.txt if you want. Tested with Python 3.13.2

## Create a Discord Bot

Creating a Bot Account

1. Go to https://discord.com/developers/applications

2. Click on the “New Application” button.

3. Give the application a name and click “Create”.

4. Navigate to the “Bot” tab to configure it.

5. You should also make sure that Require OAuth2 Code Grant is checked

6. Copy the token using the “Copy” button.


Inviting Your Bot
1. Click on your bot's page.

2. Go to the “OAuth2 > URL Generator” tab.

3. Tick the “bot” checkbox under “scopes”.

4. Tick the "Administrator" permission under “Bot Permissions”.

5. Copy and paste the URL into your browser, choose a server to invite the bot to, and click “Authorize”.

Instructions with pictures, specifically look at the "How to Make a Discord Bot in the Developer Portal" section

https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-python 

## Update config.ini
  1. Rename config-default.ini to config.ini
  
  2. Add your Discord Bot Token 
  
  3. Add Discord IDs voice and text channels
    Right click > Copy Channel ID
    
  4. Change chat model and discord command prefix (if desired)

## Edit character.json
  Edit system prompt, character name, and voice


# Usage
Start kokoro in docker
	
run start.bat
    
type !help in discord to get a list of commands

    connect        Connect to the voice channel
    disconnect     Disconnect from the voice channel
    help           Shows this message
    refresh        load changes to system prompt or voice
    text_log       log all voice messages to text channel
    memory_reset   clears current memory
    trigger_phrase prevent responses unless trigger phrase is spoken

All bot messages are sent by the bot in the text channel you specify in config.ini, regardless of where you send commands.

If you want to edit more specific llm settings like temperature, those are all in "discord-bot.py"

## Available Voices
"af_alloy", "af_aoede", "af_bella", "af_heart", "af_jadzia", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky", "af_v0", "af_v0bella", "af_v0irulan", "af_v0nicole", "af_v0sarah", "af_v0sky", "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa", "am_v0adam", "am_v0gurney", "am_v0michael", "bf_alice", "bf_emma", "bf_lily", "bf_v0emma", "bf_v0isabella", "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "bm_v0george", "bm_v0lewis", "ef_dora", "em_alex", "em_santa", "ff_siwis", "hf_alpha", "hf_beta", "hm_omega", "hm_psi", "if_sara", "im_nicola", "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo", "pf_dora", "pm_alex", "pm_santa", "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"

By default, the language is picked based on the language of the voice. What this means is that selecting "ef_dora" will "read" english text as if it is spanish (and spanish text as if it is spanish). This comes through as _heavily_ accented english, changing the language manually will greatly decrease the accent.

## Voice Mixing
Voices can be mixed together as shown, with different ratios or number of voices.

"voice": "af_bella(2)+af_sky(1)"

