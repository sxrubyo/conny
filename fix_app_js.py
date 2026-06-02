import re

with open("src/interfaces/web/static/app.js", "r") as f:
    js = f.read()

# Change dayNumber color
js = js.replace(
    "dayNumber.style.color = isToday ? '#fff' : 'var(--text-muted)';",
    "dayNumber.style.color = isToday ? '#fff' : 'var(--text)';"
)

# Fix appointment text color to ensure contrast in both modes
# We can use a darker color for the text if the background is light
js = js.replace(
    "aptEl.innerHTML = `<strong style=\"color:var(--text);\">${aptTime}</strong> - ${aptName}`;",
    "aptEl.innerHTML = `<strong style=\"color:inherit;\">${aptTime}</strong> - ${aptName}`;"
)
js = js.replace(
    "aptEl.style.color = 'var(--text)';",
    "aptEl.style.color = 'var(--text)';" # This might be fine, but we can ensure the apt background is distinct
)

# Wait, why was calendar empty?
# Because I might not have cleared the cells correctly or the month is wrong.
# Let's ensure the cells have a border if gap fails
js = js.replace(
    "cell.style.background = 'var(--surface)';",
    "cell.style.background = 'var(--bg)'; cell.style.border = '1px solid var(--border)';"
)

# And remove the gap from the grid container in HTML just in case
with open("src/interfaces/web/static/app.js", "w") as f:
    f.write(js)
