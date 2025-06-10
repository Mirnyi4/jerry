
# Вставь свой ключ (или используй переменную окружения)
API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"  # не вставляй сюда в код, используй .env

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
