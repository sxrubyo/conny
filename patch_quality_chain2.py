import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

for fpath in files_to_patch:
    with open(fpath, "r") as f:
        content = f.read()
    
    # Let's fix the logic directly via regex
    # In both, there is:
    #             if candidate and candidate.strip():
    #                 had_output = True
    #                 last_candidate = candidate (only in demo_handler)
    #                 if not validator(candidate):
    #                     return candidate, True
    
    # Let's inject last_candidate = candidate in both
    def replacer(match):
        return "if candidate and candidate.strip():\n                had_output = True\n                last_candidate = candidate\n                if not validator(candidate):\n                    return candidate, True"
        
    content = re.sub(r'if candidate and candidate\.strip\(\):\s+had_output = True\s+(?:last_candidate = candidate\s+)?if not validator\(candidate\):\s+return candidate, True', replacer, content)
    
    # And at the end of the loop:
    # replace everything until `return None, had_output`
    # with `if had_output and last_candidate: return last_candidate, True\n        return None, False`
    def end_replacer(match):
        return "if had_output and last_candidate:\n            return last_candidate, True\n        return None, False\n\n    def _save("
        
    content = re.sub(r'(?:if had_output and last_candidate.*?return last_candidate, True\s+)?return None, had_output\n\n\s*def _save\(', end_replacer, content, flags=re.DOTALL)
    
    with open(fpath, "w") as f:
        f.write(content)

