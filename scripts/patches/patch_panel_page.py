import re

filepath = "/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx"
with open(filepath, "r") as f:
    content = f.read()

# Add import
import_statement = 'import TableWithDialog from "@/components/ui/table-with-dialog";\n'
content = content.replace('import { Sidebar } from "@/components/ui/modern-side-bar";', import_statement + 'import { Sidebar } from "@/components/ui/modern-side-bar";')

# Insert TableWithDialog before the closing div of the main content
# The main content ends with:
#             </div>
#           </div>
#         </div>
#       </main>
#     </div>

insertion = """
          {/* User Table Component */}
          <div className="pb-10">
            <TableWithDialog />
          </div>
"""

content = content.replace('          </div>\n        </div>\n      </main>', '          </div>\n' + insertion + '        </div>\n      </main>')

with open(filepath, "w") as f:
    f.write(content)
