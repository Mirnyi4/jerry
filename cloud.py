import requests
import subprocess

CLIENT_ID = "Sn8AX0Wf983GAa8Ai8tjRAIWgKk3S5fN"

def search_track(query):
    url = "https://api-v2.soundcloud.com/search/tracks"
    params = {
        'q': query,
        'client_id': CLIENT_ID,
        'limit': 1
    }

    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            print(f"❌ Ошибка запроса: {r.status_code} — {r.text}")
            return None
        data = r.json()
        if 'collection' not in data or not data['collection']:
            print("⚠️ Трек не найден или пустой ответ.")
            return None
        return data['collection'][0]
    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")
        return None


def get_real_stream_url(track):
    for transcoding in track['media']['transcodings']:
        protocol = transcoding['format']['protocol']
        url = transcoding['url']
        try:
            r = requests.get(url, params={'client_id': CLIENT_ID})
            stream_info = r.json()
            if 'url' in stream_info:
                print(f"🎵 Использую поток ({protocol}): {stream_info['url']}")
                return stream_info['url']
            else:
                print(f"⚠️ Нет 'url' в ответе на {protocol}: {stream_info}")
        except Exception as e:
            print(f"❌ Ошибка при получении потока {protocol}: {e}")
    return None

def play_track_by_name(name):
    track = search_track(name)
    if not track:
        print("❌ Трек не найден.")
        return

    print(f"▶ Воспроизвожу: {track['title']} — {track['user']['username']}")
    stream_url = get_real_stream_url(track)
    if not stream_url:
        print("❌ Не удалось получить прямую ссылку на аудио.")
        return

    subprocess.Popen([
        "mpv", "--no-video",
        "--audio-device=alsa/plughw:0,0",
        stream_url
    ])

def main():
    print("🎧 Введи название трека для воспроизведения (или 'выход'):")
    while True:
        query = input(">>> ").strip()
        if query.lower() in ['выход', 'exit', 'quit']:
            print("🚪 Выход.")
            break
        if query:
            play_track_by_name(query)

if __name__ == "__main__":
    main()
