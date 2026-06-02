import re

with open("conny_cli.py", "r") as f:
    cli_code = f.read()

dev_cmd = """
def cmd_dev_account(args):
    \"\"\"Crea una cuenta de desarrollador para la UI web.\"\"\"
    header("Cuenta de Desarrollador (Web Dev Console)")
    import os, json
    import urllib.request
    import getpass
    
    # Obtener master key de .env
    master_key = ""
    env_path = "/home/ubuntu/conny/.env"
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("MASTER_API_KEY="):
                    master_key = line.split("=", 1)[1].strip()
                    break
    
    if not master_key:
        fail("No se encontró MASTER_API_KEY en .env")
        return
        
    email = input(f"  {q(C.CYN, 'Email del Dev:')} ").strip().lower()
    if not email: return
    password = getpass.getpass(f"  {q(C.CYN, 'Contraseña:')} ").strip()
    if not password: return
    
    try:
        data = json.dumps({"email": email, "password": password, "dev_token": master_key}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8003/api/auth/dev-register", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            if res.get("ok"):
                ok(f"Cuenta '{email}' creada con éxito.")
                info("Ya puedes entrar en la web mediante el botón 'API Access / Conny Dev'.")
            else:
                fail(str(res))
    except Exception as e:
        fail(f"Error al conectar con la API: {e}")

"""

# Insert before ROUTES = {
cli_code = cli_code.replace("ROUTES = {", dev_cmd + "\nROUTES = {")

# Add to ROUTES
cli_code = cli_code.replace('"sync-web": cmd_sync_web,', '"sync-web": cmd_sync_web,\n    "dev-account": cmd_dev_account, "dev": cmd_dev_account,')

with open("conny_cli.py", "w") as f:
    f.write(cli_code)

