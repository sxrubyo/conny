import re
with open("conny_cli.py", "r") as f:
    content = f.read()

new_cmd_config = """def cmd_config(args):
    \"\"\"Editar configuración ultra interactiva.\"\"\"
    name = getattr(args, 'name', '') or ''
    try:
        import conny_ultra_config
        conny_ultra_config.run_ultra_config(name)
    except Exception as e:
        error(f"Error abriendo Ultra Config: {e}")
"""

content = re.sub(r'def cmd_config\(args\):.*?(?=\ndef |\Z)', new_cmd_config, content, flags=re.DOTALL)

with open("conny_cli.py", "w") as f:
    f.write(content)
