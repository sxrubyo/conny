import re

files_to_patch = [
    "src/interfaces/web/demo_handler.py",
    "src/conny/demo/handler.py"
]

for fpath in files_to_patch:
    with open(fpath, "r") as f:
        content = f.read()
    
    # Let's replace the ending of _demo_llm_conv_quality_chain
    old_code = """        if had_output and last_candidate and not looks_fragmented_reply(last_candidate):
            candidate_norm = _normalize_conv_text(last_candidate)
            if len(candidate_norm.split()) >= 5 and not validator(last_candidate):
                return last_candidate, True
        return None, had_output"""
        
    new_code = """        # BUG FIX ARCHITECTURE: si el modelo generó algo, así no pase validaciones, se devuelve. NO FALLBACK.
        if had_output and last_candidate:
            return last_candidate, True
        return None, False"""
        
    if old_code in content:
        content = content.replace(old_code, new_code)
    else:
        print(f"Failed to find old code in {fpath}")
        
    with open(fpath, "w") as f:
        f.write(content)

