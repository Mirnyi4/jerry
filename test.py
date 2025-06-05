import asyncio
import simpleaudio as sa
from elevenlabs.client import ElevenLabs

api_key = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
client = ElevenLabs(api_key=api_key)

async def main():
    audio_stream = client.text_to_speech.convert(
        text="Ну что, поехали, мать его!",
        voice_id="EXAVITQu4vr4xnSDxMaL",
        model_id="eleven_multilingual_v2",
        output_format="pcm_44100"
    )

    audio_bytes = b"".join([chunk async for chunk in audio_stream])

    with open("output.wav", "wb") as f:
        f.write(audio_bytes)

    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

asyncio.run(main())
