import os

from_import = "from bublee.domain.prompts.human_writer import STYLE_GUIDELINES\n"

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if "STYLE_GUIDELINES" in content and "human_writer" in content:
        return # already patched

    new_content = content
    if filepath.endswith("prospect_pitch.py"):
        # return f"""Eres Bublee..."""
        new_content = new_content.replace(
            "QUÉ HACE BUBLEE", 
            "{STYLE_GUIDELINES}\n\nQUÉ HACE BUBLEE"
        )
    elif filepath.endswith("demo_handler.py"):
        # append after: system_prompt += """
        new_content = new_content.replace(
            "system_prompt += \"\"\"\n", 
            "system_prompt += \"\\n\\n\" + STYLE_GUIDELINES + \"\\n\\n\"\n            system_prompt += \"\"\"\n"
        )
        new_content = new_content.replace(
            "prompt = f\"\"\"Eres Bublee.", 
            "prompt = f\"\"\"Eres Bublee.\\n\\n{STYLE_GUIDELINES}"
        )
        new_content = new_content.replace(
            "sim_prompt = f\"\"\"Eres Bublee. Ya sabes que el negocio", 
            "sim_prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres Bublee. Ya sabes que el negocio"
        )
        new_content = new_content.replace(
            "demo_patient_prompt = \"\"\"Eres Bublee", 
            "demo_patient_prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres Bublee"
        )
    elif filepath.endswith("routes.py"):
        new_content = new_content.replace(
            "prompt = f\"\"\"Eres el coach de ventas", 
            "prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres el coach de ventas"
        )
        new_content = new_content.replace(
            "prompt = f\"\"\"Eres analista de agentes", 
            "prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres analista de agentes"
        )
    elif filepath.endswith("dashboard.py"):
        new_content = new_content.replace(
            "sys_prompt = f\"\"\"Eres Bublee, una empleada", 
            "sys_prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres Bublee, una empleada"
        )
    elif filepath.endswith("runtime.py"):
        new_content = new_content.replace(
            "prompt = f\"\"\"Eres un coach de ventas", 
            "prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres un coach de ventas"
        )
        new_content = new_content.replace(
            "system_prompt = f\"\"\"Eres {agent_name}.", 
            "system_prompt = f\"\"\"{STYLE_GUIDELINES}\\n\\nEres {agent_name}."
        )

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(from_import + new_content)
        print(f"Patched {filepath}")

patch_file("/home/ubuntu/bublee/src/domain/prompts/prospect_pitch.py")
patch_file("/home/ubuntu/bublee/src/interfaces/web/demo_handler.py")
patch_file("/home/ubuntu/bublee/src/interfaces/web/app.py")
patch_file("/home/ubuntu/bublee/src/bublee/demo/handler.py")
patch_file("/home/ubuntu/bublee/src/bublee/api/routes.py")
patch_file("/home/ubuntu/bublee/src/bublee/admin/dashboard.py")
patch_file("/home/ubuntu/bublee/src/core/runtime.py")
