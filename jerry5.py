import os
import difflib
import time
import json
import requests
import subprocess
import threading
import queue
from io import BytesIO
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from telethon import TelegramClient
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

# Инициализация клиентов
client = TelegramClient('session_jerry', API_ID, API_HASH)
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)

# ====== ЗАГРУЗКА КОНФИГА ======
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, можешь использовать юмор. Избегай длинных объяснений.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# ====== ЗАПИСЬ АУДИО ======
def record_audio(filename=AUDIO_FILENAME, duration=3):
    subprocess.run(
        ["arecord", "-D", MIC_DEVICE, "-f", "cd", "-t", "wav", "-d", str(duration), "-r", "16000", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# ====== ОЧЕРЕДЬ ОЗВУЧКИ ======
speak_queue = queue.Queue()

def speak_worker():
    while True:
        text = speak_queue.get()
        if text is None:
            break
        config = load_config()
        voice_id = config["voice_id"]
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Accept": "audio/pcm",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }

        bluetooth_sink = "bluez_sink.A6_D0_01_E1_EA_6D.a2dp_sink"
        try:
            with subprocess.Popen(["paplay", "--device", bluetooth_sink], stdin=subprocess.PIPE) as player:
                with requests.post(url, headers=headers, json=payload, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk and player.stdin:
                            player.stdin.write(chunk)
                if player.stdin:
                    player.stdin.close()
                player.wait()
        except Exception as e:
            print("Ошибка воспроизведения:", e)

# Запускаем поток один раз
threading.Thread(target=speak_worker, daemon=True).start()

def speak(text):
    print(f"\n💬 Джерри: {text}")
    speak_queue.put(text)

# ====== РАСПОЗНАВАНИЕ АУДИО ======
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

# ====== STREAM GROC ======
def ask_grok_stream(prompt, speak_func):
    import sseclient
    config = load_config()
    system_prompt = {"role": "system", "content": config["style_prompt"]}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    data = {
        "model": "grok-3-latest",
        "stream": True,
        "temperature": 0.7,
        "messages": [system_prompt] + history + [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, stream=True)
    client_sse = sseclient.SSEClient(response)

    full_text = ""
    buffer = ""
    for event in client_sse.events():
        if event.event == "message":
            try:
                chunk = json.loads(event.data)
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        buffer += delta
                        if len(buffer) > 30 or delta.endswith(('.', '!', '?')):
                            speak_func(buffer)
                            full_text += buffer
                            buffer = ""
            except Exception:
                pass
    if buffer:
        speak_func(buffer)
        full_text += buffer

    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": full_text})
    return full_text

# ====== TELEGRAM ЛОГИКА ======
latest_chat = None
fuzzy_matches = {}
awaiting_message = False
unread_users = {}

async def telegram_logic(command):
    global latest_chat, fuzzy_matches, awaiting_message, unread_users
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
        for word, number in {"перв":1,"втор":2,"трет":3,"1":1,"2":2,"3":3}.items():
            if word in command and number in fuzzy_matches:
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

# ====== ОСНОВНОЙ ЦИКЛ ======
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
                    ask_grok_stream(text, speak)
            except Exception as e:
                print(e)
                speak("Произошла ошибка.")

            # слушаем дальше 15 секунд
            timeout = time.time() + 15
            while time.time() < timeout:
                record_audio(duration=3)
                followup = transcribe_audio().strip()
                if followup:
                    print(f"📥 Продолжение: {followup}")
                    try:
                        if not await telegram_logic(followup):
                            ask_grok_stream(followup, speak)
                        timeout = time.time() + 15
                    except Exception as e:
                        speak("Ошибка при ответе.")
                        print(e)
                else:
                    speak("Понял, ухожу в режим ожидания.")
                    STATE = "sleep"
                    break

# ====== СТАРТ ======
if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main_loop())
