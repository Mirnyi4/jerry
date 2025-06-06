import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем API-ключ из переменной окружения
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

# Генерация и воспроизведение речи
audio = elevenlabs.text_to_speech.convert(
    text="Привет, я Джерри. Сейчас проверяю работу голоса.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # Здесь твой нужный голос
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)

play(audio)
