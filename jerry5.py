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
stop_speaking = False  # 🟢 NEW — флаг для прерывания речи

# Инициализация клиента Telegram
client = TelegramClient('session_jerry', API_ID, API_HASH)
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, с юмором.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def record_audio(filename=AUDIO_FILENAME, duration=3):
    subprocess.run(
        ["arecord", "-D", MIC_DEVICE, "-f", "cd", "-t", "wav", "-d", str(duration), "-r", "16000", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# 🟢 NEW — потоковая озвучка с возможностью прерывания
def speak_stream(text):
    global stop_speaking
    stop_speaking = False

    config = load_config()
    voice_id = config["voice_id"]
    print(f"\n💬 Джерри: {text}")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/pcm",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.5}
    }

    bluetooth_sink = "bluez_sink.A6_D0_01_E1_EA_6D.a2dp_sink"

    with subprocess.Popen(["paplay", "--device", bluetooth_sink],
                          stdin=subprocess.PIPE) as player:
        with requests.post(url, headers=headers, json=payload, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if stop_speaking:
                    print("🛑 Озвучка остановлена.")
                    break
                if chunk:
                    player.stdin.write(chunk)
            if player.stdin:
                player.stdin.close()
            player.wait()


def stop_speak():
    global stop_speaking
    stop_speaking = True


def transcribe_audio(filename=AUDIO_FILENAME):
    with open(filename, "rb") as f:
        transcription = elevenlabs.speech_to_text.convert(
            file=BytesIO(f.read()),
            model_id="scribe_v1",
            language_code="ru"
        )
    return transcription.text or ""


# 🟢 NEW — стриминговый ответ от Grok
def ask_grok_stream(prompt):
    config = load_config()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}

    system_prompt = {"role": "system", "content": config["style_prompt"]}
    data = {
        "model": "grok-3-latest",
        "stream": True,
        "temperature": 0.7,
        "messages": [system_prompt] + history + [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, stream=True)
    text_buffer = ""
    for line in response.iter_lines():
        if not line:
            continue
        if b"data:" not in line:
            continue
        try:
            chunk = json.loads(line.decode().split("data: ")[-1])
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                text_buffer += delta
                print(delta, end="", flush=True)
        except Exception:
            pass
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": text_buffer})
    return text_buffer


latest_chat = None
fuzzy_matches = {}
awaiting_message = False
unread_users = {}


async def telegram_logic(command):
    global latest_chat, fuzzy_matches, awaiting_message, unread_users
    command = command.lower().strip()

    if "стоп" in command:  # 🟢 NEW — команда стоп
        stop_speak()
        speak_stream("Окей, остановился.")
        return True

    # 🔍 Найти контакт
    if "найди" in command:
        name = command.replace("найди", "").strip()
        user = await find_contact_by_name(name)
        if user:
            latest_chat = user
            awaiting_message = True
            speak_stream(f"Нашёл {user.first_name}. Что ему сказать?")
        elif fuzzy_matches:
            opts = ', '.join([f"{i}. {u.first_name}" for i, u in fuzzy_matches.items()])
            speak_stream(f"Похожие: {opts}. Назови номер.")
        else:
            speak_stream("Не нашёл.")
        return True

    # 🟢 NEW — Отправка голосового после фразы
    if awaiting_message and latest_chat:
        speak_stream(f"Отправляю голосовое: {command}")
        # Сохраняем озвучку в файл
        filename = "voice_message.wav"
        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{load_config()['voice_id']}/stream"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json"
        }
        payload = {
            "text": command,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.5}
        }

        with requests.post(tts_url, headers=headers, json=payload, stream=True) as r:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

        # Отправляем voice
        await client.send_file(latest_chat, filename, voice_note=True)
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


async def main_loop():
    global STATE
    await client.start(phone=PHONE)
    config = load_config()
    WAKE_WORD = config["wake_word"].lower()
    speak_stream("Система активирована. Джерри слушает.")

    while True:
        record_audio(duration=3)
        text = transcribe_audio().lower().strip()
        if not text:
            continue

        if STATE == "sleep":
            if WAKE_WORD in text:
                STATE = "active"
                speak_stream("Слушаю.")
        elif STATE == "active":
            print(f"📥 Ты сказал: {text}")

            if "пока" in text:
                speak_stream("Понял, ухожу в ожидание.")
                STATE = "sleep"
                continue

            try:
                if not await telegram_logic(text):
                    response = ask_grok_stream(text)
                    speak_stream(response)
            except Exception as e:
                print(e)
                speak_stream("Ошибка.")

            timeout = time.time() + 15
            while time.time() < timeout:
                record_audio(duration=3)
                followup = transcribe_audio().lower().strip()
                if followup:
                    if "стоп" in followup:
                        stop_speak()
                        speak_stream("Окей, остановился.")
                        continue
                    print(f"📥 Продолжение: {followup}")
                    try:
                        if not await telegram_logic(followup):
                            response = ask_grok_stream(followup)
                            speak_stream(response)
                        timeout = time.time() + 15
                    except Exception as e:
                        print(e)
                        speak_stream("Ошибка.")
                else:
                    speak_stream("Понял, ухожу в режим ожидания.")
                    STATE = "sleep"
                    break


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main_loop())
