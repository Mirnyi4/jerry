
from datetime import datetime, timedelta
import os
import time
import threading
import json
import requests
import sounddevice as sd
import soundfile as sf
import queue
import signal

# Параметры
NAME = "Джерри"
WAKE_WORD = "привет"
GOODBYE = "Поняла, ухожу в режим ожидания."
LISTEN_TIMEOUT = 15  # секунд
HISTORY_FILE = "memory.json"
PASSWORD = "1234"  # для очистки памяти
DEVICE = "plughw:0,0"
TTS_FILE = "output.wav"
XI_API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
GROK_API_KEY = "xai-E9xNjvychdMfLI0IUDpJ9T5kHAFh0xFDYcVxPtdwCYyBb7ynVABZQuSyPkx5NFSMFTga9bgyqTsXkBWU"

q = queue.Queue()

# Инициализация памяти
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

# ---------- Звукозапись ----------
def record_audio(timeout=5):
    samplerate = 16000
    duration = timeout
    filename = "recorded.wav"

    def callback(indata, frames, time, status):
        q.put(indata.copy())

    q.queue.clear()
    with sf.SoundFile(filename, mode='w', samplerate=samplerate, channels=1) as file:
        with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
            start = time.time()
            while time.time() - start < duration:
                if not q.empty():
                    file.write(q.get())

    return filename

# ---------- Распознавание речи ----------
def transcribe(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {XI_API_KEY}"},
            files={"file": f},
            data={"model": "whisper-1"},
        )
    return response.json()["text"]

# ---------- Синтез речи ----------
def speak(text):
    print(f"🗣 {NAME}: {text}")
    url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB/stream?output_format=mp3_44100_128"
    headers = {
        "xi-api-key": XI_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }
    response = requests.post(url, headers=headers, json=data)
    with open(TTS_FILE, "wb") as f:
        f.write(response.content)
    os.system(f"ffmpeg -y -i {TTS_FILE} -ar 44100 -ac 2 -f wav - | aplay -D {DEVICE}")

# ---------- Память ----------
def load_history():
    with open(HISTORY_FILE) as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-20:], f)  # ограничим память до последних 20 сообщений

# ---------- Обработка команд ----------
def chat_with_grok(history):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": f"Ты — ассистент по имени {NAME}, общаешься просто, с юмором и черным юмором. Помни, что ты Джерри."}]
    messages.extend(history)
    data = {
        "model": "grok-3-latest",
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# ---------- Основной цикл ----------
def jerry_loop():
    print("🟢 Джерри слушает. Скажи 'Привет'...")
    active = False
    history = load_history()
    last_active = datetime.now()

    while True:
        audio_file = record_audio(5)
        text = transcribe(audio_file).lower()

        if not text.strip():
            continue

        print(f"🧠 Ты сказал: {text}")

        if not active:
            if WAKE_WORD in text:
                speak("Слушаю")
                active = True
                last_active = datetime.now()
        else:
            if PASSWORD in text and "очисти" in text:
                history = []
                save_history(history)
                speak("Память очищена.")
            else:
                history.append({"role": "user", "content": text})
                reply = chat_with_grok(history)
                history.append({"role": "assistant", "content": reply})
                save_history(history)
                speak(reply)
                last_active = datetime.now()

            if (datetime.now() - last_active).seconds > LISTEN_TIMEOUT:
                speak(GOODBYE)
                active = False
                print("🟡 В режим ожидания")

# ---------- Старт ----------
def exit_handler(sig, frame):
    print("\n[!] Выход.")
    exit(0)

signal.signal(signal.SIGINT, exit_handler)

if __name__ == "__main__":
    jerry_loop()
