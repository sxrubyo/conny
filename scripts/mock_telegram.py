import urllib.request
import json
import logging
import sys
import uuid
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_mock_message(port: int, secret: str, message_text: str):
    url = f"http://127.0.0.1:{port}/webhook/{secret}"
    update_id = int(time.time())
    
    payload = {
        "update_id": update_id,
        "message": {
            "message_id": 1,
            "from": {
                "id": 999999999,
                "is_bot": False,
                "first_name": "TestUser",
                "language_code": "es"
            },
            "chat": {
                "id": 999999999,
                "first_name": "TestUser",
                "type": "private"
            },
            "date": int(time.time()),
            "text": message_text
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method="POST", headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                logging.info(f"[✅] Sent '{message_text}' to Port {port}. Status: 200")
            else:
                logging.warning(f"[❌] Failed to send to Port {port}. Status: {response.status}")
    except Exception as e:
        logging.error(f"[❌] Error sending to Port {port}: {e}")

if __name__ == "__main__":
    instances = [
        {"name": "bublee_base", "port": 8003, "secret": "bublee_clinica-de-las-americas_2ed44661cb56cd55"},
        {"name": "melissa_x", "port": 8006, "secret": "bublee_melissa-x_019d2bbd1d0b135b"},
        {"name": "ovni", "port": 8008, "secret": "bublee_ovni_019d2bbd1d0b135b"}
    ]
    for inst in instances:
        logging.info(f"Testing {inst['name']}...")
        send_mock_message(inst["port"], inst["secret"], "Hola, ¿tienen disponibilidad para mañana?")
        time.sleep(1)

