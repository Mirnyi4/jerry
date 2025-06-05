from elevenlabs.client import ElevenLabs
import simpleaudio as sa
import tempfile

client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

audio_stream = client.text_to_speech.convert(
    text="Ну что, поехали, мать его!",
    voice_id="EXAVITQu4vr4xnSDxMaL",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)

# Сохраняем во временный MP3-файл
with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
    for chunk in audio_stream:
        f.write(chunk)
    mp3_path = f.name

# Проигрываем с помощью mpg123 (если установлен)
import subprocess
subprocess.run(["mpg123", mp3_path])
