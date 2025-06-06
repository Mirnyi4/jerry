import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
load_dotenv()
elevenlabs = ElevenLabs(
  api_key=os.getenv("sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"),
)
audio = elevenlabs.text_to_speech.convert(
    text="Привет, проверяем мою работу, йоу",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)
play(audio)
