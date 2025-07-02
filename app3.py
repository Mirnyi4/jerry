import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import subprocess

from key_utils import is_key_valid

CONFIG_PATH = "config.json"
STATE_FILE = "state.json"
SERVICE_PASSWORD = "325140"
AP_SCRIPT = "./start_ap.sh"  # Скрипт запуска точки доступа
ENV_FILE = ".env"  # Файл с переменными окружения для ключей API

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


def get_current_connection():
    try:
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            timeout=3
        )
        ssid = result.stdout.strip()
        return ssid if ssid else None
    except Exception:
        return None


def list_networks():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.splitlines()
        networks = list(sorted(set(filter(None, lines))))
        return networks
    except Exception:
        return []


def check_internet():
    try:
        res = subprocess.run(["ping", "-c", "1", "-W", "2", "8.8.8.8"], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False


def start_access_point():
    if os.path.exists(AP_SCRIPT):
        subprocess.Popen([AP_SCRIPT])
        return True
    return False


@app.before_first_request
def startup_checks():
    if not check_internet():
        start_access_point()


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
    current_connection = get_current_connection()
    networks = list_networks()

    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")
        if not ssid or not password:
            flash("❌ Укажите сеть и пароль!")
            return redirect(url_for("setup_wifi"))

        try:
            connect_cmd = ["nmcli", "device", "wifi", "connect", ssid, "password", password]
            result = subprocess.run(connect_cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                flash(f"✅ Подключено к {ssid}")
                return redirect(url_for("activate_page"))
            else:
                flash(f"❌ Не удалось подключиться к {ssid}. Ошибка: {result.stderr.strip()}")
                return redirect(url_for("setup_wifi"))

        except Exception as e:
            flash(f"❌ Ошибка при подключении: {str(e)}")
            return redirect(url_for("setup_wifi"))

    return render_template("wifi_setup.html", current_connection=current_connection, networks=networks)


@app.route("/activate", methods=["GET", "POST"])
def activate_page():
    if request.method == "POST":
        key = request.form.get("activation_key", "").strip()
        if is_key_valid(key):
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


@app.route("/start_jerry3", methods=["POST"])
def start_jerry3():
    subprocess.Popen(["python3", "jerry3.py"])
    return jsonify({"status": "started"})


@app.route("/main", methods=["GET", "POST"])
def index():
    stored_key = get_stored_key()
    if not stored_key or not is_key_valid(stored_key):
        flash("❌ У вас нет доступа, пройдите активацию.")
        return redirect(url_for("activate_page"))

    config = load_config()

    if request.method == "POST":
        if "shutdown" in request.form:
            subprocess.Popen(["sudo", "shutdown", "now"])
            flash("💀 Система выключается...")
            return redirect(url_for("index"))

        config["wake_word"] = request.form.get("wake_word", "").strip()
        config["style_prompt"] = request.form.get("style_prompt", "").strip()
        config["voice_id"] = request.form.get("voice_id", "").strip()
        save_config(config)
        flash("✅ Настройки сохранены!")
        return redirect(url_for("index"))

    return render_template("main.html", config=config)


@app.route("/service/reset_telegram", methods=["POST"])
def reset_telegram():
    data = request.get_json()
    if not data or data.get("password") != SERVICE_PASSWORD:
        return jsonify({"message": "Неверный пароль"}), 403
    try:
        if os.path.exists("session_jerry"):
            os.remove("session_jerry")
            return jsonify({"message": "Файл session_jerry удалён успешно."})
        else:
            return jsonify({"message": "Файл session_jerry не найден."})
    except Exception as e:
        return jsonify({"message": f"Ошибка: {str(e)}"}), 500


@app.route("/service/reset_settings", methods=["POST"])
def reset_settings():
    data = request.get_json()
    if not data or data.get("password") != SERVICE_PASSWORD:
        return jsonify({"message": "Неверный пароль"}), 403
    try:
        if os.path.exists("state.json"):
            os.remove("state.json")
            return jsonify({"message": "Файл state.json удалён успешно."})
        else:
            return jsonify({"message": "Файл state.json не найден."})
    except Exception as e:
        return jsonify({"message": f"Ошибка: {str(e)}"}), 500


@app.route("/service/edit_env", methods=["GET", "POST"])
def service_edit_env():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password != SERVICE_PASSWORD:
            flash("❌ Неверный пароль!")
            return redirect(url_for("service_edit_env"))

        env_text = request.form.get("env_text", "")
        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(env_text)
            flash("✅ Файл .env успешно сохранён!")
        except Exception as e:
            flash(f"❌ Ошибка при сохранении файла .env: {str(e)}")
        return redirect(url_for("service_edit_env"))

    # GET
    try:
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                env_text = f.read()
        else:
            env_text = ""
    except Exception:
        env_text = ""

    return render_template("service_edit_env.html", env_text=env_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
