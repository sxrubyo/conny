import re
with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/index.html', 'r') as f:
    html = f.read()

replacement = """
    <script>
        (function() {
            var mk = localStorage.getItem("bublee_master_key");
            var isDev = localStorage.getItem("bublee_dev_mode") === "true";
            var path = window.location.pathname;
            var googleLogin = new URLSearchParams(window.location.search).get("google_login") === "true";
            
            if (mk && isDev) {
                document.write("<style>body, #dashboard-workspace, .workspace { background: #000000 !important; }</style>");
            }
            
            if (!mk && !googleLogin) {
                document.write("<style>#login-screen { display: flex !important; opacity: 1 !important; }</style>");
            } else if (mk && path !== "/sign-in" && !googleLogin) {
                document.write("<style>#login-screen { display: none !important; opacity: 0 !important; }</style>");
                if (isDev) {
                    document.write("<style>#dashboard-layout { display: flex !important; opacity: 1 !important; }</style>");
                    document.write("<style>#dashboard-sidebar { display: none !important; }</style>");
                    document.write("<style>#dashboard-workspace { width: 100vw !important; margin-left: 0 !important; }</style>");
                } else {
                    document.write("<style>#dashboard-layout { display: flex !important; opacity: 1 !important; }</style>");
                }
            }
        })();
    </script>
"""

html = re.sub(
    r'<script>\s*\(function\(\) \{\s*var mk = localStorage\.getItem\("bublee_master_key"\);\s*var path = window\.location\.pathname;\s*var googleLogin = new URLSearchParams\(window\.location\.search\)\.get\("google_login"\) === "true";\s*if \(\!mk && \!googleLogin\) \{\s*document\.write\("<style>#login-screen \{ display: flex !important; opacity: 1 !important; \}</style>"\);\s*\} else if \(mk && path !== "/sign-in" && \!googleLogin\) \{\s*document\.write\("<style>#login-screen \{ display: none !important; opacity: 0 !important; \}</style>"\);\s*document\.write\("<style>#dashboard-layout \{ display: flex !important; opacity: 1 !important; \}</style>"\);\s*\}\s*\}\)\(\);\s*</script>',
    replacement.strip(),
    html
)

with open('/home/ubuntu/.bublee/repo/src/interfaces/web/static/index.html', 'w') as f:
    f.write(html)
with open('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'w') as f:
    f.write(html)
