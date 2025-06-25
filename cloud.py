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
    r = requests.get(url, params=params)
    data = r.json()
    return data['collection'][0] if data['collection'] else None

def get_stream_url(track_id):
    return f"https://api.soundcloud.com/tracks/{track_id}/stream?client_id={CLIENT_ID}"

def play_track_by_name(name):
    track = search_track(name)
    if not track:
        print("❌ Не найдено.")
        return
    print(f"▶ Воспроизвожу: {track['title']} — {track['user']['username']}")
    stream_url = get_stream_url(track['id'])
    subprocess.Popen([
        "mpv", "--no-video",
        "--audio-device=alsa/plughw:0,0",
        stream_url
    ])

# 🔁 Цикл ожидания команд из консоли
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
