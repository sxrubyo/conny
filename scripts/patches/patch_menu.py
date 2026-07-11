with open('/home/ubuntu/bublee-dev-react/src/components/ui/menu.tsx', 'r') as f:
    content = f.read()

content = content.replace("import { motion } from 'framer-motion';", "import { motion, Variants } from 'framer-motion';")
content = content.replace("const sidebarVariants = {", "const sidebarVariants: Variants = {")
content = content.replace("const itemVariants = {", "const itemVariants: Variants = {")

with open('/home/ubuntu/bublee-dev-react/src/components/ui/menu.tsx', 'w') as f:
    f.write(content)
