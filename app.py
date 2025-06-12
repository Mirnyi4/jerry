from flask import Flask, render_template, request, redirect, url_for, flash
import json
import subprocess

app = Flask(__name__)
app.secret_key = "supersecretkey"  # нужно для flash сообщений

SETTINGS_FILE = "settings.json"

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        default = {
            "wake_word": "привет",
            "system_prompt": "Ты голосовой помощник по имени Джерри. Отвечай кратко...",
        }
        save_settings(default)
        return default

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_wifi_status():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        for line in lines:
            parts = line.split(":")
            if len(parts) == 4 and parts[1] == "wifi":
                return {
                    "device": parts[0],
                    "state": parts[2],
                    "connection": parts[3] if parts[3] != "--" else None,
                }
    except Exception as e:
        return {"device": None, "state": "unknown", "connection": None}

def connect_wifi(ssid, password):
    try:
        # Создаем подключение или обновляем пароль
        subprocess.run(
            ["nmcli", "device", "wifi", "connect", ssid, "password", password],
            check=True, capture_output=True, text=True,
        )
        return True, f"Подключено к {ssid}"
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def disconnect_wifi(device):
    try:
        subprocess.run(
            ["nmcli", "device", "disconnect", device],
            check=True, capture_output=True, text=True,
        )
        return True, "Wi-Fi отключен"
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

@app.route("/", methods=["GET", "POST"])
def index():
    settings = load_settings()
    wifi = get_wifi_status()

    if request.method == "POST":
        if "save_settings" in request.form:
            # Сохраняем настройки Джерри
            settings["wake_word"] = request.form.get("wake_word", settings["wake_word"])
            settings["system_prompt"] = request.form.get("system_prompt", settings["system_prompt"])
            save_settings(settings)
            flash("Настройки Джерри сохранены", "success")

        elif "connect_wifi" in request.form:
            ssid = request.form.get("ssid")
            password = request.form.get("password")
            if ssid and password:
                success, msg = connect_wifi(ssid, password)
                flash(msg, "success" if success else "error")
            else:
                flash("Введите SSID и пароль", "error")

        elif "disconnect_wifi" in request.form:
            if wifi["device"]:
                success, msg = disconnect_wifi(wifi["device"])
                flash(msg, "success" if success else "error")
            else:
                flash("Wi-Fi устройство не найдено", "error")

        return redirect(url_for("index"))

    return render_template("index.html", settings=settings, wifi=wifi)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
