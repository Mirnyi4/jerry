from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Подключаемся к ElevenLabs с ключом
client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

# Генерация речи
audio = client.generate(
    text="Привет, это Джерри. Я снова в деле!",
    voice="Dmitry",
    model="eleven_multilingual_v2"
)

# Воспроизведение
play(audio)
