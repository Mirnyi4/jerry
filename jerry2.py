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
awaiting_message = False  # ← Ждём ли текст для отправки?
contact_candidates = []  # ← сюда сохраняются похожие контакты после "найди"

async def telegram_logic(command):
    global latest_chat, latest_sender, awaiting_message
    command = command.lower()

    # Если ждём сообщение — отправляем его
    if awaiting_message and latest_chat:
        text_to_send = command.strip()
        speak(f"Пишу: {text_to_send}")
        await client.send_message(latest_chat, text_to_send)
        awaiting_message = False
        return True

    if "кто мне написал" in command or "последнее сообщение" in command:
        dialogs = await client.get_dialogs(limit=10)
        for dialog in dialogs:
            if dialog.is_user:
                messages = await client(GetHistoryRequest(
                    peer=dialog.entity,
                    limit=1, offset_date=None, offset_id=0,
                    max_id=0, min_id=0, add_offset=0, hash=0
                ))
                if messages.messages:
                    msg = messages.messages[0]
                    sender = await msg.get_sender()
                    latest_sender = sender
                    latest_chat = dialog.entity
                    answer = f"Тебе написал {sender.first_name}, он сказал: {msg.message}"
                    commentary = ask_grok(answer)
                    speak(f"{answer}. {commentary}")
                    return True

    if command.startswith("ответь ему") and latest_sender:
        text = command.replace("ответь ему", "").strip()
        speak(f"Ок, пишу: {text}")
        await client.send_message(latest_chat, text)
        return True

    if "найди" in command and "чат" not in command:
        name = command.replace("найди", "").strip()
        matches = await search_similar_contacts(name)
        if not matches:
            speak("Не нашёл такого контакта.")
        elif len(matches) == 1:
            latest_chat = matches[0]
            awaiting_message = True
            speak(f"Нашёл {matches[0].first_name}. Что ему написать?")
        else:
            options = ", ".join(f"{i+1}. {u.first_name}" for i, u in enumerate(matches))
            contact_candidates[:] = matches
            speak(f"Не нашёл точно, но нашёл: {options}. Скажи номер или имя.")
        return True

    if command.isdigit() and contact_candidates:
        index = int(command) - 1
        if 0 <= index < len(contact_candidates):
            latest_chat = contact_candidates[index]
            awaiting_message = True
            speak(f"Хорошо. Что пишем {latest_chat.first_name}?")
        else:
            speak("Такого номера в списке нет.")
        return True

    if command.startswith("напиши "):
        text_to_send = command.replace("напиши ", "").strip()
        if latest_chat:
            speak(f"Пишу: {text_to_send}")
            await client.send_message(latest_chat, text_to_send)
        else:
            speak("Не выбран получатель для сообщения.")
        return True

    return False


async def find_contact_by_name(name):
    global fuzzy_matches
    name = name.lower()
    fuzzy_matches = {}

    dialogs = await client.get_dialogs()
    candidates = []
    name_map = {}

    for dialog in dialogs:
        entity = dialog.entity
        if dialog.is_user and hasattr(entity, 'first_name'):
            full_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
            key = full_name.lower()
            name_map[key] = entity
            candidates.append(key)
            if getattr(entity, "username", None):
                uname = entity.username.lower()
                name_map[uname] = entity
                candidates.append(uname)

    matches = difflib.get_close_matches(name, candidates, n=3, cutoff=0.5)

    if len(matches) == 1:
        return name_map[matches[0]]

    elif len(matches) > 1:
        for i, m in enumerate(matches, 1):
            fuzzy_matches[i] = name_map[m]
        return None

    return None


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
