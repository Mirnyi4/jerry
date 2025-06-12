from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)
SETTINGS_FILE = "settings.json"

def load_settings():
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    settings = load_settings()
    if request.method == "POST":
        settings["wake_word"] = request.form.get("wake_word", "привет")
        settings["system_prompt"] = request.form.get("system_prompt", settings["system_prompt"])
        save_settings(settings)
        return redirect(url_for("index"))
    return render_template("index.html", settings=settings)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
