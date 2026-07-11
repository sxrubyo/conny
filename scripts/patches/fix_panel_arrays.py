import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# remove lineChartData
content = re.sub(r'const lineChartData = \[.*?\];', '', content, flags=re.DOTALL)
# replace data={chartData.length > 0 ? chartData : lineChartData}
content = content.replace('data={chartData.length > 0 ? chartData : lineChartData}', 'data={chartData}')

with open(filename, 'w') as f:
    f.write(content)
