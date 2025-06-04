import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import time
import threading
import requests

WAKE_WORD = "привет"
GROK_API_KEY = "xai-zMjk4pJBgSuTmJIRvms8Op8OKM7WiBW1MTUAEtyRUoUCel3L9PqsB2Tib0AnXWro4BOB9V3dulo7OcUr"

recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    try:
        tts = gTTS(text=text, lang='ru')
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            tts.save(fp.name)
            os.system(f"mpg123 {fp.name}")
    except Exception as e:
        print(f"Ошибка синтеза речи: {e}")

def ask_grok(question: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    data = {
        "messages": [
            {
                "role": "system",
                "content": "Ты голосовой помощник на Raspberry Pi Zero 2 W. Отвечай понятно и кратко."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("Ошибка при запросе к Grok:", e)
        return "Извините, я не смог получить ответ."

def listen_for_command(timeout=15):
    with mic as source:
        print("🎤 Слушаю команду...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout)
            command = recognizer.recognize_google(audio, language="ru-RU")
            print(f"🗣 Команда: {command}")
            return command.lower()
        except sr.WaitTimeoutError:
            print("⌛ Время ожидания истекло.")
        except sr.UnknownValueError:
            print("🤷 Не понял речь.")
        except sr.RequestError as e:
            print(f"Ошибка сервиса распознавания: {e}")
        return None

def main_loop():
    while True:
        print("🎧 Ожидаю активацию... Скажите 'Привет'")
        command = listen_for_command(timeout=10)
        if command and WAKE_WORD in command:
            print("✅ Активация!")
            speak("Слушаю тебя")
            command = listen_for_command(timeout=15)
            if command:
                response = ask_grok(command)
                print("🤖 Ответ:", response)
                speak(response)
            else:
                speak("Я не услышал команды.")
        time.sleep(1)

if __name__ == "__main__":
    main_loop()
