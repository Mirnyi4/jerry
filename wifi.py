import subprocess

def list_networks():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "dev", "wifi"], text=True)
        networks = [line for line in result.strip().split("\n") if line]
        return sorted(set(networks))
    except subprocess.CalledProcessError:
        return []

def connect_to_network(ssid, password):
    try:
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)
    except subprocess.CalledProcessError:
        pass

def get_current_connection():
    try:
        result = subprocess.check_output(["nmcli", "-t", "-f", "ACTIVE,NAME", "con", "show", "--active"], text=True)
        for line in result.strip().split("\n"):
            if line.startswith("yes:"):
                return line.split(":")[1]
    except subprocess.CalledProcessError:
        pass
    return None
