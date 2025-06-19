
from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import wifi

CONFIG_PATH = "config.json"
STATE_FILE = "state.json"

app = Flask(__name__)
app.secret_key = "your_secret_key"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, можешь использовать постоянно юмор какой-то.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def is_first_run():
    return not os.path.exists(STATE_FILE)

def mark_setup_complete():
    with open(STATE_FILE, "w") as f:
        json.dump({"setup": True}, f)

@app.route("/")
def start():
    if is_first_run():
        return redirect(url_for("intro"))
    return redirect(url_for("index"))

@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/wifi", methods=["GET", "POST"])
def wifi_setup():
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")
        if not ssid or not password:
            flash("❌ Укажите сеть и пароль!")
            return redirect(url_for("wifi_setup"))
        success = wifi.connect_to_network(ssid, password)
        if success:
            flash("✅ Успешное подключение к сети!")
            return redirect(url_for("activation"))
        else:
            flash("❌ Ошибка подключения!")
    networks = wifi.list_networks()
    return render_template("wifi_setup.html", networks=networks)

@app.route("/activation", methods=["GET", "POST"])
def activation():
    if request.method == "POST":
        key = request.form.get("activation_key")
        if key and len(key.strip()) >= 5:
            mark_setup_complete()
            flash("🎉 Активация прошла успешно!")
            return redirect(url_for("index"))
        else:
            flash("❌ Неверный ключ!")
    return render_template("activation.html")

@app.route("/main", methods=["GET", "POST"])
def index():
    config = load_config()
    if request.method == "POST":
        config["wake_word"] = request.form.get("wake_word", "").strip()
        config["style_prompt"] = request.form.get("style_prompt", "").strip()
        config["voice_id"] = request.form.get("voice_id", "").strip()
        save_config(config)
        flash("✅ Настройки сохранены!")
        return redirect(url_for("index"))
    current_connection = wifi.get_current_connection()
    networks = wifi.list_networks()
    return render_template("index.html", config=config, current_connection=current_connection, networks=networks)

@app.route("/connect", methods=["POST"])
def connect():
    ssid = request.form.get("ssid")
    password = request.form.get("password")
    if not ssid or not password:
        flash("❌ Укажите сеть и пароль!")
        return redirect(url_for("index"))
    success = wifi.connect_to_network(ssid, password)
    if success:
        flash(f"✅ Подключено к {ssid}")
    else:
        flash(f"❌ Не удалось подключиться к {ssid}")
    return redirect(url_for("index"))

@app.route("/disconnect", methods=["POST"])
def disconnect():
    wifi.disconnect()
    flash("🔌 Wi-Fi отключён")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
