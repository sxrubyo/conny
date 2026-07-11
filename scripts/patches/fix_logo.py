with open('/home/ubuntu/bublee-landing/index.html', 'r') as f:
    lines = f.readlines()

out = []
skip_next = False
for line in lines:
    if skip_next:
        if "Bublee" in line.strip() and len(line.strip()) == 5:
            skip_next = False
            continue
        skip_next = False
    if '<img src="assets/isotype.png"' in line:
        skip_next = True
    out.append(line)

with open('/home/ubuntu/bublee-landing/index.html', 'w') as f:
    f.writelines(out)
