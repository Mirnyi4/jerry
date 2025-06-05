from elevenlabs.client import ElevenLabs
import simpleaudio as sa

client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

audio_stream = client.text_to_speech.convert(
    text="Ну что, поехали, мать его!",
    voice_id="EXAVITQu4vr4xnSDxMaL",
    model_id="eleven_multilingual_v2",
    output_format="pcm_44100"
)

# Собираем поток в байты
audio_bytes = b"".join(chunk for chunk in audio_stream)

# Сохраняем в файл
with open("output.wav", "wb") as f:
    f.write(audio_bytes)

# Воспроизведение
wave_obj = sa.WaveObject.from_wave_file("output.wav")
play_obj = wave_obj.play()
play_obj.wait_done()
