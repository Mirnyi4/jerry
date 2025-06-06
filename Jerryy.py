import os
import time
import json
import subprocess
import requests
from datetime import datetime

# ==== 🔑 Ключи ====
GROK_API_KEY = "xai-E9xNjvychdMfLI0IUDpJ9T5kHAFh0xFDYcVxPtdwCYyBb7ynVABZQuSyPkx5NFSMFTga9bgyqTsXkBWU"
ELEVEN_API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
ELEVEN_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Живой, нейтральный голос
PASSWORD = "1234"  # Пароль для очистки памяти

# ==== ⚙️ Переменные ====
history = [{"role": "system", "content": "Ты голосовой помощник по имени Джерри. Отвечай просто, с юмором, можно с чёрным."}]
JERRY_NAME = "джерри"
MEMORY_FILE = "jerry_memory.json"

# ==== 🧠 Загрузка/сохранение памяти ====
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f)

def load_memory():
    global history
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            history = json.load(f)

# ==== 🎤 Запись речи ====
def record_audio(filename, duration=5):
    subprocess.run(["arecord", "-D", "plughw:0,0", "-f", "cd", "-t", "wav", "-d", str(duration), "-r", "16000", filename],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==== 🧠 Распознавание речи через ElevenLabs STT ====
def speech_to_text(filename):
    with open(filename, "rb") as f:
        audio_data = f.read()
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
    }
    files = {
        "file": ("audio.wav", audio_data, "audio/wav")
    }
    params = {
        "model_id": "scribe_v1",
        "language_code": "ru",  # язык распознавания, поменяй если нужно
        "diarize": False,
        "tag_audio_events": False
    }
    response = requests.post(url, headers=headers, files=files, data=params)
    if response.status_code == 200:
        result = response.json()
        text = result.get("transcription", "").lower()
        return text
    else:
        print(f"[Ошибка распознавания]: {response.status_code} {response.text}")
        return ""

# ==== 🤖 Запрос к Grok ====
def ask_grok(prompt):
    history.append({"role": "user", "content": prompt})
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}"
        },
        json={
            "model": "grok-3-latest",
            "messages": history,
            "temperature": 0.7
        }
    )
    reply = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "assistant", "content": reply})
    save_memory()
    return reply

# ==== 🗣️ Озвучка через ElevenLabs ====
def speak(text):
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}",
        headers={
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.3, "similarity_boost": 0.7}
        }
    )
    with open("response.wav", "wb") as f:
        f.write(response.content)
    os.system("aplay -D plughw:0,0 response.wav")

# ==== 🧼 Очистка памяти ====
def clear_memory():
    global history
    history = [{"role": "system", "content": "Ты голосовой помощник по имени Джерри. Отвечай просто, с юмором."}]
    save_memory()
    
# ==== 🌀 Главный цикл ====
def main():
    print("🎤 Джерри слушает... Скажи 'Привет' для активации.")
    load_memory()

    while True:
        record_audio("input.wav", duration=2)
        text = speech_to_text("input.wav")
        print(f"[Распознано в ожидании]: {text}")
        if "привет" in text:
            speak("Слушаю")
            while True:
                record_audio("command.wav", duration=10)
                command = speech_to_text("command.wav")
                print(f"🗣 Ты сказал: {command}")

                if not command.strip():
                    speak("Поняла, ухожу в режим ожидания.")
                    break

                if "очисти память" in command:
                    speak("Назови пароль.")
                    record_audio("pass.wav", duration=5)
                    password = speech_to_text("pass.wav")
                    if PASSWORD in password:
                        clear_memory()
                        speak("Память очищена.")
                    else:
                        speak("Неверный пароль.")
                    continue

                answer = ask_grok(command)
                speak(answer)

                # Ожидаем ещё 15 сек. новую команду
                print("⏳ Ожидание команды 15 сек...")
                start = time.time()
                while time.time() - start < 15:
                    record_audio("check.wav", duration=2)
                    new_text = speech_to_text("check.wav")
                    if new_text.strip():
                        command = new_text
                        print(f"🗣 Повторная команда: {command}")
                        answer = ask_grok(command)
                        speak(answer)
                        start = time.time()
                    else:
                        continue

                speak("Поняла, ухожу в режим ожидания.")
                break

if __name__ == "__main__":
    main()
