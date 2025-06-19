from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import wifi
from key_utils import is_key_valid  # Импорт функции проверки ключа

CONFIG_PATH = "config.json"
STATE_FILE = "state.json"

app = Flask(__name__)
app.secret_key = "your_secret_key"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Ты голосовой помощник Jerry, отвечай кратко и понятно, без длинных обьяснений",
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
    current_connection = wifi.get_current_connection()
    networks = wifi.list_networks()
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")
        if not ssid or not password:
            flash("❌ Укажите сеть и пароль!")
            return redirect(url_for("setup_wifi"))
        success = wifi.connect_to_network(ssid, password)
        if success:
            flash(f"✅ Подключено к {ssid}")
            return redirect(url_for("activate_page"))
        else:
            flash(f"❌ Не удалось подключиться к {ssid}")
            return redirect(url_for("setup_wifi"))
    return render_template("wifi_setup.html", current_connection=current_connection, networks=networks)

@app.route("/activate", methods=["GET", "POST"])
def activate_page():
    if request.method == "POST":
        key = request.form.get("activation_key", "").strip()
        if is_key_valid(key):
            mark_setup_complete(key)
            flash("✅ Ключ активации принят!")
            return redirect(url_for("index"))
        else:
            flash("❌ Неверный ключ или срок действия истёк!")
            return redirect(url_for("activate_page"))
    return render_template("activation.html")

@app.route("/main", methods=["GET", "POST"])
def index():
    stored_key = get_stored_key()
    if not stored_key or not is_key_valid(stored_key):
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
    return render_template("index.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
