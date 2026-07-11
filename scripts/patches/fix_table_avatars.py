import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/table-with-dialog.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add avatar to user state
content = content.replace('const [balance, setBalance] = useState("0");', 'const [balance, setBalance] = useState("0");\n  const [avatar, setAvatar] = useState("");\n  const [showAvatars, setShowAvatars] = useState(false);\n  const presetAvatars = Array.from({ length: 30 }, (_, i) => `/static/avatars/avatar_${String(i + 1).padStart(2, "0")}.svg`);')

# Add avatar to POST
content = content.replace('body: JSON.stringify({ name, email, location, status, balance: parseFloat(balance) })', 'body: JSON.stringify({ name, email, location, status, balance: parseFloat(balance), avatar })')

# Reset avatar
content = content.replace('setBalance("0"); setStatus("Active");', 'setBalance("0"); setStatus("Active"); setAvatar("");')

# Add UI for avatar selection in the form
form_avatar_ui = """
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full overflow-hidden bg-neutral-100 dark:bg-[#252525] border border-neutral-200 dark:border-[#333] flex items-center justify-center text-xl font-medium">
                            {avatar ? <img src={avatar} alt="Avatar" className="w-full h-full object-cover" /> : (name.charAt(0) || "U")}
                        </div>
                        <button type="button" onClick={() => setShowAvatars(!showAvatars)} className="text-[12px] text-[#e05a2b] hover:underline font-medium">Choose Avatar</button>
                    </div>
                    {showAvatars && (
                        <div className="p-3 bg-neutral-50 dark:bg-[#252525] border border-neutral-200 dark:border-[#333] rounded-[8px] w-full mt-2">
                            <div className="grid grid-cols-6 gap-2 max-h-32 overflow-y-auto custom-scrollbar">
                                {presetAvatars.map((url, i) => (
                                    <img key={i} src={url} alt={`Avatar ${i}`} className="w-8 h-8 rounded-full cursor-pointer hover:ring-2 ring-[#e05a2b] transition-all" onClick={() => { setAvatar(url); setShowAvatars(false); }} />
                                ))}
                            </div>
                        </div>
                    )}
"""

content = content.replace('<form onSubmit={handleCreateUser} className="space-y-4">', '<form onSubmit={handleCreateUser} className="space-y-4">\n' + form_avatar_ui)

# Update the display of the user avatar in the table
user_avatar_display = """
                            <div className="w-7 h-7 rounded-full bg-neutral-200 dark:bg-[#333] flex items-center justify-center text-xs font-bold text-neutral-600 dark:text-[#ccc] overflow-hidden">
                            {user.avatar ? <img src={user.avatar} className="w-full h-full object-cover"/> : user.name.charAt(0)}
                            </div>
"""

content = re.sub(r'<div className="w-7 h-7.*?</div>', user_avatar_display, content, flags=re.DOTALL)

with open(filename, 'w') as f:
    f.write(content)
