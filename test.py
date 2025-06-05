from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Подключаемся к ElevenLabs
client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

# Получаем поток речи (stream)
stream = client.text_to_speech(
    text="Привет, это Джерри. Говорю быстро и чётко!",
    voice="Dmitry",
    model="eleven_multilingual_v2",
    stream=True
)

# Проигрываем аудио
play(stream)
