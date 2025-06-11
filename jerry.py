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
XAI_API_KEY = os.getenv("XAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 🎙 Настройки
MIC_DEVICE = "plughw:0,0"
AUDIO_FILENAME = "input.wav"
elevenlabs = ElevenLabs(api_key=ELEVEN_API_KEY)
USER_NAME = "Владислав"
JERRY_NAME = "Джерри"
WAKE_WORD = "привет"
STATE = "sleep"
history = []

def speak(text):
    print(f"\n💬 Джерри: {text}")
    audio = elevenlabs.text_to_speech.convert(
        voice_id="Obuyk6KKzg9olSLPaCbl",
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="pcm_24000",  # формат raw PCM доступен с платной подпиской
    )

    with open("output.wav", "wb") as f:
        f.write(b"".join(audio))

    os.system("aplay -D plughw:0,0 -c 1 -f S16_LE -r 24000 output.wav")


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
    system_prompt = {
        "role": "system",
        "content": (
            "Ты голосовой помощник по имени Джерри. "
            "Отвечай кратко, понятно и как быдло, можешь использовать постоянно юмор какой-то. Избегай длинных объяснений."
        )
    }
    data = {
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7,
        "messages": [system_prompt] + history + [{"role": "user", "content": prompt}]
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
                    speak("Понял, ухожу в режим ожидания.")
                    STATE = "sleep"
                    break

if __name__ == "__main__":
    main_loop()
