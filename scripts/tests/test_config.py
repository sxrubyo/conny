import requests
res = requests.get('http://localhost:8003/config', headers={"X-Master-Key": "8432e72097f64c2340fc48920b16cb03da3378207a8f19942b528a43979c4ac2"})
print("Status:", res.status_code)
print("Response:", res.text)
