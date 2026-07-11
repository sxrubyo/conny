content = """"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/ui/modern-side-bar";
import { User, Shield, Bell, Palette, LogOut, Upload, Sun, Moon, RefreshCw, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [profile, setProfile] = useState<any>({ name: "", email: "", role: "", avatar: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Check initial theme
    setIsDark(document.documentElement.classList.contains('dark'));
    
    // Fetch profile
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem("dev_master_key") || "";
        const res = await fetch("/api/user/profile", {
            headers: { "x-master-key": token }
        });
        if (res.ok) {
            const data = await res.json();
            setProfile(data);
        }
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchProfile();
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
              setSuccessMsg("Profile updated successfully");
              setTimeout(() => setSuccessMsg(""), 3000);
          }
      } catch (e) {
          console.error(e);
      }
      setSaving(false);
  };

  const handleLogout = () => {
      localStorage.removeItem("dev_master_key");
      window.location.href = "/login";
  };

  return (
    <div className="flex h-screen w-full bg-neutral-50 dark:bg-[#111111] overflow-hidden font-sans">
      <Sidebar />
      <main className="flex-1 overflow-y-auto custom-scrollbar p-8 text-neutral-900 dark:text-white">
        <div className="max-w-5xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
            <p className="text-neutral-500 dark:text-neutral-400">Manage your account settings and preferences.</p>
          </div>

          <div className="flex flex-col md:flex-row gap-8 items-start mt-8">
            {/* Left Menu */}
            <div className="w-full md:w-48 flex-shrink-0 flex flex-col space-y-1">
                {[
                    { id: "profile", label: "Profile", icon: User },
                    { id: "security", label: "Security", icon: Shield },
                    { id: "notifications", label: "Notifications", icon: Bell },
                    { id: "appearance", label: "Appearance", icon: Palette },
                ].map(tab => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button 
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? "bg-white dark:bg-neutral-800 text-[#e05a2b] shadow-sm" : "text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200/50 dark:hover:bg-neutral-800/50"}`}
                        >
                            <Icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Right Content */}
            <div className="flex-1 w-full bg-white dark:bg-[#111111] md:dark:bg-neutral-900/30 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-sm min-h-[500px]">
                {loading ? (
                    <div className="p-8 flex justify-center"><RefreshCw className="w-6 h-6 animate-spin text-neutral-400" /></div>
                ) : (
                    <>
                        {activeTab === "profile" && (
                            <div className="p-8 space-y-8">
                                <div>
                                    <h2 className="text-xl font-semibold mb-6">Profile Picture</h2>
                                    <div className="flex items-center gap-6">
                                        <div className="w-20 h-20 rounded-full overflow-hidden border border-neutral-200 dark:border-neutral-700">
                                            {profile.avatar ? (
                                                <img src={profile.avatar} alt="Avatar" className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center text-xl font-bold">
                                                    {profile.name?.charAt(0) || "U"}
                                                </div>
                                            )}
                                        </div>
                                        <button className="flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-sm font-medium rounded-md transition-colors border border-neutral-200 dark:border-neutral-700">
                                            <Upload className="w-4 h-4" /> Change photo
                                        </button>
                                    </div>
                                </div>

                                <div className="space-y-5">
                                    <h2 className="text-xl font-semibold">Personal Information</h2>
                                    <div className="grid gap-4 max-w-md">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Full name</label>
                                            <input 
                                                type="text" 
                                                value={profile.name}
                                                onChange={e => setProfile({...profile, name: e.target.value})}
                                                className="w-full px-3 py-2 bg-neutral-50 dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e05a2b]" 
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Email address</label>
                                            <input 
                                                type="email" 
                                                value={profile.email}
                                                disabled
                                                className="w-full px-3 py-2 bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg text-sm text-neutral-500 cursor-not-allowed" 
                                            />
                                            <p className="text-xs text-neutral-500">Email cannot be changed.</p>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Role</label>
                                            <input 
                                                type="text" 
                                                value={profile.role}
                                                onChange={e => setProfile({...profile, role: e.target.value})}
                                                className="w-full px-3 py-2 bg-neutral-50 dark:bg-black border border-neutral-200 dark:border-neutral-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#e05a2b]" 
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex items-center gap-4">
                                    <button onClick={handleSaveProfile} disabled={saving} className="px-5 py-2 bg-[#e05a2b] hover:bg-[#c94e24] text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50 flex items-center gap-2">
                                        {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
                                        Save changes
                                    </button>
                                    {successMsg && <span className="text-sm text-emerald-500 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> {successMsg}</span>}
                                </div>

                                <div className="pt-8 border-t border-neutral-200 dark:border-neutral-800">
                                    <button onClick={handleLogout} className="w-full md:w-auto px-5 py-2 border border-red-500 text-red-500 hover:bg-red-500/10 text-sm font-medium rounded-md transition-colors flex items-center justify-center gap-2">
                                        <LogOut className="w-4 h-4" /> Sign out
                                    </button>
                                </div>
                            </div>
                        )}

                        {activeTab === "appearance" && (
                            <div className="p-8 space-y-8">
                                <div>
                                    <h2 className="text-xl font-semibold mb-6">Appearance</h2>
                                    <div className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-800 rounded-xl bg-neutral-50 dark:bg-black">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-white dark:bg-neutral-900 rounded-lg shadow-sm border border-neutral-200 dark:border-neutral-800">
                                                {isDark ? <Moon className="w-6 h-6 text-indigo-400" /> : <Sun className="w-6 h-6 text-amber-500" />}
                                            </div>
                                            <div>
                                                <h3 className="font-medium">Theme Preference</h3>
                                                <p className="text-sm text-neutral-500">Toggle between light and dark mode.</p>
                                            </div>
                                        </div>
                                        <button onClick={toggleTheme} className="px-4 py-2 border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-md text-sm font-medium transition-colors">
                                            Switch to {isDark ? 'Light' : 'Dark'} Mode
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {(activeTab === "security" || activeTab === "notifications") && (
                            <div className="p-8 flex items-center justify-center h-64 text-neutral-500">
                                This section is under construction.
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
