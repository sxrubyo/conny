import urllib.request
try:
    urllib.request.urlopen("http://localhost:8000/video-bg")
    print("Video route OK")
except Exception as e:
    print("Error:", e)
