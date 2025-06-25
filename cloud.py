from yt_dlp import YoutubeDL
import subprocess

def get_audio_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']

def play_audio_url(url):
    # ffplay - легкий и быстрый плеер без видео
    subprocess.Popen(['ffplay', '-nodisp', '-autoexit', url])

if __name__ == "__main__":
    video_url = input("Введите YouTube URL или ключевые слова: ").strip()
    # Если надо, можно добавить поиск по ключевым словам через API, а сейчас вводим URL
    audio_url = get_audio_url(video_url)
    print("▶ Запускаю аудио поток...")
    play_audio_url(audio_url)
