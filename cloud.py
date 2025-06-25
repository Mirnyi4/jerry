from yt_dlp import YoutubeDL
import subprocess

def play_soundcloud_search(query):
    search_url = f"scsearch:{query}"

    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,  # только первый результат
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_url, download=False)
            if 'entries' in info:
                track = info['entries'][0]
            else:
                track = info
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
            play_soundcloud_search(query)

if __name__ == "__main__":
    main()
