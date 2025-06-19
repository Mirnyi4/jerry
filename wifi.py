import subprocess

def list_networks():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], text=True)
        networks = [line for line in result.strip().split("\n") if line]
        return sorted(set(networks))
    except subprocess.CalledProcessError:
        return []

def connect_to_network(ssid, password):
    try:
        # Проверка: уже подключены?
        current = get_current_connection()
        if current == ssid:
            with open("wifi_log.txt", "w") as f:
                f.write(f"✅ Уже подключены к {ssid}")
            return True

        # Удаляем старое соединение
        subprocess.run(["nmcli", "con", "delete", ssid], stderr=subprocess.DEVNULL)

        # Подключаемся
        result = subprocess.run(
            ["nmcli", "dev", "wifi", "connect", ssid, "password", password],
            capture_output=True,
            text=True
        )

        with open("wifi_log.txt", "w") as f:
            f.write("STDOUT:\n" + result.stdout + "\n\nSTDERR:\n" + result.stderr)

        # Проверка, подключены ли после попытки
        if "successfully activated" in result.stdout.lower() or get_current_connection() == ssid:
            return True

        return False

    except Exception as e:
        with open("wifi_log.txt", "w") as f:
            f.write("❌ Exception: " + str(e))
        return False

def get_current_connection():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "ACTIVE,SSID", "con", "show", "--active"], text=True)
        for line in result.strip().split("\n"):
            if line.startswith("yes:"):
                return line.split(":")[1]
    except subprocess.CalledProcessError:
        pass
    return None

def disconnect():
    current = get_current_connection()
    if current:
        try:
            subprocess.run(["nmcli", "con", "down", "id", current], check=True)
        except subprocess.CalledProcessError:
            pass
