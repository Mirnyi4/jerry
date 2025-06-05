import speech_recognition as sr
import time
import threading
import queue
import json
from elevenlabs import ElevenLabs, VoiceSettings
import requests

# === НАСТРОЙКИ === #
WAKE_WORD = "привет"
API_GROK_KEY = "xai-zMjk4pJBgSuTmJIRvms8Op8OKM7WiBW1MTUAEtyRUoUCel3L9PqsB2Tib0AnXWro4BOB9V3dulo7OcUr"
ELEVEN_API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
ELEVEN_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Можно заменить на другой голос

# === Состояние === #
chat_history = [
    {"role": "system", "content": "Ты голосовой ассистент Джерри. Общайся как быдло, кратко, с черным юмором и шути. Не извиняйся. Отвечай как человек с характером."}
]
is_listening = True
last_input_time = time.time()

# === Инициализация ElevenLabs === #
tts = ElevenLabs(api_key=ELEVEN_API_KEY)

# === Функция воспроизведения текста голосом === #
def say(text):
    audio = tts.generate(
        text=text,
        voice=ELEVEN_VOICE_ID,
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.75)
    )
    tts.play(audio)

# === Отправка сообщения в Grok (X.AI) === #
def send_to_grok(messages):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_GROK_KEY}"
    }
    data = {
        "messages": messages,
        "model": "grok-1",
        "temperature": 0.5
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Извини, с серверами Grok что-то не так."

# === Функция распознавания речи === #
def recognize_speech(recognizer, mic):
    with mic as source:
        print("🎧 Слушаю...")
        audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)
    try:
        text = recognizer.recognize_google(audio, language="ru-RU").lower()
        print(f"🗣 Ты сказал: {text}")
        return text
    except sr.UnknownValueError:
        print("🤖 Не понял")
        return ""
    except sr.RequestError:
        return "Ошибка подключения"

# === Главная логика === #
def assistant_loop():
    global chat_history, last_input_time
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    while True:
        text = recognize_speech(recognizer, mic)
        if WAKE_WORD in text:
            say("Слушаю")
            last_input_time = time.time()
            while True:
                user_text = recognize_speech(recognizer, mic)
                if not user_text:
                    if time.time() - last_input_time > 15:
                        say("Поняла, ухожу в режим ожидания.")
                        break
                    continue

                last_input_time = time.time()

                # Проверка на очистку памяти
                if "очисти память" in user_text:
                    chat_history = chat_history[:1]  # Сбросить до системного промта
                    say("Очистила всё к чертям")
                    continue

                chat_history.append({"role": "user", "content": user_text})
                bot_reply = send_to_grok(chat_history)
                chat_history.append({"role": "assistant", "content": bot_reply})
                say(bot_reply)

# === Запуск === #
if __name__ == "__main__":
    try:
        assistant_loop()
    except KeyboardInterrupt:
        print("Выключаюсь...")
