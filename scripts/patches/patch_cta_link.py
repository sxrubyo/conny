with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

content = content.replace('<a href="#" class="btn btn-primary">\n                    Get Started Free \&rarr;\n                </a>', '<a href="/app" class="btn btn-primary">\n                    Get Started Free \&rarr;\n                </a>')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
