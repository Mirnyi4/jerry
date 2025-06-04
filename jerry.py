import speech_recognition as sr
from gtts import gTTS
import os
import time
from datetime import datetime, timedelta

WAKE_WORD = "привет"
RESPONSE_TIMEOUT = 15

recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    tts = gTTS(text=text, lang="ru")
    tts.save("response.mp3")
    os.system("mpg123 -q response.mp3")
    os.remove("response.mp3")

def listen_for_command(timeout=None):
    with mic as source:
        if timeout:
            audio = recognizer.listen(source, timeout=timeout)
        else:
            audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio, language="ru-RU")
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Ошибка Google API: {e}")
        return ""

print("🎧 Жду слово активации...")

while True:
    command = listen_for_command()
    if WAKE_WORD in command:
        print("🟢 Активирован")
        speak("Что?")
        start_time = datetime.now()

        while True:
            time_passed = datetime.now() - start_time
            if time_passed > timedelta(seconds=RESPONSE_TIMEOUT):
                print("⏱ Время ожидания истекло.")
                break

            try:
                with mic as source:
                    print("🎙 Слушаю команду...")
                    audio = recognizer.listen(source, timeout=RESPONSE_TIMEOUT)
                message = recognizer.recognize_google(audio, language="ru-RU").lower()
                print(f"📥 Вы сказали: {message}")
                speak(f"Ты сказал: {message}")
                break
            except sr.WaitTimeoutError:
                print("⏱ Нет команды в течение 15 секунд.")
                break
            except sr.UnknownValueError:
                print("🙉 Не распознано.")
                speak("Я не понял.")
                break
