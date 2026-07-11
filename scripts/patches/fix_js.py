with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

content = content.replace("if(text.charAt(i) === '\\' && text.charAt(i+1) === 'n') {", "if(text.charAt(i) === '\\\\' && text.charAt(i+1) === 'n') {")

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
