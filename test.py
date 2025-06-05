from elevenlabs import ElevenLabs
import subprocess

API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"

def say(text):
    client = ElevenLabs(api_key=API_KEY)
    voices = client.voices.get_all()
    print("Доступные голоса:", [v.name for v in voices])

    voice = next((v for v in voices if v.name == "Rachel"), None)
    if voice is None:
        voice = voices[0]  # первый голос, если Rachel нет

    audio_stream = client.text_to_speech.speech(text=text, voice_id=voice.id)

    with open("output.mp3", "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    subprocess.run(["aplay", "-D", "plughw:0,0", "output.mp3"])

if __name__ == "__main__":
    say("Привет, это тест ElevenLabs и воспроизведение через aplay на USB PnP Sound Device")
