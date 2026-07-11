import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'r') as f:
    content = f.read()

# 1. Hide left side
old_left = """.login-left-side {
    position: relative;
    width: 50%;
    height: 100%;
    background: linear-gradient(rgba(5, 5, 10, 0.75), rgba(0, 0, 5, 0.88)), url('/static/web.background.png') center center / cover no-repeat;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}"""
new_left = """.login-left-side {
    display: none !important;
}"""
content = content.replace(old_left, new_left)

# 2. Make right side 100% and centered
old_right = """.login-right-side {
    width: 50%;
    height: 100%;
    background-color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 40px;
    position: relative;
}"""
new_right = """.login-right-side {
    width: 100%;
    height: 100%;
    background-color: #F9FAFB; /* Clean light background like ChatGPT */
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 24px;
    position: relative;
}"""
if old_right in content:
    content = content.replace(old_right, new_right)
else:
    # If not found exactly, do a regex replace
    content = re.sub(r'\.login-right-side \{[^}]+\}', new_right, content)


# 3. Make login-form-wrapper look like a card
old_wrapper = """.login-form-wrapper {
    width: 100%;
    max-width: 440px;
    display: flex;
    flex-direction: column;
}"""
new_wrapper = """.login-form-wrapper {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    background: #FFFFFF;
    padding: 48px 40px;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.05);
}"""
if old_wrapper in content:
    content = content.replace(old_wrapper, new_wrapper)
else:
    content = re.sub(r'\.login-form-wrapper \{[^}]+\}', new_wrapper, content)


# 4. Show mobile header universally so logo appears
old_mobile_header = """.login-mobile-header {
    display: none;
    flex-direction: column;
    align-items: center;
    margin-bottom: 32px;
}"""
new_mobile_header = """.login-mobile-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 32px;
}"""
content = content.replace(old_mobile_header, new_mobile_header)

# Dark theme overrides for the new background and card
dark_overrides = """body.dark-theme .login-right-side {
    background-color: #05050A !important;
}

body.dark-theme .login-form-wrapper {
    background: #111116 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5) !important;
}"""

content += "\n" + dark_overrides

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.css', 'w') as f:
    f.write(content)
