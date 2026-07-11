import re

filename = '/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add state for profile
if 'const [profile, setProfile]' not in content:
    state_code = """
  const [profile, setProfile] = useState<any>({ name: "Santiago", email: "Santi21435@gmail.com", avatar: "https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60" });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem("dev_master_key") || "";
        const res = await fetch("/api/user/profile", { headers: { "x-master-key": token } });
        if (res.ok) {
          const data = await res.json();
          setProfile((prev: any) => ({ ...prev, ...data }));
        }
      } catch (e) {}
    };
    fetchProfile();

    const handleAvatarUpdate = (e: any) => {
      setProfile((prev: any) => ({ ...prev, avatar: e.detail }));
    };
    // Let's also listen to a general profile update if name changes
    const handleProfileUpdate = (e: any) => {
      if(e.detail.name) setProfile((prev: any) => ({ ...prev, name: e.detail.name }));
    };

    window.addEventListener('avatarUpdated', handleAvatarUpdate);
    window.addEventListener('profileUpdated', handleProfileUpdate);
    return () => {
        window.removeEventListener('avatarUpdated', handleAvatarUpdate);
        window.removeEventListener('profileUpdated', handleProfileUpdate);
    };
  }, []);
"""
    content = content.replace('export function Sidebar({ className, children }: SidebarProps) {\n', 'export function Sidebar({ className, children }: SidebarProps) {\n' + state_code)

# Replace the hardcoded top left
content = re.sub(r'<span className="font-semibold text-neutral-900 dark:text-white\ntext-base">Santiago</span>', r'<span className="font-semibold text-neutral-900 dark:text-white text-base">{profile.name}</span>', content, flags=re.MULTILINE|re.DOTALL)
content = content.replace('<span className="font-semibold text-neutral-900 dark:text-white text-base">Santiago</span>', '<span className="font-semibold text-neutral-900 dark:text-white text-base">{profile.name}</span>')

# Replace the hardcoded bottom left
# <img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover" />
# with: {profile.avatar ? <img src={profile.avatar} className="w-full h-full object-cover" /> : profile.name.charAt(0)}
avatar_img = r'<img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79\?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover" />'
avatar_img_multiline = r'<img src="https://images.unsplash.com/photo-1531427186611-ecfd\n6d936c79\?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover"\n />'

replacement = '{profile.avatar ? <img src={profile.avatar} className="w-full h-full object-cover" /> : <span className="font-bold text-neutral-600 dark:text-[#ccc] text-sm">{profile.name?.charAt(0)}</span>}'

content = re.sub(avatar_img, replacement, content)
content = re.sub(avatar_img_multiline, replacement, content)
content = re.sub(r'<img\s+src="https://images\.unsplash\.com/photo-1531427186611-ecfd\s+6d936c79\?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover"\s+/>', replacement, content, flags=re.MULTILINE)


content = re.sub(r'<span className=\{`text-sm font-semibold truncate transition-colors \$\{activeItem === \'settings\' \? \'text-\[#e05a2b\]\' : \'text-neutral-900 dark:text-white group-hover:text-\[#e05a2b\]\'\}`\}>Santiago</span>', r'<span className={`text-sm font-semibold truncate transition-colors ${activeItem === \'settings\' ? \'text-[#e05a2b]\' : \'text-neutral-900 dark:text-white group-hover:text-[#e05a2b]\'}`}>{profile.name}</span>', content)
content = re.sub(r'<span className=\{`text-sm font-semibold truncate transition-co\s+lors \$\{activeItem === \'settings\' \? \'text-\[#e05a2b\]\' : \'text-neutral-900 dark:tex\s+t-white group-hover:text-\[#e05a2b\]\'\}`\}>Santiago</span>', r'<span className={`text-sm font-semibold truncate transition-colors ${activeItem === \'settings\' ? \'text-[#e05a2b]\' : \'text-neutral-900 dark:text-white group-hover:text-[#e05a2b]\'}`}>{profile.name}</span>', content, flags=re.MULTILINE)


content = content.replace('<span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">Santi21435@gmail.com</span>', '<span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{profile.email}</span>')
content = re.sub(r'<span className="text-xs text-neutral-500 dark:text-neutral-40\s+0 truncate">Santi21435@gmail\.com</span>', '<span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{profile.email}</span>', content, flags=re.MULTILINE)

with open(filename, 'w') as f:
    f.write(content)
