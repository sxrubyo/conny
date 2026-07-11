with open('/home/ubuntu/bublee/src/core/globals.py', 'r') as f:
    content = f.read()

import_statement = "from bublee.domain.prompts.human_writer import STYLE_GUIDELINES"
if import_statement not in content:
    content = import_statement + "\n" + content

# we need to append STYLE_GUIDELINES at the end of _v8_build_addon_inner
target = "lines.append(v9_build_humanization_block("
if "lines.append(STYLE_GUIDELINES)" not in content:
    replacement = "lines.append(STYLE_GUIDELINES)\n            " + target
    content = content.replace(target, replacement)

# if the replacement didn't work because of indentation or it wasn't there, we can do it before return
target2 = "return \"\\n\\n\".join(lines)"
if "lines.append(STYLE_GUIDELINES)" not in content:
    replacement2 = "lines.append(STYLE_GUIDELINES)\n    " + target2
    content = content.replace(target2, replacement2)

with open('/home/ubuntu/bublee/src/core/globals.py', 'w') as f:
    f.write(content)
