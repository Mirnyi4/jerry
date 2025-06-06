import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Загружаем ключ из .env
load_dotenv()

# Инициализируем клиент
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Генерируем аудиофайл
audio = elevenlabs.text_to_speech.convert(
    text="Привет, хозяин! Говорит Джерри.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="pcm_44100",
)

# Сохраняем как WAV-файл
with open("speech.wav", "wb") as f:
    f.write(b"".join(audio))

# Воспроизводим через USB-звук
os.system("aplay -D plughw:0,0 speech.wav")
