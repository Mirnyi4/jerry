from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Укажи свой API-ключ
client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

# Получаем голосовой поток через метод .generate()
stream = client.generate(
    text="Привет, это Джерри. Я говорю быстро и чётко.",
    voice="Dmitry",  # Можно указать другой голос, если хочешь
    model="eleven_multilingual_v2",
    stream=True
)

# Воспроизвести голос
play(stream)
