from elevenlabs import ElevenLabs
import subprocess

API_KEY = "твой_ключ_сюда"

def say(text):
    client = ElevenLabs(api_key=API_KEY)
    voices = client.voices.list()
    print("Доступные голоса:", [v.name for v in voices])

    # Попытаемся взять голос "Rachel", если есть
    voice = next((v for v in voices if v.name == "Rachel"), None)
    if voice is None:
        voice = voices[0]  # если нет Rachel, берём первый доступный голос

    audio_stream = client.text_to_speech.speech(text=text, voice_id=voice.id)

    with open("output.mp3", "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    # Проигрываем через aplay на нужном устройстве
    subprocess.run(["aplay", "-D", "plughw:0,0", "output.mp3"])

if __name__ == "__main__":
    say("Привет, это тест ElevenLabs и воспроизведение через aplay на USB PnP Sound Device")
