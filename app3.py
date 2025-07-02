import subprocess
import threading
import time
import socket
import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

CONFIG_PATH = "config.json"
STATE_FILE = "state.json"
SERVICE_PASSWORD = "325140"

AP_INTERFACE = "wlan0"
HOSTAPD_SERVICE = "hostapd"
WPA_SUPPLICANT_SERVICE = "wpa_supplicant"

app = Flask(__name__)
app.secret_key = "your_secret_key"

# --- Утилиты для управления сетью ---

def is_connected(host="8.8.8.8", port=53, timeout=3):
    """Проверяет доступ к интернету (пингуя Google DNS)."""
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False

def start_ap():
    """Запуск точки доступа."""
    print("Запускаем точку доступа...")
    subprocess.run(["sudo", "systemctl", "stop", WPA_SUPPLICANT_SERVICE])
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", AP_INTERFACE])
    subprocess.run(["sudo", "ip", "addr", "add", "192.168.4.1/24", "dev", AP_INTERFACE])
    subprocess.run(["sudo", "ip", "link", "set", AP_INTERFACE, "up"])
    subprocess.run(["sudo", "systemctl", "start", HOSTAPD_SERVICE])

def stop_ap():
    """Остановка точки доступа."""
    print("Останавливаем точку доступа...")
    subprocess.run(["sudo", "systemctl", "stop", HOSTAPD_SERVICE])
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", AP_INTERFACE])

def start_sta():
    """Запуск клиента Wi-Fi."""
    print("Запускаем Wi-Fi клиент (STA)...")
    subprocess.run(["sudo", "systemctl", "stop", HOSTAPD_SERVICE])
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", AP_INTERFACE])
    subprocess.run(["sudo", "systemctl", "start", WPA_SUPPLICANT_SERVICE])
    subprocess.run(["sudo", "ip", "link", "set", AP_INTERFACE, "up"])

def get_current_mode():
    """Определяем режим: AP или STA."""
    # Проверим, запущен ли hostapd
    result = subprocess.run(["systemctl", "is-active", HOSTAPD_SERVICE], capture_output=True, text=True)
    if result.stdout.strip() == "active":
        return "ap"
    else:
        return "sta"

# --- Фоновой менеджер Wi-Fi режима ---

def wifi_mode_manager():
    last_mode = None
    while True:
        connected = is_connected()
        current_mode = get_current_mode()

        if connected and current_mode != "sta":
            print("[Manager] Интернет доступен, переключаемся в режим клиента")
            stop_ap()
            start_sta()
            last_mode = "sta"
        elif not connected and current_mode != "ap":
            print("[Manager] Интернет недоступен, запускаем точку доступа")
            start_ap()
            last_mode = "ap"
        else:
            print(f"[Manager] Режим стабилен: {current_mode}, интернет доступен: {connected}")

        time.sleep(15)

def start_wifi_manager():
    t = threading.Thread(target=wifi_mode_manager, daemon=True)
    t.start()

# --- Конфигурация и состояние ---

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Ты голосовой помощник Jerry, отвечай кратко и понятно, без длинных объяснений",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def is_first_run():
    return not os.path.exists(STATE_FILE)

def mark_setup_complete(activation_key):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"setup": True, "activation_key": activation_key}, f)

def get_stored_key():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("activation_key")

# --- Flask маршруты ---

@app.before_first_request
def before_first_request():
    start_wifi_manager()

@app.route("/")
def start():
    if is_first_run():
        return redirect(url_for("intro"))
    return redirect(url_for("index"))

@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/wifi", methods=["GET", "POST"])
def setup_wifi():
    # Для примера список сетей получаем через systemctl или nmcli, здесь заглушка
    networks = ["HomeWiFi", "OfficeNet", "FreeWiFi"]
    current_connection = "Не подключен"
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")
        if not ssid or not password:
            flash("❌ Укажите сеть и пароль!")
            return redirect(url_for("setup_wifi"))
        # Тут нужно реализовать подключение к Wi-Fi через wpa_supplicant
        # Например, записать в /etc/wpa_supplicant/wpa_supplicant.conf и перезапустить службу
        # Для простоты делаем заглушку:
        flash(f"✅ Попытка подключения к {ssid} (не реализовано)")
        return redirect(url_for("activate_page"))
    return render_template("wifi_setup.html", current_connection=current_connection, networks=networks)

@app.route("/activate", methods=["GET", "POST"])
def activate_page():
    if request.method == "POST":
        key = request.form.get("activation_key", "").strip()
        # Здесь проверка ключа, заглушка:
        if key == "valid_key_example":
            mark_setup_complete(key)
            flash("✅ Ключ активации принят!")
            return redirect(url_for("activated"))
        else:
            flash("❌ Неверный ключ или срок действия истёк!")
            return redirect(url_for("activate_page"))
    return render_template("activation.html")

@app.route("/activated")
def activated():
    return render_template("activated.html")

@app.route("/main", methods=["GET", "POST"])
def index():
    stored_key = get_stored_key()
    if not stored_key:
        flash("❌ У вас нет доступа, пройдите активацию.")
        return redirect(url_for("activate_page"))
    config = load_config()
    if request.method == "POST":
        config["wake_word"] = request.form.get("wake_word", "").strip()
        config["style_prompt"] = request.form.get("style_prompt", "").strip()
        config["voice_id"] = request.form.get("voice_id", "").strip()
        save_config(config)
        flash("✅ Настройки сохранены!")
        return redirect(url_for("index"))
    return render_template("main.html", config=config)

# --- Запуск сервера ---

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
