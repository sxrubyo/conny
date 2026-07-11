import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("agent_tester")

INSTANCES = {
    "bublee_base": 8003,
    "melissa_x": 8006,
    "ovni": 8008
}

def ping_agent(name: str, port: int) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                log.info(f"[✅] {name} (Port {port}) is ONLINE. Status: {data.get('status')}")
                return True
            else:
                log.warning(f"[❌] {name} (Port {port}) returned status {response.status}")
                return False
    except Exception as e:
        log.error(f"[❌] {name} (Port {port}) FAILED: {e}")
        return False

def main():
    log.info("Starting Agent Health Check...")
    results = [ping_agent(name, port) for name, port in INSTANCES.items()]
    if all(results):
        log.info("All agents are connected and online.")
    else:
        log.warning("Some agents failed the health check.")

if __name__ == "__main__":
    main()
