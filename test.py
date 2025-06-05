from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import simpleaudio as sa

client = ElevenLabs(
    api_key="sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
)

audio = client.generate(
    text="Ну что, поехали, мать его!",
    voice=Voice(
        voice_id="EXAVITQu4vr4xnSDxMaL",
        settings=VoiceSettings(stability=0.3, similarity_boost=0.8)
    ),
    model="eleven_multilingual_v2"
)

# Сохраняем и воспроизводим
with open("output.wav", "wb") as f:
    f.write(audio)

wave_obj = sa.WaveObject.from_wave_file("output.wav")
play_obj = wave_obj.play()
play_obj.wait_done()
