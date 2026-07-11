import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# I replaced `{[...` with `(dashboardData || [...` 
# Let's replace `(dashboardData || [` with `{(dashboardData || [`
# And we need to add the closing brace `})` ? Wait!
# Let's replace `            ]).map((kpi, i) => (` with `            ]).map((kpi: any, i: number) => (`
# Let's just do an exact string replace.

old_str = """            (dashboardData || [
              { label: "Total Conversations", value: "-", growth: "0%", up: true },
              { label: "Messages Sent", value: "-", growth: "0%", up: true },
              { label: "Active Instances", value: "-", growth: "0%", up: true },
              { label: "Avg Response Time", value: "-", growth: "0%", up: true },
            ]).map"""

new_str = """            {(dashboardData || [
              { label: "Total Conversations", value: "-", growth: "0%", up: true },
              { label: "Messages Sent", value: "-", growth: "0%", up: true },
              { label: "Active Instances", value: "-", growth: "0%", up: true },
              { label: "Avg Response Time", value: "-", growth: "0%", up: true },
            ]).map"""

content = content.replace(old_str, new_str)

old_str2 = """              </div>
            ))}
          </div>"""

new_str2 = """              </div>
            ))}
          </div>"""
# Wait, I didn't remove the closing `}`! Because it was originally `] ).map( ... )}` and I replaced `{[ ... ]}`.
# So I just need to add the `{` before `(dashboardData`.

with open(filename, 'w') as f:
    f.write(content)
