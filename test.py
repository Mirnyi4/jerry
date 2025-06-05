def say(text):
    client = ElevenLabs(api_key=API_KEY)
    voices = client.voices.get_all()

    print("voices:", voices)  # Посмотри структуру

    # Если голос — кортеж, где имя на позиции 1
    print("Доступные голоса:", [v[1] for v in voices])

    # Выбираем голос по имени, например "Rachel"
    voice = next((v for v in voices if v[1] == "Rachel"), None)
    if voice is None:
        voice = voices[0]

    audio_stream = client.text_to_speech.speech(text=text, voice_id=voice[0])  # id в позиции 0

    with open("output.mp3", "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    subprocess.run(["aplay", "-D", "plughw:0,0", "output.mp3"])
