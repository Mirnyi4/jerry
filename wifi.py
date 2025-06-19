import subprocess

def list_networks():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], text=True)
        networks = [line for line in result.strip().split("\n") if line]
        return sorted(set(networks))
    except subprocess.CalledProcessError:
        return []

def get_current_connection():
    try:
        ssid = subprocess.check_output(["iwgetid", "-r"], text=True).strip()
        return ssid if ssid else None
    except Exception:
        return None

def connect_to_network(ssid, password):
    try:
        current = get_current_connection()
        if current == ssid:
            with open("wifi_log.txt", "w") as f:
                f.write(f"✅ Уже подключены к {ssid}")
            return True

        # Удаляем старое соединение с таким именем (если есть)
        subprocess.run(["nmcli", "con", "delete", ssid], stderr=subprocess.DEVNULL)

        # Подключаемся к Wi-Fi
        result = subprocess.run(
            ["nmcli", "dev", "wifi", "connect", ssid, "password", password],
            capture_output=True,
            text=True
        )

        with open("wifi_log.txt", "w") as f:
            f.write("STDOUT:\n" + result.stdout + "\n\nSTDERR:\n" + result.stderr)

        # Проверяем, подключились ли мы
        if "successfully activated" in result.stdout.lower() or get_current_connection() == ssid:
            return True

        return False

    except Exception as e:
        with open("wifi_log.txt", "w") as f:
            f.write("❌ Exception: " + str(e))
        return False

def disconnect():
    current = get_current_connection()
    if current:
        try:
            subprocess.run(["nmcli", "con", "down", "id", current], check=True)
        except subprocess.CalledProcessError:
            pass
