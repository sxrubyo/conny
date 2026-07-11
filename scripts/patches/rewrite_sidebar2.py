import re

content = """"use client";
import React, { useState, useEffect } from 'react';
import {
  Home,
  User,
  Settings,
  LogOut, Sun, Moon,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  FileText,
  Bell,
  Search,
  HelpCircle,
  Server
} from 'lucide-react';

interface NavigationItem {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
}

interface SidebarProps {
  className?: string;
  children?: React.ReactNode;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const navigationItems: NavigationItem[] = [
  { id: "dashboard", name: "Home", icon: Home, href: "/panel/" },
  { id: "instances", name: "Instances", icon: Server, href: "/panel/instances/" },
  { id: "analytics", name: "Analytics", icon: BarChart3, href: "/analytics" },
  { id: "documents", name: "Documents", icon: FileText, href: "/documents", badge: "3" },
];

export function Sidebar({ className = "", children, isCollapsed = false, onToggleCollapse }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isThemeDark, setIsThemeDark] = useState(true);
  
  const toggleTheme = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsThemeDark(!isThemeDark);
    if (!isThemeDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  };

  const [activeItem, setActiveItem] = useState("dashboard");

  useEffect(() => {
    // Set active item based on current pathname
    const path = window.location.pathname;
    if (path.includes("/panel/instances")) {
        setActiveItem("instances");
    } else if (path.includes("/analytics")) {
        setActiveItem("analytics");
    } else if (path.includes("/documents")) {
        setActiveItem("documents");
    } else if (path.includes("/settings")) {
        setActiveItem("settings");
    } else if (path.includes("/help")) {
        setActiveItem("help");
    } else {
        setActiveItem("dashboard");
    }

    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsOpen(true);
      } else {
        setIsOpen(false);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleSidebar = () => setIsOpen(!isOpen);

  const handleItemClick = (itemId: string, href: string) => {
    if(itemId === "logout") {
        window.location.href = '/api/auth/login';
        return;
    }

    // Force trailing slash or whatever mapping needed if using /dev-portal
    if (href && href !== window.location.pathname) {
        window.location.href = href;
        return;
    }

    setActiveItem(itemId);
    if (window.innerWidth < 768) {
      setIsOpen(false);
    }
  };

  return (
    <>
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 rounded-md bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 md:hidden hover:bg-neutral-200 dark:hover:bg-neutral-200 dark:bg-neutral-800 transition-all duration-200"
      >
        {isOpen ? <X className="h-5 w-5 text-neutral-700 dark:text-neutral-300" /> : <Menu className="h-5 w-5 text-neutral-700 dark:text-neutral-300" />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden transition-opacity" onClick={toggleSidebar} />
      )}

      <aside
        className={`
          bg-neutral-50 dark:bg-[#111111] border-r border-neutral-200 dark:border-neutral-800 z-40 flex flex-col
          ${isOpen ? "fixed inset-y-0 left-0 translate-x-0" : "max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:-translate-x-full"}
          md:translate-x-0
          ${className}
        `}
        style={{ height: "100%", overflowY: "auto", position: "relative" }}
      >
        {/* Header with logo */}
        <div 
          className={`flex items-center justify-between p-5 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-[#111111]/60 ${isCollapsed ? "cursor-pointer hover:opacity-80 transition-opacity" : ""}`}
          onClick={isCollapsed ? onToggleCollapse : undefined}
        >
          <div className="flex items-center space-x-3 w-full">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${isCollapsed ? "mx-auto" : ""}`}>
              <img 
                  src="/dev-portal/isotype.png" 
                  alt="Bublee" 
                  className="w-full h-full object-contain brightness-0 opacity-80 dark:invert dark:opacity-70"
              />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="font-semibold text-neutral-900 dark:text-white text-base">Santiago</span>
                <span className="text-xs text-neutral-500 dark:text-neutral-600 dark:text-neutral-400">Workspace</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Navigation */}
          <nav className={`flex-1 ${isCollapsed ? "px-1" : "px-3"} py-4 overflow-y-auto custom-scrollbar`}>
            <ul className="space-y-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeItem === item.id;

                return (
                  <li key={item.id}>
                    <button
                      onClick={() => handleItemClick(item.id, item.href)}
                      className={`
                        w-full flex items-center py-2 text-left transition-all duration-150 group border-l-2
                        ${isCollapsed ? "justify-center rounded-md px-0" : "space-x-3 rounded-r-md pl-[10px] pr-3"}
                        ${isActive
                          ? "border-[#e05a2b] text-[#e05a2b] bg-transparent"
                          : "border-transparent text-neutral-600 dark:text-[#666666] hover:bg-neutral-100 dark:hover:bg-white/5"
                        }
                      `}
                      title={isCollapsed ? item.name : undefined}
                    >
                      <div className="flex items-center justify-center min-w-[24px]">
                        <Icon className={`h-5 w-5 flex-shrink-0 ${isActive ? "text-[#e05a2b]" : "text-neutral-500 dark:text-[#666666] group-hover:text-neutral-700 dark:group-hover:text-white"}`} />
                      </div>

                      {!isCollapsed && (
                        <div className="flex items-center justify-between w-full">
                          <span className={`text-sm ${isActive ? "font-medium" : "font-normal"}`}>{item.name}</span>
                          {item.badge && (
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${isActive ? "bg-[#e05a2b]/10 text-[#e05a2b]" : "bg-neutral-200 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400"}`}>
                              {item.badge}
                            </span>
                          )}
                        </div>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Bottom section */}
          <div className={`mt-auto pb-6 flex flex-col pt-4 border-t border-neutral-200 dark:border-neutral-800/50 ${isCollapsed ? "gap-4 items-center px-1" : "gap-5 px-4"}`}>
            {/* Profile Area */}
            <div 
              onClick={() => handleItemClick('settings', '/settings')}
              className={`flex items-center cursor-pointer group ${isCollapsed ? "justify-center" : "justify-start"}`}
              title="Settings & Profile"
            >
              <div className="h-9 w-9 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 shadow-sm">
                  <img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=900&auto=format&fit=crop&q=60" className="w-full h-full object-cover" />
              </div>
              
              {!isCollapsed && (
                <div className="ml-3 flex flex-col min-w-0">
                  <span className={`text-sm font-semibold truncate transition-colors ${activeItem === 'settings' ? 'text-[#e05a2b]' : 'text-neutral-900 dark:text-white group-hover:text-[#e05a2b]'}`}>Santiago</span>
                  <span className="text-xs text-neutral-500 dark:text-neutral-400 truncate">Santi21435@gmail.com</span>
                </div>
              )}
            </div>

            <div
              onClick={() => handleItemClick('help', '/help')}
              className={`flex items-center cursor-pointer group transition-colors ${isCollapsed ? "justify-center" : "justify-start"} ${activeItem === 'help' ? 'text-[#e05a2b]' : 'text-neutral-500 hover:text-neutral-900 dark:hover:text-white'}`}
              title={isCollapsed ? "Help Center" : undefined}
            >
              <HelpCircle className="h-4 w-4 flex-shrink-0" />
              {!isCollapsed && <span className="ml-3 text-xs font-medium">Help Center</span>}
            </div>
            
            <div
              onClick={toggleTheme}
              className={`flex items-center cursor-pointer group text-neutral-500 hover:text-neutral-900 dark:hover:text-white transition-colors ${isCollapsed ? "justify-center" : "justify-start"}`}
              title={isCollapsed ? (isThemeDark ? "Light Mode" : "Dark Mode") : undefined}
            >
              {isThemeDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {!isCollapsed && <span className="ml-3 text-xs font-medium">{isThemeDark ? "Light Mode" : "Dark Mode"}</span>}
            </div>
          </div>
        </div>
        {children}
      </aside>
    </>
  );
}
"""

with open('/home/ubuntu/bublee-dev-react/src/components/ui/modern-side-bar.tsx', 'w') as f:
    f.write(content)
