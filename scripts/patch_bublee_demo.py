import os

from_import = "from bublee.domain.prompts.human_writer import STYLE_GUIDELINES\n"

filepath = "/home/ubuntu/bublee/src/bublee/demo/handler.py"

with open(filepath, 'r') as f:
    content = f.read()

if "STYLE_GUIDELINES" not in content:
    new_content = content
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
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(from_import + new_content)
        print(f"Patched {filepath}")
