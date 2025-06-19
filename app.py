from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import wifi  # wifi.py рядом

CONFIG_PATH = "config.json"

app = Flask(__name__)
app.secret_key = "your_secret_key"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "wake_word": "привет",
            "style_prompt": "Отвечай кратко, понятно и как быдло, можешь использовать постоянно юмор какой-то. Избегай длинных объяснений.",
            "voice_id": "Obuyk6KKzg9olSLPaCbl"
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    config = load_config()
    if request.method == "POST":
        config["wake_word"] = request.form.get("wake_word", "").strip()
        config["style_prompt"] = request.form.get("style_prompt", "").strip()
        config["voice_id"] = request.form.get("voice_id", "").strip()
        save_config(config)
        flash("✅ Настройки сохранены!")
        return redirect(url_for("index"))
    return render_template("index.html", config=config)

@app.route("/setup_wifi", methods=["GET", "POST"])
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
        else:
            flash(f"❌ Не удалось подключиться к {ssid}")
        return redirect(url_for("setup_wifi"))
    return render_template("wifi_setup.html", current_connection=current_connection, networks=networks)

@app.route("/activate", methods=["POST"])
def activate():
    key = request.form.get("activation_key", "").strip()
    # Логика проверки ключа — пока пропускаем
    if key == "правильный_ключ":  # заглушка, потом заменишь
        # Можно сохранить что-то в config или файле, что активация прошла
        flash("✅ Активация прошла успешно!")
        return redirect(url_for("index"))
    else:
        flash("❌ Неверный ключ активации!")
        return redirect(url_for("activate_page"))

@app.route("/activate_page")
def activate_page():
    return render_template("activate.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
