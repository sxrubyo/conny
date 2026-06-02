with open("conny_doctor.py", "r") as f:
    content = f.read()

content = content.replace("actions = await doctor.auto_heal()", "actions = await doctor.auto_heal()\n        await doctor.run_self_healing()")

with open("conny_doctor.py", "w") as f:
    f.write(content)
