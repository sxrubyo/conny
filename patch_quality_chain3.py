import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

for fpath in files_to_patch:
    with open(fpath, "r") as f:
        content = f.read()
    
    # We will search for _demo_llm_quality_chain specifically
    # And replace the end of the loop
    def end_replacer(match):
        return "if had_output and last_candidate:\n            return last_candidate, True\n        return None, False\n\n    def _demo_owner_last_resort("
        
    content = re.sub(r'(?:if had_output and last_candidate.*?return last_candidate, True\s+)?return None, had_output\n\n\s*def _demo_owner_last_resort\(', end_replacer, content, flags=re.DOTALL)
    
    # Let's ensure last_candidate is set in handler.py inside _demo_llm_quality_chain
    # But wait, looking at the code above:
    #             if candidate and candidate.strip():
    #                 had_output = True
    #                 last_candidate = candidate
    #                 if not validator(candidate):
    #                     return candidate, True
    # It already had `last_candidate = candidate`!
    
    with open(fpath, "w") as f:
        f.write(content)

