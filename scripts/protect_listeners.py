import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'r') as f:
    js = f.read()

# For any variable.addEventListener(...) at the start of a line, wrap it
def wrap_listener(match):
    indent = match.group(1)
    var_name = match.group(2)
    rest = match.group(3)
    # Don't wrap document, window
    if var_name in ('document', 'window'):
        return match.group(0)
    return f"{indent}if ({var_name}) {{\n{indent}    {var_name}.addEventListener{rest}"

# We will just replace common variables manually
vars_to_protect = [
    'tabDevRegister', 'tabDevLogin', 'devLoginFormNew', 'devRegisterForm',
    'btnSwitchToDev', 'btnBackToAdmin', 'adminChatInputElem', 'adminChatFormElem',
    'chatSearch', 'chatSendForm', 'adminChatForm'
]

for var in vars_to_protect:
    js = re.sub(rf"^(\s*){var}\.addEventListener(\([^\)]+\)\s*=>\s*{{)", rf"\1if ({var}) {{\n\1    {var}.addEventListener\2", js, flags=re.MULTILINE)
    js = re.sub(rf"^(\s*){var}\.addEventListener(\([^\)]+\)\s*\{{)", rf"\1if ({var}) {{\n\1    {var}.addEventListener\2", js, flags=re.MULTILINE)

# Close the brackets for the ones we opened!
# Actually this is hard to do safely with regex. 
