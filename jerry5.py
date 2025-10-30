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

# === Ключи ===
XAI_API_KEY = os.getenv("XAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

# === Настройки ===
MIC_DEVICE = "plughw:0,0"
AUDIO_FILENAME = "input.wav"
CONFIG_PATH = "config.json"
STATE = "sleep"
stop_speaking = False
history = []

# === Инициализация ===
client = TelegramClient('session_jerry', API_ID, API_HASH)
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)

# === Telegram состояние ===
latest_chat = None
latest_sender = None
fuzzy_matches = {}
awaiting_message = False
unread_users = {}
current_contact = None
waiting_for_message = False


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и по-пацански, с юмором. Избегай длинных объяснений.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# === Речь ===
def stop_speech():
    global stop_speaking
    stop_speaking = True
    subprocess.run(["pkill", "-f", "paplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🛑 Джерри: остановил речь.")


def speak_streaming(text, send_to_telegram=False):
    global stop_speaking
    stop_speaking = False

    if not text.strip():
        return

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
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.5}
    }

    bluetooth_sink = "bluez_sink.A6_D0_01_E1_EA_6D.a2dp_sink"
    wav_path = "/tmp/jerry_voice.wav"
    ogg_path = "/tmp/jerry_voice.ogg"

    print(f"\n💬 Джерри: {text}")

    with open(wav_path, "wb") as audio_file:
        with subprocess.Popen(["paplay", "--device", bluetooth_sink], stdin=subprocess.PIPE) as player:
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                for chunk in r.iter_content(chunk_size=1024):
                    if stop_speaking:
                        break
                    if chunk:
                        if player.stdin:
                            player.stdin.write(chunk)
                        audio_file.write(chunk)
            if player.stdin:
                player.stdin.close()
            player.wait()

    if send_to_telegram and latest_chat:
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-ar", "48000", "-ac", "1", ogg_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        client.loop.run_until_complete(client.send_file(latest_chat, ogg_path, voice_note=True))
        print("📤 Отправлено голосовое в Telegram")


# === Распознавание речи ===
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
            language_code="ru"
        )
    return transcription.text or ""


# === Мозги (Grok) ===
def ask_grok(prompt):
    config = load_config()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    data = {
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": config["style_prompt"]}
        ] + history + [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": content})
    return content


# === Поиск контактов ===
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


# === Telegram логика ===
async def telegram_logic(command):
    global latest_chat, fuzzy_matches, awaiting_message, current_contact, waiting_for_message

    command = command.lower().strip()

    if command == "стоп":
        stop_speech()
        return True

    # Найти контакт
    if "найди" in command:
        name = command.replace("найди", "").strip()
        if not name:
            speak_streaming("Кого искать?")
            return True
        user = await find_contact_by_name(name)
        if user:
            latest_chat = user
            current_contact = user
            waiting_for_message = True
            speak_streaming(f"Нашёл {user.first_name}. Что ему сказать?")
        elif fuzzy_matches:
            options = ', '.join([f"{i}. {user.first_name}" for i, user in fuzzy_matches.items()])
            speak_streaming(f"Похожие: {options}. Назови номер.")
        else:
            speak_streaming("Не нашёл такого.")
        return True

    # Выбор контакта
    if fuzzy_matches:
        for word, number in {"перв": 1, "втор": 2, "трет": 3, "1": 1, "2": 2, "3": 3}.items():
            if word in command:
                if number in fuzzy_matches:
                    user = fuzzy_matches[number]
                    latest_chat = user
                    current_contact = user
                    fuzzy_matches = {}
                    waiting_for_message = True
                    speak_streaming(f"Нашёл {user.first_name}. Что ему сказать?")
                    return True

    # Если ждём сообщение — отправляем голосовое
    if waiting_for_message and current_contact:
        speak_streaming(f"Отправляю голосовое сообщение {current_contact.first_name}.")
        speak_streaming(command, send_to_telegram=True)
        waiting_for_message = False
        current_contact = None
        return True

    return False


# === Основной цикл ===
async def main_loop():
    global STATE
    await client.start(phone=PHONE)
    config = load_config()
    WAKE_WORD = config["wake_word"].lower()
    speak_streaming("Обновление 5.0, Скажи Привет")

    while True:
        record_audio(duration=3)
        text = transcribe_audio().lower().strip()
        if not text:
            continue

        if STATE == "sleep":
            if WAKE_WORD in text:
                STATE = "active"
                speak_streaming("Слушаю.")
        elif STATE == "active":
            print(f"📥 Ты сказал: {text}")
            if "пока" in text:
                speak_streaming("Понял, ухожу в ожидание.")
                STATE = "sleep"
                continue
            try:
                if not await telegram_logic(text):
                    response = ask_grok(text)
                    speak_streaming(response)
            except Exception as e:
                print(e)
                speak_streaming("Ошибка.")

            timeout = time.time() + 15
            while time.time() < timeout:
                record_audio(duration=3)
                followup = transcribe_audio().strip()
                if followup:
                    if "стоп" in followup.lower():
                        stop_speech()
                        continue
                    print(f"📥 Продолжение: {followup}")
                    try:
                        if not await telegram_logic(followup):
                            response = ask_grok(followup)
                            speak_streaming(response)
                        timeout = time.time() + 15
                    except Exception as e:
                        print(e)
                        speak_streaming("Ошибка.")
                else:
                    speak_streaming("Ухожу в ожидание.")
                    STATE = "sleep"
                    break


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main_loop())
