import os
import time
import wave
import requests
import subprocess
from io import BytesIO
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from dotenv import load_dotenv

load_dotenv()

# 🔑 Ключи
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY") or "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
XAI_API_KEY = os.getenv("XAI_API_KEY") or "xai-Tknz2fMYxD6V3OqeopEf3ujUoQhblT0Hwe0kQ6mjLthOadiwA9CQ5avqFDvIdkTuGlNwKiDbqoqmGg4U"

# 🎙 Настройки
MIC_DEVICE = "plughw:0,0"
AUDIO_FILENAME = "input.wav"
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)
USER_NAME = "пользователь"
JERRY_NAME = "Джерри"
WAKE_WORD = "привет"
STATE = "sleep"
history = []

def speak(text):
    print(f"\n💬 Джерри: {text}")
    audio = elevenlabs.text_to_speech.convert(
        voice_id="D38z5RcWu1voky8WS1ja",  # можешь сменить на нужного
        model_id="eleven_monolingual_v1",  # либо другой доступный тебе
        text=text,
        output_format="mp3_44100_64",  # бесплатный формат, разрешённый без Pro
    )
    with open("output.mp3", "wb") as f:
        f.write(b"".join(audio))
    os.system("ffmpeg -hide_banner -loglevel error -i output.mp3 -f wav - | aplay -D plughw:0,0")

def record_audio(filename=AUDIO_FILENAME, duration=5):
    subprocess.run(["arecord", "-D", MIC_DEVICE, "-f", "cd", "-t", "wav", "-d", str(duration), "-r", "16000", filename],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio(filename=AUDIO_FILENAME):
    with open(filename, "rb") as f:
        transcription = elevenlabs.speech_to_text.convert(
            file=BytesIO(f.read()),
            model_id="scribe_v1",
            language_code="ru",  # русский
            diarize=False,
            tag_audio_events=False
        )
    return transcription.text or ""

def ask_grok(prompt):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}"
    }
    data = {
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7,
        "messages": history + [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": content})
    return content

def main_loop():
    global STATE
    print("🎤 Джерри слушает... Скажи 'Привет' для активации.")
    while True:
        record_audio(duration=3)
        text = transcribe_audio()
        if not text:
            continue

        if STATE == "sleep":
            if WAKE_WORD in text.lower():
                STATE = "active"
                speak("Слушаю.")
                print("🎙 Ожидаю команду...")
        elif STATE == "active":
            print(f"📥 Ты сказал: {text}")
            if "пока" in text.lower():
                speak("Поняла, ухожу в режим ожидания.")
                STATE = "sleep"
                continue
            try:
                response = ask_grok(text)
                speak(response)
            except Exception as e:
                speak("Произошла ошибка.")
                print(e)
            timeout = time.time() + 15
            while time.time() < timeout:
                record_audio(duration=3)
                followup = transcribe_audio()
                if followup.strip():
                    print(f"📥 Продолжение: {followup}")
                    try:
                        response = ask_grok(followup)
                        speak(response)
                        timeout = time.time() + 15
                    except Exception as e:
                        speak("Ошибка при ответе.")
                        print(e)
                else:
                    speak("Поняла, ухожу в режим ожидания.")
                    STATE = "sleep"
                    break

if __name__ == "__main__":
    main_loop()
