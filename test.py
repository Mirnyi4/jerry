from elevenlabs import text_to_speech, play, set_api_key

# Устанавливаем ключ (твой сохранён)
set_api_key("sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d")

# Синтезируем фразу на русском языке
audio = text_to_speech(
    text="Привет! Я Джерри, твой голосовой ассистент. Чем могу помочь?",
    voice="Dmitry",  # Поддерживает русский
    model="eleven_multilingual_v2"
)

# Проигрываем результат
play(audio)
