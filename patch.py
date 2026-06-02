with open("src/conny/demo/handler.py", "r") as f:
    lines = f.readlines()
with open("src/conny/demo/handler.py", "w") as f:
    for i, line in enumerate(lines):
        if "if not response:" in line and "response = _lang_text" in lines[i+1]:
            f.write(line)
            f.write(lines[i+1])
            continue
        if "response = _lang_text" in line and "#" in line:
            pass # written above
        elif i == 1246 and ")" in line.strip():
            pass # delete this
        else:
            f.write(line)
