import re

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'r') as f:
    content = f.read()

content = content.replace('import { Bell, Search, Calendar, ArrowUpRight, ArrowDownRight, Sun, Moon } from "lucide-react";', 'import { Bell, Search, Calendar, ArrowUpRight, ArrowDownRight, Sun, Moon, ChevronLeft } from "lucide-react";')

with open('/home/ubuntu/bublee-dev-react/src/app/panel/page.tsx', 'w') as f:
    f.write(content)
