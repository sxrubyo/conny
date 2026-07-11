import re

filename = '/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

if 'useSearchParams' not in content:
    content = content.replace('import { useState, useEffect, useRef } from "react";', 'import { useState, useEffect, useRef, Suspense } from "react";\nimport { useSearchParams } from "next/navigation";')
    
    # We need to wrap the SettingsContent in a Suspense, or just use useSearchParams inside it.
    # To keep it simple in Next.js 14 client components, useSearchParams must be in a Suspense boundary if statically exported, but this is SSR probably.
    
    # Actually, we can just check window.location.search in useEffect to avoid Suspense issues entirely.
    effect = """
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('tab')) {
      setActiveTab(params.get('tab') as string);
    }
"""
    content = content.replace('useEffect(() => {\n    setIsDark', effect + '\n    setIsDark')

with open(filename, 'w') as f:
    f.write(content)
