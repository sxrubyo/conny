with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    lines = f.readlines()

out = []
in_right_side = False
in_left_side = False
in_wrapper = False
in_mobile_header = False

for line in lines:
    if line.startswith(".login-left-side {"):
        out.append(".login-left-side {\n    display: none !important;\n}\n")
        in_left_side = True
        continue
    if in_left_side:
        if line.strip() == "}":
            in_left_side = False
        continue

    if line.startswith(".login-right-side {"):
        out.append(".login-right-side {\n    width: 100%;\n    height: 100%;\n    background-color: #F9FAFB;\n    display: flex;\n    align-items: center;\n    justify-content: center;\n    padding: 0 24px;\n    position: relative;\n}\n")
        in_right_side = True
        continue
    if in_right_side:
        if line.strip() == "}":
            in_right_side = False
        continue

    if line.startswith(".login-form-wrapper {"):
        out.append(".login-form-wrapper {\n    width: 100%;\n    max-width: 400px;\n    display: flex;\n    flex-direction: column;\n    background: #FFFFFF;\n    padding: 48px 40px;\n    border-radius: 12px;\n    box-shadow: 0 8px 30px rgba(0,0,0,0.04);\n    border: 1px solid rgba(0,0,0,0.05);\n}\n")
        in_wrapper = True
        continue
    if in_wrapper:
        if line.strip() == "}":
            in_wrapper = False
        continue

    if line.startswith(".login-mobile-header {"):
        out.append(".login-mobile-header {\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n    margin-bottom: 32px;\n}\n")
        in_mobile_header = True
        continue
    if in_mobile_header:
        if line.strip() == "}":
            in_mobile_header = False
        continue
        
    out.append(line)

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.writelines(out)

