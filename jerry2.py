import os
import difflib
import time
import json
import requests
import subprocess
from io import BytesIO
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.contacts import SearchRequest

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

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, можешь использовать постоянно юмор какой-то. Избегай длинных объяснений.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def speak(text):
    config = load_config()
    print(f"\n💬 Джерри: {text}")
    audio = elevenlabs.text_to_speech.convert(
        voice_id=config["voice_id"],
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_24000"
    )
    with open("output.wav", "wb") as f:
        f.write(b"".join(audio))
    os.system("aplay -D plughw:0,0 -c 1 -f S16_LE -r 24000 output.wav")

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

def ask_grok(prompt):
    config = load_config()
    system_prompt = {"role": "system", "content": config["style_prompt"]}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    data = {
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7,
        "messages": [system_prompt] + history + [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": content})
    return content

import difflib

latest_chat = None
latest_sender = None
pending_similar_contacts = []

async def telegram_logic(command):
    global latest_chat, latest_sender, pending_similar_contacts
    command_lower = command.lower().strip()

    if "найди" in command_lower and "чат" not in command_lower:
        name = command_lower.replace("найди", "").strip()
        user = await find_contact_by_name_exact(name)
        if user:
            latest_chat = user
            pending_similar_contacts = []
            speak(f"Нашёл {user.first_name}. Что ему написать?")
        else:
            similar = await find_similar_contacts(name)
            if similar:
                pending_similar_contacts = similar
                text_list = ", ".join(f"{i+1}. {c.first_name}" for i, c in enumerate(similar))
                speak(f"Не нашёл точно, но нашёл: {text_list}. Скажи номер или имя.")
            else:
                speak("Не нашёл такого контакта.")
        return True

    # Выбор контакта из похожих
    if pending_similar_contacts:
        choice = command_lower.strip()
        # Если сказали номер
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(pending_similar_contacts):
                latest_chat = pending_similar_contacts[idx]
                speak(f"Хорошо. Что пишем {latest_chat.first_name}?")
                pending_similar_contacts = []
                return True
        # Если сказали имя
        for c in pending_similar_contacts:
            if c.first_name.lower() in choice:
                latest_chat = c
                speak(f"Хорошо. Что пишем {latest_chat.first_name}?")
                pending_similar_contacts = []
                return True

        speak("Не понял выбор, скажи номер или имя из списка.")
        return True

    # остальная логика (например, "ответь ему", "напиши", "кто мне написал") ...

    return False

async def find_contact_by_name_exact(name):
    name = name.lower()
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.is_user:
            entity = dialog.entity
            full_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip().lower()
            if name == full_name:
                return entity
    return None

async def find_similar_contacts(name):
    name = name.lower()
    dialogs = await client.get_dialogs()
    result = []
    for dialog in dialogs:
        if dialog.is_user:
            entity = dialog.entity
            full_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip().lower()
            # Ищем вхождение имени в полном имени контакта
            if name in full_name or full_name in name:
                result.append(entity)
            else:
                # Можно добавить похожесть по частичному совпадению
                if any(part in full_name for part in name.split()):
                    result.append(entity)
    return result


async def main_loop():
    global STATE
    await client.start(phone=PHONE)
    config = load_config()
    WAKE_WORD = config["wake_word"].lower()
    speak("Система активирована. Джерри слушает.")

    while True:
        record_audio(duration=3)
        text = transcribe_audio().lower().strip()
        if not text:
            continue

        if STATE == "sleep":
            if WAKE_WORD in text:
                STATE = "active"
                speak("Слушаю.")
        elif STATE == "active":
            print(f"📥 Ты сказал: {text}")
            if "пока" in text:
                speak("Поняла, ухожу в режим ожидания.")
                STATE = "sleep"
                continue
            try:
                if not await telegram_logic(text):
                    response = ask_grok(text)
                    speak(response)
            except Exception as e:
                print(e)
                speak("Произошла ошибка.")
            timeout = time.time() + 15
            while time.time() < timeout:
                record_audio(duration=3)
                followup = transcribe_audio().strip()
                if followup:
                    print(f"📥 Продолжение: {followup}")
                    try:
                        if not await telegram_logic(followup):
                            response = ask_grok(followup)
                            speak(response)
                        timeout = time.time() + 15
                    except Exception as e:
                        speak("Ошибка при ответе.")
                        print(e)
                else:
                    speak("Понял, ухожу в режим ожидания.")
                    STATE = "sleep"
                    break

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main_loop())
