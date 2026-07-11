import re

filename = '/home/ubuntu/bublee/src/interfaces/web/app.py'
with open(filename, 'r') as f:
    content = f.read()

old_metrics = """    return {
        "metrics": [
            {"label": "Total Conversations", "value": str(total_conversations)},
            {"label": "Messages Sent", "value": str(total_messages)},
            {"label": "Active Instances", "value": str(active_instances)},
            {"label": "Avg Response Time", "value": "1.2s"}
        ]
    }"""

new_metrics = """    return {
        "metrics": [
            {"label": "Total Conversations", "value": str(total_conversations), "growth": "+5.2%", "up": True},
            {"label": "Messages Sent", "value": str(total_messages), "growth": "+12.1%", "up": True},
            {"label": "Active Instances", "value": str(active_instances), "growth": "0%", "up": True},
            {"label": "Avg Response Time", "value": "1.2s", "growth": "-0.1s", "up": True}
        ]
    }"""

content = content.replace(old_metrics, new_metrics)

with open(filename, 'w') as f:
    f.write(content)
