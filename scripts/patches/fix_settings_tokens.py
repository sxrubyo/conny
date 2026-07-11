import re

filename = '/home/ubuntu/bublee-dev-react/src/app/settings/page.tsx'
with open(filename, 'r') as f:
    content = f.read()

# Add Copy icon
content = content.replace('Key } from "lucide-react";', 'Key, Copy } from "lucide-react";')

# Update Token List
old_tokens = """                                            <div key={token.id} className="flex items-center justify-between p-3 bg-[#252525] border border-[#333] rounded-[8px]">
                                                <div className="flex items-center gap-3">
                                                    <Key className="w-4 h-4 text-[#888]" />
                                                    <div>
                                                        <p className="text-[13px] font-medium">{token.clinic_label}</p>
                                                        <p className="text-[#666] text-[11px] font-mono mt-0.5">{token.key_hint}</p>
                                                    </div>
                                                </div>
                                                <button 
                                                    onClick={() => handleDeleteToken(token.id)}
                                                    className="p-1.5 text-[#666] hover:text-[#f87171] hover:bg-[#f87171]/10 rounded-[4px] transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>"""

new_tokens = """                                            <div key={token.token} className="flex items-center justify-between p-3 bg-[#252525] border border-[#333] rounded-[8px]">
                                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                                    <Key className="w-4 h-4 text-[#888] flex-shrink-0" />
                                                    <div className="min-w-0 flex-1 pr-4">
                                                        <p className="text-[13px] font-medium">{token.clinic_label}</p>
                                                        <div className="flex items-center gap-2 mt-0.5">
                                                            <p className="text-[#888] text-[11px] font-mono truncate">{token.token}</p>
                                                            <button 
                                                                onClick={() => { navigator.clipboard.writeText(token.token); alert('Token copied!'); }}
                                                                className="text-[#e05a2b] hover:text-[#c94e24] transition-colors flex-shrink-0" title="Copy Token"
                                                            >
                                                                <Copy className="w-3 h-3" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                                <button 
                                                    onClick={() => handleDeleteToken(token.token)}
                                                    className="p-1.5 text-[#666] hover:text-[#f87171] hover:bg-[#f87171]/10 rounded-[4px] transition-colors flex-shrink-0"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>"""

content = content.replace(old_tokens, new_tokens)

# Update delete logic
content = content.replace('setTokens(tokens.filter(t => t.id !== tokenId));', 'setTokens(tokens.filter(t => t.token !== tokenId));')

with open(filename, 'w') as f:
    f.write(content)
