import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Загрузка переменных из .env
load_dotenv()

# Получение API-ключа из переменной окружения
API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not API_KEY:
    print("❌ Ключ ELEVENLABS_API_KEY не найден в .env")
    exit(1)

client = ElevenLabs(api_key=API_KEY)

print("🎙 Список доступных голосов:")
voices = client.voices.get_all()

for voice in voices.voices:
    print(f"- ID: {voice.voice_id}")
    print(f"  Имя: {voice.name}")
    print(f"  Категория: {voice.category}")  # free / premium / professional
    print(f"  Языки: {', '.join(voice.labels.get('language', []))}")
    print(f"  Бесплатный: {'✅' if voice.category == 'free' else '❌'}")
    print()
