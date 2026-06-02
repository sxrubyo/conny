with open("conny_cli.py", "r") as f:
    cli_code = f.read()

# remove old dev_cmd
idx = cli_code.find("def cmd_dev_account(args):")
if idx != -1:
    idx2 = cli_code.find("ROUTES = {", idx)
    if idx2 != -1:
        cli_code = cli_code[:idx] + cli_code[idx2:]

dev_cmd = """
def cmd_dev_account(args):
    \"\"\"Crea una cuenta de desarrollador para la UI web.\"\"\"
    print("\\n══ Cuenta de Desarrollador (Web Dev Console) ══")
    import os, sqlite3, secrets, hashlib
    import getpass
    
    db_path = "/home/ubuntu/conny/conny_ultra.db"
    if not os.path.exists(db_path):
        db_path = "/home/ubuntu/conny/conny.db"
        
    email = input(f"  {q(C.CYN, 'Email del Dev:')} ").strip().lower()
    if not email: return
    password = getpass.getpass(f"  {q(C.CYN, 'Contraseña:')} ").strip()
    if not password: return
    
    try:
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000).hex()
        hashed = f"{salt}:{key}"
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS dev_accounts (email TEXT PRIMARY KEY, password_hash TEXT)")
        c.execute("INSERT OR REPLACE INTO dev_accounts (email, password_hash) VALUES (?, ?)", (email, hashed))
        conn.commit()
        conn.close()
        ok(f"Cuenta '{email}' creada con éxito.")
        info("Ya puedes entrar en la web mediante el botón 'API Access / Conny Dev'.")
    except Exception as e:
        fail(f"Error al crear cuenta localmente: {e}")

"""

cli_code = cli_code.replace("ROUTES = {", dev_cmd + "\nROUTES = {")

with open("conny_cli.py", "w") as f:
    f.write(cli_code)

