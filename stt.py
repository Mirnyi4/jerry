import os
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs

# Укажи свой ключ напрямую
elevenlabs = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d",
)

# Запись звука через arecord (3 секунды)
print("🎤 Говори что-нибудь (3 секунды)...")
os.system("arecord -D plughw:0,0 -f cd -t wav -d 3 -r 16000 test.wav")

# Загрузка файла и отправка в ElevenLabs
with open("test.wav", "rb") as f:
    audio_data = BytesIO(f.read())

# Распознавание речи
print("🧠 Распознаю...")
transcription = elevenlabs.speech_to_text.convert(
    file=audio_data,
    model_id="scribe_v1",
    tag_audio_events=False,
    language_code="rus",  # Можно попробовать "None" или "eng"
    diarize=False
)

# Вывод результата
print("📝 Результат распознавания:")
print(transcription)
