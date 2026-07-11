import re

filename = '/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

back_block = """
          {/* Back to Portal Block */}
          <div className="mt-8">
            <a href="https://bublee.duckdns.org/dev-portal/" className="block bg-white dark:bg-[#1e1e1e] border border-neutral-200 dark:border-[#2a2a2a] rounded-[12px] p-8 text-center hover:bg-neutral-50 dark:hover:bg-[#252525] transition-colors shadow-sm group">
                <div className="mx-auto w-12 h-12 rounded-full bg-neutral-100 dark:bg-[#2a2a2a] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <img src="/dev-portal/isotype.png" alt="Bublee Logo" className="w-6 h-6 object-contain dark:invert opacity-70 group-hover:opacity-100 transition-opacity" />
                </div>
                <h3 className="text-lg font-medium text-neutral-900 dark:text-white mb-1">Return to Landing Page</h3>
                <p className="text-sm text-neutral-500 dark:text-[#888]">Go back to the main Bublee website</p>
            </a>
          </div>
        </div>
      </main>
"""

content = content.replace('        </div>\n      </main>', back_block)

with open(filename, 'w') as f:
    f.write(content)
