import re

with open("src/interfaces/web/app.py", "r") as f:
    content = f.read()

# Endpoints to secure
endpoints = [
    r'@app\.get\("/appointments"\)',
    r'@app\.get\("/appointments/\{apt_id\}"\)',
    r'@app\.get\("/patients"\)',
    r'@app\.get\("/patients/\{chat_id\}"\)',
    r'@app\.get\("/conversations/\{chat_id\}"\)',
    r'@app\.get\("/metrics"\)',
    r'@app\.get\("/plugins"\)',
    r'@app\.get\("/config"\)',
    r'@app\.patch\("/config"\)',
    r'@app\.get\("/personality"\)',
    r'@app\.patch\("/personality"\)',
    r'@app\.get\("/tasks"\)',
    r'@app\.post\("/tasks"\)',
    r'@app\.get\("/export"\)',
    r'@app\.get\("/analytics/summary"\)',
    r'@app\.get\("/analytics/intents"\)',
    r'@app\.get\("/analytics/sentiment"\)',
    r'@app\.get\("/logs/improvements"\)',
    r'@app\.get\("/logs/errors"\)',
    r'@app\.get\("/feedback"\)',
    r'@app\.get\("/trust-rules"\)',
    r'@app\.post\("/trust-rules"\)',
    r'@app\.get\("/api/admins"\)'
]

def add_security(content, endpoint_regex):
    # Find the endpoint
    match = re.search(endpoint_regex + r'\nasync def ([a-zA-Z0-9_]+)\((.*?)\):', content)
    if not match:
        return content
    
    full_match = match.group(0)
    func_name = match.group(1)
    args = match.group(2)
    
    # Check if already secured
    body_start_idx = match.end()
    if "_verify_master_key" in content[body_start_idx:body_start_idx+150]:
        return content # Already secured
    
    # Add request: Request if missing
    new_args = args
    if "request: Request" not in args and "request" not in args:
        if args.strip() == "":
            new_args = "request: Request"
        else:
            new_args = "request: Request, " + args

    # Replacement
    secure_block = """
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")"""
    
    new_def = full_match.replace(f"({args})", f"({new_args})") + secure_block
    
    return content.replace(full_match, new_def)

for ep in endpoints:
    content = add_security(content, ep)

# Special cases where the arguments span multiple lines
def fix_multiline_endpoint(content, endpoint_str, func_name):
    idx = content.find(endpoint_str)
    if idx == -1: return content
    
    def_idx = content.find(f"async def {func_name}(", idx)
    colon_idx = content.find("):", def_idx)
    
    if def_idx == -1 or colon_idx == -1: return content
    
    # Check if already secured
    if "_verify_master_key" in content[colon_idx:colon_idx+150]:
        return content
        
    args_str = content[def_idx + len(f"async def {func_name}("):colon_idx]
    
    new_args = args_str
    if "request: Request" not in args_str and "request" not in args_str:
        if args_str.strip() == "":
            new_args = "request: Request"
        else:
            new_args = "request: Request, " + args_str
            
    secure_block = """):
    if not _verify_master_key(request):
        raise HTTPException(status_code=401, detail="No autorizado")"""
        
    content = content[:def_idx + len(f"async def {func_name}(")] + new_args + content[colon_idx:].replace("):", secure_block, 1)
    return content

content = fix_multiline_endpoint(content, '@app.get("/appointments")', "list_appointments")

with open("src/interfaces/web/app.py", "w") as f:
    f.write(content)

