import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Загрузка переменных из .env
load_dotenv()

# Инициализация клиента
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Генерация аудио в MP3
audio = elevenlabs.text_to_speech.convert(
    text="Привет, хозяин! Говорит Джерри.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

# Сохраняем как MP3
with open("speech.mp3", "wb") as f:
    f.write(b"".join(audio))

# Конвертируем MP3 в WAV (если aplay не поддерживает mp3 напрямую)
os.system("ffmpeg -y -i speech.mp3 speech.wav")

# Воспроизводим через USB-звук
os.system("aplay -D plughw:0,0 speech.wav")
