from yt_dlp import YoutubeDL
import subprocess

def play_youtube_search(query):
    search_url = f"ytsearch:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_url, download=False)
            track = info['entries'][0]
            print(f"▶ Воспроизвожу: {track['title']} — {track['uploader']}")
            stream_url = track['url']

            subprocess.Popen([
                "mpv", "--no-video",
                stream_url
            ])
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    print("🎧 Введи ключевые слова для поиска трека (или 'выход'):")
    while True:
        query = input(">>> ").strip()
        if query.lower() in ['выход', 'exit', 'quit']:
            print("🚪 Выход.")
            break
        if query:
            play_youtube_search(query)

if __name__ == "__main__":
    main()
