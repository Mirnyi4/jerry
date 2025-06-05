import subprocess
from elevenlabs import ElevenLabs, VoiceClient

API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"

client = ElevenLabs(api_key=API_KEY)
voice_client = VoiceClient(client)

def say(text, voice_name="Bella"):
    voices = voice_client.list_voices()
    voice = None
    for v in voices:
        if v.name == voice_name:
            voice = v
            break
    if not voice:
        print(f"Голос с именем '{voice_name}' не найден, использую первый доступный.")
        voice = voices[0]

    audio_gen = client.text_to_speech.convert(text=text, voice=voice)
    audio_bytes = b"".join(chunk for chunk in audio_gen)

    filename = "output.mp3"
    with open(filename, "wb") as f:
        f.write(audio_bytes)

    subprocess.run(["mpg123", "-a", "plughw:0,0", filename])

if __name__ == "__main__":
    say("Привет, это тест звука через ElevenLabs и mpg123 на устройстве USB PnP Sound Device.")
