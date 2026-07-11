import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace the DEV VIEWS section with the new AI Chat
dev_views_start = html.find('<!-- DEV VIEWS -->')
# Find the end of dev views, which is right before <!-- MODALS --> or </main>
end_of_main = html.find('</main>')

new_dev_html = """<!-- DEV VIEWS -->
            <section id="view-dev-ai-chat" class="tab-view active">
                <div class="h-full flex flex-col w-full items-center justify-center bg-transparent text-white relative overflow-hidden" style="height: 100vh; position: relative;">
                    <div class="absolute inset-0 w-full h-full overflow-hidden pointer-events-none">
                        <div class="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal blur-[128px]" style="animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;"></div>
                        <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal blur-[128px]" style="animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite 700ms;"></div>
                        <div class="absolute top-1/4 right-1/3 w-64 h-64 bg-fuchsia-500/10 rounded-full mix-blend-normal blur-[96px]" style="animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite 1000ms;"></div>
                    </div>
                    <div class="w-full max-w-2xl mx-auto relative z-10 space-y-12 transition-all duration-700 ease-out translate-y-0 opacity-100" style="padding: 24px;">
                        <div class="text-center" style="margin-bottom: 48px;">
                            <div class="inline-block" style="text-align: center;">
                                <h1 style="font-size: 1.875rem; font-weight: 500; letter-spacing: -0.025em; background-clip: text; color: transparent; background-image: linear-gradient(to right, rgba(255,255,255,0.9), rgba(255,255,255,0.4)); padding-bottom: 4px; margin-bottom: 12px;">
                                    How can I help today?
                                </h1>
                                <div style="height: 1px; width: 100%; background: linear-gradient(to right, transparent, rgba(255,255,255,0.2), transparent);"></div>
                            </div>
                            <p style="font-size: 0.875rem; color: rgba(255,255,255,0.4); margin-top: 12px;">Type a command or ask a question</p>
                        </div>

                        <div style="position: relative; backdrop-filter: blur(40px); background: rgba(255,255,255,0.02); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);">
                            
                            <div id="dev-command-palette" style="display: none; position: absolute; left: 16px; right: 16px; bottom: 100%; margin-bottom: 8px; backdrop-filter: blur(24px); background: rgba(0,0,0,0.9); border-radius: 8px; z-index: 50; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.1); overflow: hidden;">
                                <div style="padding: 4px; background: rgba(0,0,0,0.95);">
                                    <div class="cmd-suggestion" data-cmd="/clone" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 0.75rem; cursor: pointer; color: rgba(255,255,255,0.7); transition: background 0.2s; border-radius: 4px;">
                                        <i data-lucide="image" style="width: 16px; height: 16px; color: rgba(255,255,255,0.6);"></i>
                                        <div style="font-weight: 500; flex: 1;">Clone UI</div>
                                        <div style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">/clone</div>
                                    </div>
                                    <div class="cmd-suggestion" data-cmd="/figma" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 0.75rem; cursor: pointer; color: rgba(255,255,255,0.7); transition: background 0.2s; border-radius: 4px;">
                                        <i data-lucide="figma" style="width: 16px; height: 16px; color: rgba(255,255,255,0.6);"></i>
                                        <div style="font-weight: 500; flex: 1;">Import Figma</div>
                                        <div style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">/figma</div>
                                    </div>
                                    <div class="cmd-suggestion" data-cmd="/page" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 0.75rem; cursor: pointer; color: rgba(255,255,255,0.7); transition: background 0.2s; border-radius: 4px;">
                                        <i data-lucide="monitor" style="width: 16px; height: 16px; color: rgba(255,255,255,0.6);"></i>
                                        <div style="font-weight: 500; flex: 1;">Create Page</div>
                                        <div style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">/page</div>
                                    </div>
                                    <div class="cmd-suggestion" data-cmd="/improve" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; font-size: 0.75rem; cursor: pointer; color: rgba(255,255,255,0.7); transition: background 0.2s; border-radius: 4px;">
                                        <i data-lucide="sparkles" style="width: 16px; height: 16px; color: rgba(255,255,255,0.6);"></i>
                                        <div style="font-weight: 500; flex: 1;">Improve</div>
                                        <div style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">/improve</div>
                                    </div>
                                </div>
                            </div>

                            <div style="padding: 16px;">
                                <textarea id="dev-ai-input" placeholder="Ask zap a question..." style="width: 100%; padding: 12px 16px; resize: none; background: transparent; border: none; color: rgba(255,255,255,0.9); font-size: 0.875rem; outline: none; min-height: 60px; overflow: hidden; box-shadow: none;"></textarea>
                            </div>

                            <div id="dev-ai-attachments" style="display: none; padding: 0 16px 12px 16px; display: flex; gap: 8px; flex-wrap: wrap;"></div>

                            <div style="padding: 16px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <button id="dev-ai-attach-btn" style="padding: 8px; color: rgba(255,255,255,0.4); background: transparent; border: none; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;" onmouseover="this.style.color='rgba(255,255,255,0.9)'; this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.color='rgba(255,255,255,0.4)'; this.style.background='transparent'">
                                        <i data-lucide="paperclip" style="width: 16px; height: 16px;"></i>
                                    </button>
                                    <button id="dev-ai-cmd-btn" style="padding: 8px; color: rgba(255,255,255,0.4); background: transparent; border: none; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;" onmouseover="this.style.color='rgba(255,255,255,0.9)'; this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.color='rgba(255,255,255,0.4)'; this.style.background='transparent'">
                                        <i data-lucide="command" style="width: 16px; height: 16px;"></i>
                                    </button>
                                </div>
                                
                                <button id="dev-ai-send-btn" style="padding: 8px 16px; border-radius: 8px; font-size: 0.875rem; font-weight: 500; display: flex; align-items: center; gap: 8px; transition: all 0.2s; background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); border: none; cursor: not-allowed;" disabled>
                                    <i data-lucide="send" style="width: 16px; height: 16px;" id="dev-ai-send-icon"></i>
                                    <i data-lucide="loader" style="width: 16px; height: 16px; display: none; animation: spin 2s linear infinite;" id="dev-ai-loader-icon"></i>
                                    <span>Send</span>
                                </button>
                            </div>
                        </div>

                        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px; margin-top: 32px;">
                            <button class="dev-quick-cmd" data-cmd="/clone" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 8px; font-size: 0.875rem; color: rgba(255,255,255,0.6); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'; this.style.color='rgba(255,255,255,0.9)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'; this.style.color='rgba(255,255,255,0.6)'">
                                <i data-lucide="image" style="width: 16px; height: 16px;"></i>
                                <span>Clone UI</span>
                            </button>
                            <button class="dev-quick-cmd" data-cmd="/figma" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 8px; font-size: 0.875rem; color: rgba(255,255,255,0.6); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'; this.style.color='rgba(255,255,255,0.9)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'; this.style.color='rgba(255,255,255,0.6)'">
                                <i data-lucide="figma" style="width: 16px; height: 16px;"></i>
                                <span>Import Figma</span>
                            </button>
                            <button class="dev-quick-cmd" data-cmd="/page" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 8px; font-size: 0.875rem; color: rgba(255,255,255,0.6); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'; this.style.color='rgba(255,255,255,0.9)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'; this.style.color='rgba(255,255,255,0.6)'">
                                <i data-lucide="monitor" style="width: 16px; height: 16px;"></i>
                                <span>Create Page</span>
                            </button>
                            <button class="dev-quick-cmd" data-cmd="/improve" style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 8px; font-size: 0.875rem; color: rgba(255,255,255,0.6); border: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'; this.style.color='rgba(255,255,255,0.9)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'; this.style.color='rgba(255,255,255,0.6)'">
                                <i data-lucide="sparkles" style="width: 16px; height: 16px;"></i>
                                <span>Improve</span>
                            </button>
                        </div>
                    </div>

                    <div id="dev-ai-typing-indicator" style="display: none; position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); backdrop-filter: blur(40px); background: rgba(255,255,255,0.02); border-radius: 9999px; padding: 8px 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05); z-index: 50;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 32px; height: 28px; border-radius: 9999px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center;">
                                <span style="font-size: 0.75rem; font-weight: 500; color: rgba(255,255,255,0.9);">zap</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.875rem; color: rgba(255,255,255,0.7);">
                                <span>Thinking</span>
                                <div style="display: flex; align-items: center; gap: 4px;">
                                    <div style="width: 6px; height: 6px; background: rgba(255,255,255,0.9); border-radius: 50%; animation: pulse 1.2s infinite ease-in-out;"></div>
                                    <div style="width: 6px; height: 6px; background: rgba(255,255,255,0.9); border-radius: 50%; animation: pulse 1.2s infinite ease-in-out 200ms;"></div>
                                    <div style="width: 6px; height: 6px; background: rgba(255,255,255,0.9); border-radius: 50%; animation: pulse 1.2s infinite ease-in-out 400ms;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
"""

# Replace the dev views
html = html[:dev_views_start] + new_dev_html + "\n            " + html[end_of_main:]

# 2. Update the sidebar dev nav
sidebar_nav_start = html.find('<nav class="sidebar-nav" id="dev-sidebar-nav"')
sidebar_nav_end = html.find('</nav>', sidebar_nav_start) + 6

new_sidebar_nav = """<nav class="sidebar-nav" id="dev-sidebar-nav" style="display: none;">
                <button class="nav-item active" data-view="dev-ai-chat" title="Zap AI">
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path>
                    </svg>
                    <span class="nav-text">Zap AI</span>
                </button>
            </nav>"""

html = html[:sidebar_nav_start] + new_sidebar_nav + html[sidebar_nav_end:]

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
