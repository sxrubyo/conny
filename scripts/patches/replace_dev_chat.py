import re

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Locate the current dev views section
start_tag = '<section id="view-dev-ai-chat" class="tab-view active">'
end_tag = '</section>'
start_idx = html.find(start_tag)
if start_idx == -1:
    print("Could not find view-dev-ai-chat section")
    exit(1)

# Find the end of the section by counting <section> tags or just finding the first </section> since we know its structure
sub_html = html[start_idx:]
end_idx = start_idx + sub_html.find(end_tag) + len(end_tag)

new_v0_html = """<section id="view-dev-ai-chat" class="tab-view active" style="background: #ffffff; margin: 0; padding: 0;">
    <div style="display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 56rem; margin: 0 auto; padding: 16px; gap: 32px; height: 100vh; justify-content: center; background: #ffffff;">
        <h1 style="font-size: 2.25rem; font-weight: 700; color: #000000;">
            What can I help you ship?
        </h1>

        <div style="width: 100%;">
            <div style="position: relative; background-color: #f5f5f5; border-radius: 0.75rem; border: 1px solid #e5e5e5; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);">
                <div style="overflow-y: auto;">
                    <textarea id="dev-v0-input" placeholder="Ask v0 a question..." style="width: 100%; padding: 16px; resize: none; background: transparent; border: none; color: #000000; font-size: 0.875rem; outline: none; min-height: 60px; overflow: hidden; box-shadow: none;"></textarea>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button style="padding: 8px; border-radius: 0.5rem; border: none; background: transparent; cursor: pointer; display: flex; align-items: center; gap: 4px; color: #71717a; transition: background 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.children[1].style.display='inline'" onmouseout="this.style.background='transparent'; this.children[1].style.display='none'">
                            <i data-lucide="paperclip" style="width: 16px; height: 16px; color: #000000;"></i>
                            <span style="font-size: 0.75rem; display: none;">Attach</span>
                        </button>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button style="padding: 4px 8px; border-radius: 0.5rem; font-size: 0.875rem; color: #71717a; transition: all 0.2s; border: 1px dashed #d4d4d8; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 4px;" onmouseover="this.style.borderColor='#a1a1aa'; this.style.background='#e5e5e5'" onmouseout="this.style.borderColor='#d4d4d8'; this.style.background='transparent'">
                            <i data-lucide="plus" style="width: 16px; height: 16px;"></i>
                            Project
                        </button>
                        <button id="dev-v0-send-btn" style="padding: 6px; border-radius: 0.5rem; transition: all 0.2s; border: 1px solid #d4d4d8; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 4px; color: #71717a;" onmouseover="if(!this.disabled){this.style.borderColor='#a1a1aa'; this.style.background='#e5e5e5';}" onmouseout="if(!this.disabled){this.style.borderColor='#d4d4d8'; this.style.background='transparent';}">
                            <i data-lucide="arrow-up" style="width: 16px; height: 16px;" id="dev-v0-send-icon"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 12px; margin-top: 16px;">
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #fafafa; border-radius: 9999px; border: 1px solid #e5e5e5; color: #71717a; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.style.color='#000000'" onmouseout="this.style.background='#fafafa'; this.style.color='#71717a'">
                    <i data-lucide="image" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Clone a Screenshot</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #fafafa; border-radius: 9999px; border: 1px solid #e5e5e5; color: #71717a; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.style.color='#000000'" onmouseout="this.style.background='#fafafa'; this.style.color='#71717a'">
                    <i data-lucide="figma" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Import from Figma</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #fafafa; border-radius: 9999px; border: 1px solid #e5e5e5; color: #71717a; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.style.color='#000000'" onmouseout="this.style.background='#fafafa'; this.style.color='#71717a'">
                    <i data-lucide="file-up" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Upload a Project</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #fafafa; border-radius: 9999px; border: 1px solid #e5e5e5; color: #71717a; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.style.color='#000000'" onmouseout="this.style.background='#fafafa'; this.style.color='#71717a'">
                    <i data-lucide="monitor" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Landing Page</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #fafafa; border-radius: 9999px; border: 1px solid #e5e5e5; color: #71717a; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#e5e5e5'; this.style.color='#000000'" onmouseout="this.style.background='#fafafa'; this.style.color='#71717a'">
                    <i data-lucide="circle-user-round" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Sign Up Form</span>
                </button>
            </div>
        </div>
    </div>
</section>"""

# Wait, the v0 chat has a dark version and light version. I will use a dark theme because Bublee is mostly dark.
new_v0_html_dark = """<section id="view-dev-ai-chat" class="tab-view active" style="background: #000000; margin: 0; padding: 0;">
    <div style="display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 56rem; margin: 0 auto; padding: 16px; gap: 32px; height: 100vh; justify-content: center; background: #000000;">
        <h1 style="font-size: 2.25rem; font-weight: 700; color: #ffffff;">
            What can I help you ship?
        </h1>

        <div style="width: 100%;">
            <div style="position: relative; background-color: #171717; border-radius: 0.75rem; border: 1px solid #262626;">
                <div style="overflow-y: auto;">
                    <textarea id="dev-v0-input" placeholder="Ask v0 a question..." style="width: 100%; padding: 16px; resize: none; background: transparent; border: none; color: #ffffff; font-size: 0.875rem; outline: none; min-height: 60px; overflow: hidden; box-shadow: none;"></textarea>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button style="padding: 8px; border-radius: 0.5rem; border: none; background: transparent; cursor: pointer; display: flex; align-items: center; gap: 4px; color: #a1a1aa; transition: background 0.2s;" onmouseover="this.style.background='#262626'; this.children[1].style.display='inline'" onmouseout="this.style.background='transparent'; this.children[1].style.display='none'">
                            <i data-lucide="paperclip" style="width: 16px; height: 16px; color: #ffffff;"></i>
                            <span style="font-size: 0.75rem; display: none;">Attach</span>
                        </button>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button style="padding: 4px 8px; border-radius: 0.5rem; font-size: 0.875rem; color: #a1a1aa; transition: all 0.2s; border: 1px dashed #3f3f46; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 4px;" onmouseover="this.style.borderColor='#52525b'; this.style.background='#27272a'" onmouseout="this.style.borderColor='#3f3f46'; this.style.background='transparent'">
                            <i data-lucide="plus" style="width: 16px; height: 16px;"></i>
                            Project
                        </button>
                        <button id="dev-v0-send-btn" style="padding: 6px; border-radius: 0.5rem; transition: all 0.2s; border: 1px solid #3f3f46; background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 4px; color: #a1a1aa;" disabled>
                            <i data-lucide="arrow-up" style="width: 16px; height: 16px;" id="dev-v0-send-icon"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 12px; margin-top: 16px;">
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #171717; border-radius: 9999px; border: 1px solid #262626; color: #a1a1aa; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#262626'; this.style.color='#ffffff'" onmouseout="this.style.background='#171717'; this.style.color='#a1a1aa'">
                    <i data-lucide="image" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Clone a Screenshot</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #171717; border-radius: 9999px; border: 1px solid #262626; color: #a1a1aa; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#262626'; this.style.color='#ffffff'" onmouseout="this.style.background='#171717'; this.style.color='#a1a1aa'">
                    <i data-lucide="figma" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Import from Figma</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #171717; border-radius: 9999px; border: 1px solid #262626; color: #a1a1aa; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#262626'; this.style.color='#ffffff'" onmouseout="this.style.background='#171717'; this.style.color='#a1a1aa'">
                    <i data-lucide="file-up" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Upload a Project</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #171717; border-radius: 9999px; border: 1px solid #262626; color: #a1a1aa; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#262626'; this.style.color='#ffffff'" onmouseout="this.style.background='#171717'; this.style.color='#a1a1aa'">
                    <i data-lucide="monitor" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Landing Page</span>
                </button>
                <button class="v0-action-btn" style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background-color: #171717; border-radius: 9999px; border: 1px solid #262626; color: #a1a1aa; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#262626'; this.style.color='#ffffff'" onmouseout="this.style.background='#171717'; this.style.color='#a1a1aa'">
                    <i data-lucide="circle-user-round" style="width: 16px; height: 16px;"></i>
                    <span style="font-size: 0.75rem;">Sign Up Form</span>
                </button>
            </div>
        </div>
    </div>
</section>"""

html = html[:start_idx] + new_v0_html_dark + html[end_idx:]

with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

