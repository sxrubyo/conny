"""bublee_design.py — Single source of truth for all visual elements."""
from __future__ import annotations

COLORS = {
    "primary": "#b48ead",      # Lavender/Purple
    "secondary": "#81a1c1",    # Soft Blue
    "success": "#a3be8c",      # Sage Green
    "warning": "#ebcb8b",      # Muted Yellow
    "error": "#bf616a",        # Soft Red
    "dim": "#4c566a",          # Slate Grey
    "text": "#d8dee9",         # Snow Storm White
    "accent": "#88c0d0",       # Frost Cyan
}

LOGO_FULL = """\
[#b48ead] ██████╗  ██████╗ ███╗   ██╗███╗   ██╗██╗   ██╗[/#b48ead]
[#a690b8]██╔════╝ ██╔═══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝[/#a690b8]
[#9992c3]██║      ██║   ██║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝ [/#9992c3]
[#8b93ce]██║      ██║   ██║██║╚██╗██║██║╚██╗██║  ╚██╔╝  [/#8b93ce]
[#7d95d8]╚██████╗ ╚██████╔╝██║ ╚████║██║ ╚████║   ██║   [/#7d95d8]
[#6f97e3] ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝   [/#6f97e3]"""

WORM_RESTING = """\
[#b48ead]◆[/#b48ead][#4c566a]█▓▒░[/#4c566a]╮
       ╰─╯"""

WORM_INLINE = "[#b48ead]◆[/#b48ead][dim]▓▒░[/dim]"

SEP = "[dim]─────────────────────────────────────────────────────[/dim]"

# Status icons - using standard circles and marks for universal compatibility
ICON_ONLINE = "[#a3be8c]●[/#a3be8c]"
ICON_OFFLINE = "[#bf616a]○[/#bf616a]"
ICON_WARN = "[#ebcb8b]![/#ebcb8b]"
ICON_OK = "[#a3be8c]✓[/#a3be8c]"
ICON_ERR = "[#bf616a]✕[/#bf616a]"
ICON_BRAND = "[#b48ead]✦[/#b48ead]"

# Category icons - professional and clean
ICON_CORE = "■"
ICON_BOT = "⬢"
ICON_INT = "▲"
ICON_OPS = "◆"
