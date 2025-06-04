import requests

API_KEY = "xai-uT9dB1qXXGWVidc9OpXacnjegjXwVWrjAye5o6M7N82QwW3fQL66YVjDkqMxmhfDgF280V3SKUdiA1AT"
url = "https://api.x.ai/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "messages": [
        {"role": "user", "content": "Привет, что ты умеешь делать?"}
    ],
    "model": "grok-3-latest",
    "stream": False,
    "temperature": 0.7
}

response = requests.post(url, headers=headers, json=data)
print(response.json()["choices"][0]["message"]["content"])
