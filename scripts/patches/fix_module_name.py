import os

files_to_fix = [
    "/home/ubuntu/bublee/src/domain/prompts/prospect_pitch.py",
    "/home/ubuntu/bublee/src/interfaces/web/demo_handler.py",
    "/home/ubuntu/bublee/src/bublee/demo/handler.py",
    "/home/ubuntu/bublee/src/bublee/api/routes.py",
    "/home/ubuntu/bublee/src/bublee/admin/dashboard.py",
    "/home/ubuntu/bublee/src/core/runtime.py",
    "/home/ubuntu/bublee/src/core/globals.py"
]

old_import = "from bublee.domain.prompts.human_writer import STYLE_GUIDELINES"
new_import = "from src.domain.prompts.human_writer import STYLE_GUIDELINES"

for filepath in files_to_fix:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if old_import in content:
            new_content = content.replace(old_import, new_import)
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
    except FileNotFoundError:
        pass
