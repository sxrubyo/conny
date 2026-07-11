with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    content = f.read()

# Change the HTML structure for the H1
old_html = """Un Agente<br>
                <span class="text-accent-infinite">Infinitos</span> Clientes."""

new_html = """Un Agente<br>
                Clientes <span class="text-accent-infinite">Infinitos</span>."""

content = content.replace(old_html, new_html)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.write(content)
