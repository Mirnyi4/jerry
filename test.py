from elevenlabs import generate, play, set_api_key
import os

set_api_key("sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d")

# Генерация речи на русском
audio = generate(
    text="Привет! Я русский голосовой ассистент Джерри. Чем могу помочь?",
    voice="Dmitry",  # Русский голос
    model="eleven_multilingual_v2"
)

# Воспроизведение
play(audio)
