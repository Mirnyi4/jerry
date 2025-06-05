import asyncio
import websockets
import json
import base64
import sounddevice as sd
import numpy as np

API_KEY = "sk_cd7225a5b96a922efa4da311b752fdf96e70d009dca6a46d"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Можно поменять на русский (например, Дмитрий)

TEXT = "Привет, я Джерри. Сейчас будет стрим речи напрямую."

# Преобразуем base64 → аудио массив
def play_audio_chunk(b64_audio):
    wav_bytes = base64.b64decode(b64_audio)
    audio_data = np.frombuffer(wav_bytes, dtype=np.int16)
    sd.play(audio_data, samplerate=22050)
    sd.wait()

async def main():
    url = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    async with websockets.connect(
        url,
        extra_headers={"xi-api-key": API_KEY, "Accept": "application/json"},
    ) as ws:
        await ws.send(json.dumps({
            "text": TEXT,
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.75},
            "model_id": "eleven_multilingual_v2"
        }))

        while True:
            try:
                response = await ws.recv()
                if isinstance(response, bytes):
                    continue
                data = json.loads(response)
                if "audio" in data:
                    play_audio_chunk(data["audio"])
            except websockets.ConnectionClosed:
                break

asyncio.run(main())
