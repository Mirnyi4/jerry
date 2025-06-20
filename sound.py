import re
import subprocess
from youtubesearchpython import VideosSearch

def search_youtube(query):
    """Ищет первый трек на YouTube по запросу и возвращает его URL"""
    search = VideosSearch(query, limit=1)
    results = search.result().get("result")
    if results:
        video_id = results[0]['id']
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def play_audio_stream(url):
    """Проигрывает аудио из YouTube через mpv (без видео)"""
    print(f"▶ Воспроизвожу: {url}")
    subprocess.Popen(["mpv", "--no-video", url])

def play_song_by_voice_command(command):
    """Обработка голосовой команды, типа 'включи беливер'"""
    command = command.lower()
    match = re.search(r"включи\s+(.+)", command)
    if match:
        query = match.group(1).strip()
        print(f"🔍 Ищем: {query}")
        url = search_youtube(query)
        if url:
            play_audio_stream(url)
            return f"🎵 Воспроизводится: {query}"
        else:
            return "❌ Не удалось найти трек"
    return "❓ Команда не распознана"

# ▶ Тестовый запуск
if __name__ == "__main__":
    while True:
        command = input("🎤 Скажи команду: ")
        print("💬", play_song_by_voice_command(command))
