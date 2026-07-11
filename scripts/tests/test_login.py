import requests
res = requests.post('http://localhost:8003/api/auth/login', json={"email": "santi21435@gmail.com", "password": "Bichosiuu721@"})
print("Status:", res.status_code)
print("Response:", res.text)
