import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r') as f:
    content = f.read()

# The naked HTML starts at `<div style="margin-bottom: 24px; background: #F3F4F6;`
# and ends at `</form>` before `<div id="onboarding-waitlist-view"` or `auth-mode-toggle-container`

# Let's just find the exact text and delete it
bad_html = """                    <div style="margin-bottom: 24px; background: #18181B !important; 
    border-color: #3F3F46 !important;; padding: 16px; border-radius: 8px; border: 1px solid #E5E7EB; text-align: center;">"""

# Actually, the background was modified by carbon patch!
# Let's use regex to remove everything from `<div style="margin-bottom: 24px; background:` to `</form>` right before `auth-mode-toggle-container`? No, let's just carefully slice.

# Find line indices
lines = content.split('\n')
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '<!-- TOGGLE ENTRE LOGIN Y SIGNUP AL FONDO -->' in line:
        start_idx = i
    if 'id="auth-mode-toggle-container"' in line:
        end_idx = i

if start_idx != -1 and end_idx != -1:
    # Look inside this range for the naked form
    print("Found toggle range:", start_idx, "to", end_idx)
    # Let's wipe everything between start_idx and end_idx EXCEPT empty lines
    lines_to_keep = lines[:start_idx+1] + lines[end_idx:]
    
    with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
        f.write('\n'.join(lines_to_keep))
    print("Cleaned naked HTML")
else:
    print("Could not find bounds")
    
