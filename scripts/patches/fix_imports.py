import os

files_to_fix = [
    "/home/ubuntu/bublee/src/domain/prompts/prospect_pitch.py",
    "/home/ubuntu/bublee/src/interfaces/web/demo_handler.py",
    "/home/ubuntu/bublee/src/bublee/demo/handler.py",
    "/home/ubuntu/bublee/src/bublee/api/routes.py",
    "/home/ubuntu/bublee/src/bublee/admin/dashboard.py",
    "/home/ubuntu/bublee/src/core/runtime.py"
]

import_stmt = "from bublee.domain.prompts.human_writer import STYLE_GUIDELINES"

for filepath in files_to_fix:
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    has_import = False
    import_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == import_stmt:
            has_import = True
            import_idx = i
            break
            
    if not has_import:
        continue
        
    # remove the import
    lines.pop(import_idx)
    
    # find where to insert it: after from __future__
    insert_idx = 0
    for i, line in enumerate(lines):
        if "from __future__" in line:
            insert_idx = i + 1
            break
            
    # if no from __future__, try to insert after docstring or utf-8
    if insert_idx == 0:
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') and i > 0:
                insert_idx = i + 1
                break
                
    lines.insert(insert_idx, import_stmt + "\n")
    
    with open(filepath, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {filepath}")
