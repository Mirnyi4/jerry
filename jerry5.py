import os
import difflib
import time
import json
import requests
import subprocess
import threading
from io import BytesIO
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import User, MessageService

load_dotenv()

# 🔑 Ключи и настройки
XAI_API_KEY = os.getenv("XAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

MIC_DEVICE = "plughw:0,0"
AUDIO_FILENAME = "input.wav"
CONFIG_PATH = "config.json"
STATE = "sleep"
history = []
latest_sender = None
latest_chat = None

# Инициализация клиента Telegram с сессией
client = TelegramClient('session_jerry', API_ID, API_HASH)
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)


# ==========================
# ⚙️  Конфигурация
# ==========================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, можешь использовать постоянно юмор какой-то. Избегай длинных объяснений.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# ==========================
# 🎤  Запись и распознавание речи
# ==========================
def record_audio(filename=AUDIO_FILENAME, duration=3):
    subprocess.run(
        ["arecord", "-D", MIC_DEVICE, "-f", "cd", "-t", "wav", "-d", str(duration), "-r", "16000", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def transcribe_audio(filename=AUDIO_FILENAME):
    with open(filename, "rb") as f:
        transcription = elevenlabs.speech_to_text.convert(
            file=BytesIO(f.read()),
            model_id="scribe_v1",
            language_code="ru",
            diarize=False,
            tag_audio_events=False
        )
    return transcription.text or ""


# ==========================
# 🧠  Потоковый Grok
# ==========================
def ask_grok_stream(prompt):
    """Потоковый запрос к Grok (xAI)"""
    config = load_config()
    system_prompt = {"role": "system", "content": config["style_prompt"]}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    data = {
        "model": "grok-3-latest",
        "stream": True,
        "temperature": 0.7,
        "messages": [system_prompt] + history + [{"role": "user", "content": prompt}]
    }

    collected_text = ""

    with requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, stream=True) as r:
        for line in r.iter_lines():
            if not line or not line.startswith(b"data: "):
                continue
            try:
                data_json = json.loads(line.split(b"data: ")[1])
                delta = data_json.get("choices", [{}])[0].get("delta", {}).get("content")
                if delta:
                    collected_text += delta
                    yield delta
            except Exception:
                continue

    # добавляем в историю
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": collected_text})


# ==========================
# 🔊  Потоковая озвучка ElevenLabs
# ==========================
def speak_streaming(text_chunks):
    """Озвучка в реальном времени"""
    config = load_config()
    voice_id = config["voice_id"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/pcm",
        "Content-Type": "application/json"
    }

    bluetooth_sink = "bluez_sink.A6_D0_01_E1_EA_6D.a2dp_sink"

    with subprocess.Popen(["paplay", "--device", bluetooth_sink], stdin=subprocess.PIPE) as player:
        for chunk_text in text_chunks:
            payload = {
                "text": chunk_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
            }
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                for audio_chunk in r.iter_content(chunk_size=1024):
                    if audio_chunk and player.stdin:
                        player.stdin.write(audio_chunk)
        if player.stdin:
            player.stdin.close()
        player.wait()


def speak(text):
    """Обычная (непотоковая) озвучка — используется для коротких фраз"""
    config = load_config()
    print(f"\n💬 Джерри: {text}")

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/pcm",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    voice_id = config["voice_id"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    bluetooth_sink = "bluez_sink.A6_D0_01_E1_EA_6D.a2dp_sink"

    with subprocess.Popen(
        ["paplay", "--device", bluetooth_sink],
        stdin=subprocess.PIPE
    ) as player:
        with requests.post(url, headers=headers, json=payload, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk and player.stdin:
                    player.stdin.write(chunk)
            if player.stdin:
                player.stdin.close()
            player.wait()


# ==========================
# 💬 Telegram логика
# ==========================
latest_chat = None
latest_sender = None
fuzzy_matches = {}
awaiting_message = False
unread_users = {}


async def telegram_logic(command):
    global latest_chat, latest_sender, fuzzy_matches, awaiting_message, unread_users
    command = command.lower().strip()

    # 🔔 Кто мне писал?
    if "непрочитан" in command or "кто мне писал" in command:
        unread_users = {}
        dialogs = await client.get_dialogs(limit=30)
        count = 0

        for dialog in dia
