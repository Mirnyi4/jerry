import speech_recognition as sr
from gtts import gTTS
import os
import requests
import time

# 🔑 Твой API-ключ от x.ai (Grok)
GROK_API_KEY = "xai-uT9dB1qXXGWVidc9OpXacnjegjXwVWrjAye5o6M7N82QwW3fQL66YVjDkqMxmhfDgF280V3SKUdiA1AT"
GROK_API_URL = "https://x.ai/api/chat"

# 📦 История диалога (можно доработать, сейчас простая)
dialogue_history = []

# 📢 Функция озвучки
def speak(text):
    tts = gTTS(text, lang='ru')
    filename = f"voice_{int(time.time())}.mp3"
    tts.save(filename)
    os.system(f"mpg123 {filename}")
    os.remove(filename)

# 📥 Функция отправки текста в Grok
def ask_grok(prompt):
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    # Добавляем историю в запрос
    messages = [{"role": "system", "content": "Ты голосовой помощник по имени Джорджи"}]
    for item in dialogue_history:
        messages.append({"role": "user", "content": item["user"]})
        messages.append({"role": "assistant", "content": item["bot"]})

    messages.append({"role": "user", "content": prompt})

    data = {
        "messages": messages,
        "model": "grok-1"
    }

    response = requests.post(GROK_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        reply = response.json().get("message", {}).get("content", "Извини, я не понял.")
        dialogue_history.append({"user": prompt, "bot": reply})
        return reply
    else:
        return "Произошла ошибка при подключении к Grok."

# 🎤 Слушаем микрофон и обрабатываем команду
def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎧 Слушаю... Скажи 'Привет' для активации")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="ru-RU").lower()
        print("📢 Ты сказал:", text)
        return text
    except:
        return ""

# 🧠 Основной цикл
def main():
    while True:
        said = listen()
        if "Привет" in said:
            speak("Что?")
            print("🟢 Активировано")
            time.sleep(1)
            command = listen()
            if command:
                print("📨 Отправка в Grok:", command)
                response = ask_grok(command)
                print("🤖 Джорджи:", response)
                speak(response)

if __name__ == "__main__":
    main()
