import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Загружаем .env
load_dotenv()

# Проверяем API ключ
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("❌ API ключ не найден! Проверь .env файл.")
    exit(1)

print("✅ API ключ загружен.")

try:
    elevenlabs = ElevenLabs(api_key=api_key)

    print("🛠 Генерация аудио...")
    audio = elevenlabs.text_to_speech.convert(
        text="Привет! Джерри снова в деле.",
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )

    print("🔊 Воспроизведение...")
    play(audio)
    print("✅ Готово.")

except Exception as e:
    print("❗Произошла ошибка:")
    print(e)
