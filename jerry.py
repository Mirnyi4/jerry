import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io
import requests
import time

GROK_API_KEY = "xai-zMjk4pJBgSuTmJIRvms8Op8OKM7WiBW1MTUAEtyRUoUCel3L9PqsB2Tib0AnXWro4BOB9V3dulo7OcUr"

recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    tts = gTTS(text=text, lang='ru')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio = AudioSegment.from_file(fp, format="mp3")
    play(audio)

def ask_grok(question):
    url = "https://x.ai/api/chat"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": question}],
        "model": "grok-1"
    }
    response = requests.post(url, json=data, headers=headers)
    if response.ok:
        return response.json()['choices'][0]['message']['content']
    else:
        return "Извините, я не смог получить ответ."

def listen_for_keyword(keyword="привет"):
    print("🎧 В режиме ожидания. Скажите 'Привет'")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, phrase_time_limit=4)
    try:
        text = recognizer.recognize_google(audio, language="ru-RU").lower()
        return keyword in text
    except:
        return False

def listen_command(timeout=15):
    print("🎤 Ожидаю команду 15 секунд...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
    try:
        return recognizer.recognize_google(audio, language="ru-RU")
    except:
        return None

while True:
    if listen_for_keyword("привет"):
        print("✅ Ключевое слово обнаружено!")
        speak("Слушаю")
        try:
            command = listen_command(timeout=15)
            if command:
                print(f"📥 Команда: {command}")
                response = ask_grok(command)
                print(f"🤖 Ответ: {response}")
                speak(response)
            else:
                print("⏱ Время ожидания истекло")
        except sr.WaitTimeoutError:
            print("⏳ Никто не говорил. Возврат в ожидание.")
