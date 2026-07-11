with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

content = content.replace('<a href="#" class="btn btn-ghost">\n                    See how it works\n                </a>', '<a href="#sdk" class="btn btn-ghost">\n                    See how it works\n                </a>')

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
