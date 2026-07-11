import json

with open("/home/ubuntu/.gemini/antigravity-cli/brain/d4b57b0a-7144-48e5-9630-7e2af3a48e9d/.system_generated/logs/transcript.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_REQUEST":
            content = data.get("content", "")
            if "arreglalo, el de devs era este" in content:
                print("FOUND!")
                start = content.find("```tsx\\nsign-in.tsx")
                if start == -1:
                    start = content.find("```tsx\nsign-in.tsx")
                if start != -1:
                    code = content[start:start+1000]
                    print(code)
                break
