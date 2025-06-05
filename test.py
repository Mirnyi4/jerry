import os
import simpleaudio as sa
from elevenlabs.client import ElevenLabs

# Установи свой API-ключ
api_key = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"

# Инициализация клиента ElevenLabs
client = ElevenLabs(api_key=api_key)

# Генерация аудио
audio = client.text_to_speech.convert(
    text="Ну что, поехали, мать его!",
    voice_id="EXAVITQu4vr4xnSDxMaL",  # Замените на нужный voice_id
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)

# Сохранение аудио в файл
with open("output.mp3", "wb") as f:
    f.write(audio)

# Воспроизведение аудио
wave_obj = sa.WaveObject.from_wave_file("output.mp3")
play_obj = wave_obj.play()
play_obj.wait_done()
