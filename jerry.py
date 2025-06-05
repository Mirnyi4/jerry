import speech_recognition as sr
import time
import requests
import os
from elevenlabs import generate, play, set_api_key
from pydub import AudioSegment
from pydub.playback import play as play_audio
from io import BytesIO

# === Настройки API ===
GROK_API_KEY = "xai-zMjk4pJBgSuTmJIRvms8Op8OKM7WiBW1MTUAEtyRUoUCel3L9PqsB2Tib0AnXWro4BOB9V3dulo7OcUr"
ELEVEN_API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"

# === Инициализация ===
set_api_key(ELEVEN_API_KEY)
recognizer = sr.Recognizer()
microphone = sr.Microphone()
conversation_history = []
ASSISTANT_NAME = "Джерри"
ACTIVE = False
last_interaction_time = 0
TIMEOUT = 15

# === Grok ===
def ask_grok(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    data = {
        "messages": [{"role": "system", "content": "Ты помощник Джерри. Общайся как быдло, кратко, с юмором, иногда с чёрным юмором. Не будь вежливым."}] + conversation_history + [{"role": "user", "content": prompt}],
        "model": "grok-3-latest",
        "stream": False,
        "temperature": 0.7
    }
    try:
        response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ Ошибка Grok:", e)
        return "Что-то с мозгами... Попробуй ещё раз."

# === Голосовой ответ ===
def speak(text):
    try:
        audio = generate(
            text=text,
            voice="Antoni",  # Можно заменить на другой голос
            model="eleven_monolingual_v1"
        )
        play(audio)
    except Exception as e:
        print("❌ Ошибка озвучки:", e)

# === Распознавание речи ===
def listen():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            print("🎤 Слушаю...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio, language="ru-RU")
            print("🗣 Вы сказали:", text)
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print("❌ Ошибка подключения к Google Speech:", e)
            return None

# === Основной цикл ===
def main():
    global ACTIVE, last_interaction_time, conversation_history

    print(f"🤖 Джерри в режиме ожидания. Скажи 'Привет'...")

    while True:
        if not ACTIVE:
            text = listen()
            if text and "привет" in text:
                ACTIVE = True
                last_interaction_time = time.time()
                speak("Слушаю")
                continue
        else:
            # В активном режиме
            text = listen()
            now = time.time()

            if text:
                last_interaction_time = now

                if "очисти память" in text:
                    conversation_history = []
                    speak("Окей, всё забыто.")
                    continue

                conversation_history.append({"role": "user", "content": text})
                response = ask_grok(text)
                conversation_history.append({"role": "assistant", "content": response})
                print("🤖", response)
                speak(response)

            elif now - last_interaction_time > TIMEOUT:
                speak("Поняла, ухожу в режим ожидания")
                ACTIVE = False
                conversation_history = []
                print("🕓 Джерри вернулся в режим ожидания.")

# === Запуск ===
if __name__ == "__main__":
    main()
