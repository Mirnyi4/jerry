import speech_recognition as sr
import pyttsx3

r = sr.Recognizer()
engine = pyttsx3.init()

with sr.Microphone() as source:
    print("🎤 Говорите...")
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source)

try:
    text = r.recognize_google(audio, language="ru-RU")
    print("Вы сказали:", text)
    engine.say(f"Вы сказали: {text}")
    engine.runAndWait()
except sr.UnknownValueError:
    print("🤔 Не распознал речь")
    engine.say("Я вас не понял")
    engine.runAndWait()
except sr.RequestError as e:
    print(f"Ошибка сервиса: {e}")
