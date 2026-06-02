with open("conny_doctor.py", "r") as f:
    lines = f.readlines()

main_idx = -1
for i, line in enumerate(lines):
    if "if __name__ == \"__main__\":" in line:
        main_idx = i
        break

# Extract the newly added methods (they are at the end, from main_idx + 3 to EOF)
if main_idx != -1 and len(lines) > main_idx + 2:
    new_methods = lines[main_idx+2:]
    # Remove them from the end
    lines = lines[:main_idx]
    
    # Insert them BEFORE the main block (which means inside the class? 
    # Wait, the main block is NOT inside the class. The class ends just before `async def main():`
    class_end_idx = -1
    for i in range(main_idx, -1, -1):
        if "async def main():" in lines[i]:
            class_end_idx = i
            break
    
    if class_end_idx != -1:
        # Insert new methods just before async def main()
        # Make sure they are indented correctly (4 spaces)
        fixed_methods = []
        for m in new_methods:
            if m.startswith("    "):
                fixed_methods.append(m)
            elif m.strip() == "":
                fixed_methods.append("\n")
            else:
                fixed_methods.append("    " + m)
                
        lines.insert(class_end_idx, "\n" + "".join(fixed_methods) + "\n")
        
        with open("conny_doctor.py", "w") as f:
            f.writelines(lines)
        print("Patched successfully")
    else:
        print("Could not find main()")
