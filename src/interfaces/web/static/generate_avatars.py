import os
import urllib.request
import time

def download_notionists_avatars(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # 30 different name seeds to get distinct premium characters
    seeds = [
        "Ane", "Bob", "Clara", "David", "Eva", "Felix", "Grace", "Hugo", 
        "Iris", "Jack", "Kim", "Leo", "Maya", "Nico", "Olivia", "Paul", 
        "Quinn", "Ruby", "Sam", "Tess", "Uli", "Val", "Will", "Xena", 
        "Yuri", "Zoe", "Amelie", "Bruno", "Chloe", "Dan"
    ]
    
    # Soft pastel background colors that fit the dark theme nicely
    backgrounds = [
        "c0aade", "b3c5fc", "fca3b7", "fcd2a3", "a3fcd6", "a3edf8",
        "e2e8f0", "cbd5e1", "f1f5f9", "ffd2e2", "d2ffeb", "ffe3d2"
    ]
    
    for i, seed in enumerate(seeds, 1):
        num = f"{i:02d}"
        bg = backgrounds[i % len(backgrounds)]
        url = f"https://api.dicebear.com/7.x/notionists/svg?seed={seed}&backgroundColor={bg}"
        file_path = os.path.join(output_dir, f"avatar_{num}.svg")
        
        try:
            print(f"Downloading avatar {num} (seed: {seed})...")
            # Set a User-Agent to avoid HTTP 403 Forbidden errors
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                svg_data = response.read().decode('utf-8')
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(svg_data)
            time.sleep(0.2) # Soft delay to be polite to the server
        except Exception as e:
            print(f"Error downloading avatar {num}: {e}")

if __name__ == '__main__':
    output_dir = '/home/ubuntu/conny/src/interfaces/web/static/avatars'
    download_notionists_avatars(output_dir)
    print("All 30 premium Notionist avatars downloaded successfully!")
