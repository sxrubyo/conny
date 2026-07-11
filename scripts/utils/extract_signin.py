import json

found = False
with open("/home/ubuntu/.gemini/antigravity-cli/brain/d4b57b0a-7144-48e5-9630-7e2af3a48e9d/.system_generated/logs/transcript.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_REQUEST":
            content = data.get("content", "")
            if "arreglalo, el de devs era este." in content and "sign-in.tsx" in content:
                print("FOUND!")
                start_idx = content.find("```tsx\\nsign-in.tsx")
                if start_idx != -1:
                    code = content[start_idx:]
                    end_idx = code.find("```", 10)
                    if end_idx != -1:
                        code = code[:end_idx+3]
                    with open("extracted_dev_signin.tsx", "w") as out:
                        out.write(code)
                break
