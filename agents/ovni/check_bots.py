import urllib.request, json
tokens = {
    "OVNI": "8749260201:AAFzUPcSu3g1qpeYXoFr-hHoRa-5NfoUARY",
    "CLINICA": "8779529912:AAEO-UTbbiR4Y2-NPPc3AVikILoZcHc9EmQ",
}
for n, t in tokens.items():
    try:
        r = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{t}/getMe").read())
        u = r["result"]["username"]
        print(f"{n}: @{u} — ID: {r['result']['id']}")
    except Exception as e:
        print(f"{n}: ERROR {e}")
