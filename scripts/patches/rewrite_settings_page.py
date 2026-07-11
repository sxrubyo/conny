content = """"use client";

import { useState, useEffect, useRef } from "react";
import { Sidebar } from "@/components/ui/modern-side-bar";
import { CheckCircle2, AlertCircle, RefreshCw, LogOut, Moon, Sun, Trash2, Key } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [profile, setProfile] = useState<any>({ name: "", email: "", role: "", avatar: "" });
  const [tokens, setTokens] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [isDark, setIsDark] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'));
    
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("dev_master_key") || "";
        
        // Fetch Profile
        const resProfile = await fetch("/api/user/profile", { headers: { "x-master-key": token } });
        if (resProfile.ok) {
            const data = await resProfile.json();
            setProfile(data);
        }

        // Fetch Tokens
        const resTokens = await fetch("/api/tokens", { headers: { "x-master-key": token } });
        if (resTokens.ok) {
            const tData = await resTokens.json();
            setTokens(tData.tokens || []);
        }

      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const toggleTheme = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    if (newDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  };

  const handleSaveProfile = async () => {
      setSaving(true);
      setSuccessMsg("");
      try {
          const token = localStorage.getItem("dev_master_key") || "";
          const res = await fetch("/api/user/profile", {
              method: "PATCH",
              headers: { 
                  "Content-Type": "application/json",
                  "x-master-key": token
              },
              body: JSON.stringify(profile)
          });
          if (res.ok) {
              setSuccessMsg("Name updated");
              setTimeout(() => setSuccessMsg(""), 3000);
          }
      } catch (e) {
          console.error(e);
      }
      setSaving(false);
  };

  const handleLogout = () => {
      localStorage.removeItem("dev_master_key");
      window.location.href = "/dev-portal/login/";
  };

  const handleDeleteToken = async (tokenId: string) => {
      if(!confirm("Delete this token?")) return;
      try {
          const master = localStorage.getItem("dev_master_key") || "";
          const res = await fetch(`/api/tokens/${tokenId}`, {
              method: "DELETE",
              headers: { "x-master-key": master }
          });
          if (res.ok) {
              setTokens(tokens.filter(t => t.id !== tokenId));
          }
      } catch(e) {}
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onloadend = async () => {
          const base64String = reader.result as string;
          // Optimistic update
          setProfile({ ...profile, avatar: base64String });

          try {
              const res = await fetch("/upload-avatar", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                      filename: file.name,
                      content_type: file.type,
                      data: base64String
                  })
              });
              const data = await res.json();
              if (res.ok && data.url) {
                  setProfile(prev => ({ ...prev, avatar: data.url }));
                  
                  // Also patch the profile
                  const master = localStorage.getItem("dev_master_key") || "";
                  await fetch("/api/user/profile", {
                      method: "PATCH",
                      headers: { "Content-Type": "application/json", "x-master-key": master },
                      body: JSON.stringify({ avatar: data.url })
                  });
              }
          } catch(err) {
              console.error(err);
          }
      };
      reader.readAsDataURL(file);
  };

  const inputStyle = "w-full bg-[#252525] border border-[#333] rounded-[8px] text-white px-[14px] py-[10px] text-[13px] focus:outline-none focus:border-[#e05a2b] transition-colors";
  const labelStyle = "block uppercase text-[#888] text-[11px] tracking-[0.06em] mb-2 font-medium";

  return (
    <div className="flex h-screen w-full bg-[#161616] overflow-hidden font-sans">
      <Sidebar />
      <main className="flex-1 overflow-y-auto custom-scrollbar p-8 text-white">
        <div className="max-w-4xl mx-auto space-y-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight mb-1">Account Settings</h1>
            <p className="text-[#888] text-sm">Manage your profile, security, and preferences.</p>
          </div>

          <div className="flex flex-col md:flex-row items-start mt-8">
            {/* Left Menu (160px) */}
            <div className="w-full md:w-[160px] flex-shrink-0 flex flex-col space-y-2 pr-8 mb-8 md:mb-0">
                {[
                    { id: "profile", label: "Profile" },
                    { id: "security", label: "Security" },
                    { id: "appearance", label: "Appearance" },
                ].map(tab => {
                    const isActive = activeTab === tab.id;
                    return (
                        <button 
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`text-left py-1.5 px-3 text-sm transition-colors ${isActive ? "text-[#e05a2b] border-l-2 border-[#e05a2b] bg-[#e05a2b]/5 font-medium" : "text-[#666] border-l-2 border-transparent hover:text-[#888]"}`}
                        >
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Right Content */}
            <div className="flex-1 w-full max-w-2xl">
                {loading ? (
                    <div className="p-8 flex justify-center"><RefreshCw className="w-5 h-5 animate-spin text-[#666]" /></div>
                ) : (
                    <>
                        {activeTab === "profile" && (
                            <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-[12px] p-6 space-y-8">
                                
                                {/* Section 1: Avatar */}
                                <div>
                                    <div className="flex flex-col items-start gap-3">
                                        <div 
                                            onClick={() => fileInputRef.current?.click()}
                                            className="w-[72px] h-[72px] rounded-full overflow-hidden bg-[#252525] border border-[#333] flex items-center justify-center text-xl font-medium cursor-pointer hover:border-[#e05a2b] transition-colors"
                                        >
                                            {profile.avatar ? (
                                                <img src={profile.avatar} alt="Avatar" className="w-full h-full object-cover" />
                                            ) : (
                                                profile.name?.charAt(0) || "U"
                                            )}
                                        </div>
                                        <button 
                                            onClick={() => fileInputRef.current?.click()}
                                            className="text-[#e05a2b] text-[13px] font-medium hover:underline"
                                        >
                                            Change photo
                                        </button>
                                        <input 
                                            type="file" 
                                            ref={fileInputRef} 
                                            className="hidden" 
                                            accept="image/*" 
                                            onChange={handleFileSelect} 
                                        />
                                    </div>
                                </div>

                                <div className="h-[0.5px] w-full bg-[#2a2a2a]" />

                                {/* Section 2: Display Name */}
                                <div>
                                    <label className={labelStyle}>Display name</label>
                                    <div className="flex items-center gap-3">
                                        <input 
                                            type="text" 
                                            value={profile.name}
                                            onChange={e => setProfile({...profile, name: e.target.value})}
                                            className={inputStyle} 
                                        />
                                        <button 
                                            onClick={handleSaveProfile} 
                                            disabled={saving} 
                                            className="px-4 py-[10px] bg-[#e05a2b] text-white text-[13px] font-medium rounded-[6px] hover:bg-[#c94e24] transition-colors disabled:opacity-50 whitespace-nowrap"
                                        >
                                            {saving ? 'Saving...' : 'Save'}
                                        </button>
                                    </div>
                                    {successMsg && <p className="mt-2 text-xs text-emerald-500">{successMsg}</p>}
                                </div>

                                <div className="h-[0.5px] w-full bg-[#2a2a2a]" />

                                {/* Section 3: Email */}
                                <div>
                                    <label className={labelStyle}>Email address</label>
                                    <input 
                                        type="email" 
                                        value={profile.email}
                                        disabled
                                        className={`${inputStyle} opacity-60 cursor-not-allowed`} 
                                    />
                                    <p className="text-[#555] text-[11px] mt-2">Contact support to change your email.</p>
                                </div>

                                <div className="h-[0.5px] w-full bg-[#2a2a2a]" />

                                {/* Section 4: Danger Zone */}
                                <div>
                                    <label className="block uppercase text-[#f87171] text-[11px] tracking-[0.06em] mb-3 font-medium">Danger Zone</label>
                                    <button 
                                        onClick={handleLogout} 
                                        className="w-full px-4 py-[10px] border border-[#f87171] text-[#f87171] bg-transparent text-[13px] font-medium rounded-[8px] hover:bg-[#f87171]/10 transition-colors flex items-center justify-center gap-2"
                                    >
                                        <LogOut className="w-4 h-4" /> Sign out
                                    </button>
                                </div>

                            </div>
                        )}

                        {activeTab === "appearance" && (
                            <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-[12px] p-6">
                                <div className="flex items-center justify-between">
                                    <label className={labelStyle} style={{ marginBottom: 0 }}>Theme</label>
                                    <button 
                                        onClick={toggleTheme} 
                                        className="flex items-center gap-2 px-3 py-1.5 bg-[#252525] border border-[#333] rounded-[6px] text-[13px] hover:border-[#e05a2b] transition-colors"
                                    >
                                        {isDark ? <Moon className="w-4 h-4 text-[#888]" /> : <Sun className="w-4 h-4 text-[#888]" />}
                                        {isDark ? 'Dark' : 'Light'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {activeTab === "security" && (
                            <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-[12px] p-6 space-y-4">
                                <label className={labelStyle}>API Tokens</label>
                                
                                {tokens.length === 0 ? (
                                    <p className="text-[#666] text-[13px]">No active tokens.</p>
                                ) : (
                                    <div className="space-y-3">
                                        {tokens.map((token: any) => (
                                            <div key={token.id} className="flex items-center justify-between p-3 bg-[#252525] border border-[#333] rounded-[8px]">
                                                <div className="flex items-center gap-3">
                                                    <Key className="w-4 h-4 text-[#888]" />
                                                    <div>
                                                        <p className="text-[13px] font-medium">{token.clinic_label}</p>
                                                        <p className="text-[#666] text-[11px] font-mono mt-0.5">{token.key_hint}</p>
                                                    </div>
                                                </div>
                                                <button 
                                                    onClick={() => handleDeleteToken(token.id)}
                                                    className="p-1.5 text-[#666] hover:text-[#f87171] hover:bg-[#f87171]/10 rounded-[4px] transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
"""
with open('/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx', 'w') as f:
    f.write(content)
