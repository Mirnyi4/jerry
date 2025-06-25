import requests
import subprocess

API_KEY = "AIzaSyApjrQYIwA2Slnn4i7ibiPhd7LH8634kvg"

def search_youtube(query):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'key': API_KEY,
        'maxResults': 1,
        'type': 'video',
    }
    response = requests.get(search_url, params=params)
    print("DEBUG: status_code =", response.status_code)
    print("DEBUG: response =", response.text)
    if response.status_code != 200:
        print("❌ Ошибка API:", response.status_code)
        return None
    data = response.json()
    items = data.get('items')
    if not items:
        return None
    video_id = items[0]['id']['videoId']
    title = items[0]['snippet']['title']
    return video_id, title


def play_youtube_video(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"▶ Воспроизвожу: {title}")
    subprocess.Popen([
        "mpv", "--no-video", url
    ])

def main():
    print("🎧 Введи ключевые слова для поиска трека (или 'выход'):")
    while True:
        query = input(">>> ").strip()
        if query.lower() in ['выход', 'exit', 'quit']:
            print("🚪 Выход.")
            break
        if query:
            result = search_youtube(query)
            if result:
                video_id, title = result
                play_youtube_video(video_id, title)
            else:
                print("❌ Видео не найдено.")

if __name__ == "__main__":
    main()
