import os
import difflib
import time
import json
import re
import requests
import subprocess
from io import BytesIO
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import User, MessageService
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from youtubesearchpython import VideosSearch

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
STATE_FILE = "state.json"
SHEET_NAME = "Jerry KEY"  # Название твоей Google Таблицы
STATE = "sleep"
history = []
latest_sender = None
latest_chat = None

# Инициализация клиента Telegram с сессией
client = TelegramClient('session_jerry', API_ID, API_HASH)
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)

def get_keys_from_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open(SHEET_NAME).sheet1
    return sheet.get_all_records()

def is_key_valid(key):
    try:
        records = get_keys_from_google_sheet()
    except Exception as e:
        print("Ошибка доступа к Google Sheets:", e)
        return False
    for row in records:
        sheet_key = str(row.get("Ключ", "")).strip()
        paid = str(row.get("Оплачен", "")).strip().lower() == "да"
        if sheet_key == key and paid:
            return True
    return False

def load_saved_key():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("activation_key")
    except:
        return None

def speak_startup(text):
    print(f"\n💬 Джерри: {text}")
    audio = elevenlabs.text_to_speech.convert(
        voice_id="Obuyk6KKzg9olSLPaCbl",
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_24000"
    )
    with open("output.wav", "wb") as f:
        f.write(b"".join(audio))
    os.system("aplay -D plughw:0,0 -c 1 -f S16_LE -r 24000 output.wav")

def check_activation_key():
    saved_key = load_saved_key()
    if not saved_key:
        speak_startup("У меня нет доступа к ключу активации.")
        exit(1)
    if not is_key_valid(saved_key):
        speak_startup("У меня нет доступа к ключу активации.")
        exit(1)
    speak_startup("Система запущена.")

check_activation_key()

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

latest_chat = None
latest_sender = None
fuzzy_matches = {}
awaiting_message = False
unread_users = {}

async def telegram_logic(command):
    global latest_chat, latest_sender, fuzzy_matches, awaiting_message, unread_users
    command = command.lower().strip()

    if "непрочитан" in command or "кто мне писал" in command:
        unread_users = {}
        dialogs = await client.get_dialogs(limit=30)
        count = 0

        for dialog in dialogs:
            entity = dialog.entity
            if not isinstance(entity, User) or entity.bot:
                continue

            if dialog.unread_count > 0:
                messages = await client.get_messages(entity, limit=1)
                if messages:
                    msg = messages[0]
                    if isinstance(msg, MessageService):
                        continue
                    sender = await msg.get_sender()
                    if sender and sender.first_name:
                        unread_users[sender.first_name.lower()] = (entity, msg.message)
                        count += 1
                        if count >= 4:
                            break

        if unread_users:
            names = ', '.join(name.capitalize() for name in unread_users.keys())
            speak(f"У тебя есть сообщение от: {names}. Чьё сообщение прочитать?")
        else:
            speak("Нет новых сообщений от людей.")
        return True

    if unread_users:
        for name in unread_users:
            if name in command:
                chat, message = unread_users[name]
                latest_chat = chat
                speak(f"{name.capitalize()} написала: {message}")
                unread_users = {}
                return True

    if command.startswith("ответь ему") and latest_chat:
        text = command.replace("ответь ему", "").strip()
        speak(f"Ок, пишу: {text}")
        await client.send_message(latest_chat, text)
        awaiting_message = False
        return True

    if fuzzy_matches:
        for word, number in {
            "перв": 1, "втор": 2, "трет": 3, "1": 1, "2": 2, "3": 3
        }.items():
            if word in command:
                if number in fuzzy_matches:
                    user = fuzzy_matches[number]
                    latest_chat = user
                    fuzzy_matches = {}
                    awaiting_message = True
                    speak(f"Хорошо. Что пишем {user.first_name}?")
                    return True

    if "найди" in command and "чат" not in command:
        name = command.replace("найди", "").strip()
        user = await find_contact_by_name(name)
        if user:
            latest_chat = user
            awaiting_message = True
            speak(f"Нашёл {user.first_name}. Что ему написать?")
        elif fuzzy_matches:
            options = ', '.join([f"{i}. {user.first_name}" for i, user in fuzzy_matches.items()])
            speak(f"Не нашёл точно, но нашёл: {options}. Скажи номер или имя.")
        else:
            speak("Не нашёл такого контакта.")
        return True

    if command.startswith("напиши "):
        text_to_send = command.replace("напиши ", "").strip()
        if latest_chat:
            speak(f"Пишу: {text_to_send}")
            await client.send_message(latest_chat, text_to_send)
            awaiting_message = False
        else:
            speak("Не выбран получатель.")
        return True

    if awaiting_message and latest_chat:
        speak(f"Пишу: {command}")
        await client.send_message(latest_chat, command)
        awaiting_message = False
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

# --- Новая часть — поиск и воспроизведение музыки ---

def search_youtube(query):
    search = VideosSearch(query, limit=1)
    results = search.result().get("result")
    if results:
        video_id = results[0]['id']
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def play_audio_stream(url):
    print(f"▶ Воспроизвожу: {url}")
    subprocess.Popen(["mpv", "--no-video", url])

def try_play_song(command):
    command = command.lower()
    match = re.search(r"включи\s+(.+)", command)
    if match:
        query = match.group(1).strip()
        url = search_youtube(query)
        if url:
            play_audio_stream(url)
            return f"🎵 Воспроизводится: {query}"
        else:
            return "❌ Не удалось найти трек"
    return None

# --- Главный цикл ---

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

            # Попытка запустить музыку по команде
            song_response = try_play_song(text)
            if song_response:
                speak(song_response)
                continue  # Пропускаем остальную обработку

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
