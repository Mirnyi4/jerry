import os
import subprocess
from youtube_search import YoutubeSearch
import re

# 📁 Убедись, что ffmpeg установлен в системе и доступен через командную строку
# Убедись, что установлен yt-dlp:
# pip install yt-dlp youtube-search-python

def search_youtube(query):
    """Ищет первый трек на YouTube по запросу и возвращает его URL"""
    results = YoutubeSearch(query, max_results=1).to_dict()
    if not results:
        return None
    video_id = results[0]['id']
    return f"https://www.youtube.com/watch?v={video_id}"

def play_audio_stream(url):
    """Проигрывает аудио без скачивания через ffmpeg и mpv (или mpg123)"""
    print(f"▶ Воспроизвожу: {url}")
    subprocess.Popen([
        "mpv", "--no-video", url
    ])

def play_song_by_voice_command(command):
    """Основная логика обработки голосовой команды"""
    # Пример команды: "включи беливер"
    if "включи" in command.lower():
        match = re.search(r"включи (.+)", command.lower())
        if match:
            query = match.group(1)
            print(f"🔍 Ищем: {query}")
            url = search_youtube(query)
            if url:
                play_audio_stream(url)
                return f"Воспроизводится {query}"
            else:
                return "Не удалось найти трек"
    return "Команда не распознана"

# ▶ Пример использования
if __name__ == "__main__":
    while True:
        command = input("Скажи команду: ")
        response = play_song_by_voice_command(command)
        print("💬", response)
