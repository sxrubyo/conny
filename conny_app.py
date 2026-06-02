#!/usr/bin/env python3
"""conny — AI receptionist platform."""
from __future__ import annotations

import os, sys, time, json, subprocess, signal, random
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.theme import Theme
from rich.padding import Padding
from rich.progress import Progress, SpinnerColumn, TextColumn

from conny_design import (
    COLORS, LOGO_FULL, WORM_RESTING, SEP,
    ICON_ONLINE, ICON_OFFLINE, ICON_OK, ICON_ERR, ICON_WARN, ICON_BRAND,
    ICON_CORE, ICON_BOT, ICON_INT, ICON_OPS,
)

THEME = Theme({
    "m": f"bold {COLORS['primary']}",
    "m.dim": COLORS['secondary'],
    "ok": COLORS["success"],
    "warn": COLORS["warning"],
    "err": COLORS["error"],
    "dim": COLORS["dim"],
    "text": COLORS["text"],
})
con = Console(theme=THEME)

VERSION = "9.3.5"
try: VERSION = json.loads((Path(__file__).parent / "package.json").read_text()).get("version", VERSION)
except: pass

TAGLINES = [
    "Enterprise AI Receptionist",
    "Smart Conversational Interface",
    "Omni-channel Business Intelligence",
    "Autonomous Customer Engagement",
    "Scalable AI Agent Infrastructure",
]

BOOT_FILE = Path.home() / ".conny" / ".boot_shown"
APP_DIR = Path(os.environ.get("CONNY_DIR", str(Path(__file__).resolve().parent))).resolve()
INSTANCES_DIR = Path(os.environ.get("INSTANCES_DIR", str(Path.home() / ".conny" / "instances"))).resolve()


# ─── Boot ─────────────────────────────────────────────────────────────────────

def _should_boot():
    """Show boot animation once per session."""
    if not sys.stdout.isatty():
        return False
    if BOOT_FILE.exists():
        ts = BOOT_FILE.read_text().strip()
        if ts == time.strftime("%Y-%m-%d"):
            return False
    return True

def _mark_boot():
    BOOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOOT_FILE.write_text(time.strftime("%Y-%m-%d"))


# ─── Help (main screen) ──────────────────────────────────────────────────────

def cmd_help(args=""):
    # Boot animation (first time today)
    if _should_boot():
        try:
            from conny_worm import boot_sequence
            boot_sequence(duration=1.8)
            _mark_boot()
        except Exception:
            _mark_boot()

    con.print()
    con.print(LOGO_FULL)
    con.print(f"  {ICON_BRAND} v{VERSION}  [dim]·[/dim]  [m.dim]{random.choice(TAGLINES)}[/m.dim]       {WORM_RESTING}")
    con.print(SEP)

    # Live status
    procs = _pm2()
    online = [p for p in procs if "conny" in p.get("name","") and p.get("pm2_env",{}).get("status")=="online"]
    if online:
        for p in online:
            name = p["name"].replace("conny-","").replace("conny","main")
            up = _uptime(p.get("pm2_env",{}).get("pm_uptime",0))
            mem = p.get("monit",{}).get("memory",0)/1024/1024
            con.print(f"  {ICON_ONLINE} [bold]{name:30s}[/bold] [dim]{mem:.0f}M  {up}[/dim]")
    else:
        con.print(f"  {ICON_OFFLINE} [dim]No active Conny instances found[/dim]")
    con.print(SEP)

    # Commands
    sections = [
        (f"{ICON_CORE} CORE", [
            ("new",      "Launch a new instance",        "n"),
            ("list",     "See all your agents",          "l"),
            ("status",   "Check vital signs",            "s"),
            ("doctor",   "Auto-heal & diagnostics",      "d"),
            ("chat",     "Talk to Conny (monitor)",      "c"),
            ("logs",     "Live brain stream",            ""),
        ]),
        (f"{ICON_BOT} CONTROL", [
            ("persona",  "Design her personality",       ""),
            ("demo",     "Toggle simulation mode",       ""),
            ("modelo",   "Switch LLM provider",          ""),
            ("config",   "Deep settings",                ""),
            ("sync",     "Deploy latest upgrades",       ""),
        ]),
        (f"{ICON_INT} INTELLIGENCE", [
            ("aprender", "Teach new knowledge",          ""),
            ("gaps",     "Unanswered questions",         ""),
            ("reporte",  "Performance metrics",          ""),
            ("studio",   "Live session studio",          ""),
        ]),
        (f"{ICON_OPS} OPERATIONS", [
            ("restart",  "Quick reboot",                 "r"),
            ("stop",     "Shutdown instance",            ""),
            ("backup",   "Snapshot your agent",          ""),
            ("bridge",   "WhatsApp connection",          ""),
            ("pair",     "Connect Telegram bot",         ""),
        ]),
    ]


    for title, cmds in sections:
        con.print(f"  [dim]{title}[/dim]")
        for cmd, desc, sc in cmds:
            sc_text = f"[dim]{sc}[/dim]" if sc else ""
            con.print(f"    [m]{cmd:12s}[/m] [text]{desc:35s}[/text] {sc_text}")
        con.print()

    con.print(SEP)
    con.print(f"  [dim]shortcuts: n=new  l=list  s=status  d=doctor  c=chat  r=restart[/dim]")
    con.print(f"  [dim]docs: github.com/sxrubyo/conny[/dim]")
    con.print()


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_status(args=""):
    t = Table(box=box.SIMPLE, border_style=COLORS["primary"], show_edge=False, padding=(0,1))
    t.add_column("", width=3); t.add_column("instance", style="bold")
    t.add_column("status"); t.add_column("mem", justify="right", style="dim")
    t.add_column("up", justify="right", style="dim")
    for p in _pm2():
        if "conny" not in p.get("name",""): continue
        st = p.get("pm2_env",{}).get("status","?")
        mem = p.get("monit",{}).get("memory",0)/1024/1024
        up = _uptime(p.get("pm2_env",{}).get("pm_uptime",0))
        icon = ICON_ONLINE if st=="online" else ICON_OFFLINE
        st_s = f"[ok]{st}[/ok]" if st=="online" else f"[err]{st}[/err]"
        t.add_row(icon, p["name"], st_s, f"{mem:.0f}M", up)
    con.print(); con.print(Padding(t,(0,2))); con.print()

def cmd_list(args=""):
    idir = INSTANCES_DIR
    if not idir.exists(): con.print("  [dim]no instances[/dim]"); return
    t = Table(box=box.SIMPLE, border_style=COLORS["primary"], show_edge=False, padding=(0,1))
    t.add_column("", width=3); t.add_column("name", style="bold")
    t.add_column("port", style="dim"); t.add_column("sector", style="m.dim")
    for d in sorted(idir.iterdir()):
        if not d.is_dir() or not (d/".env").exists(): continue
        port=sector=""
        for l in (d/".env").read_text().splitlines():
            if l.startswith("PORT="): port=l.split("=",1)[1]
            if l.startswith("SECTOR="): sector=l.split("=",1)[1]
        t.add_row("[m]⬡[/m]", d.name, f":{port}" if port else "-", sector or "-")
    con.print(); con.print(Padding(t,(0,2))); con.print()

def cmd_doctor(args=""):
    _py("conny_doctor.py", *(args.split() if args.strip() else []))

def cmd_new(args=""): _py("conny_init.py")
def cmd_chat(args=""): _py("conny_studio.py", "--instance", args.strip() or "default")
def cmd_persona(args=""): _py("conny_persona_cli.py", *(args.split() if args else ["list"]))
def cmd_logs(args=""): _sh("pm2","logs",args.strip() or "conny","--lines","30","--nostream")
def cmd_sync(args=""): _py("conny_cli.py","sync")
def cmd_demo(args=""): _py("conny_cli.py","demo",args or "")
def cmd_modelo(args=""): _py("conny_cli.py","modelo",args or "")
def cmd_restart(args=""): _sh("pm2","restart",args.strip() or "conny")
def cmd_stop(args=""): _sh("pm2","stop",args.strip() or "conny")
def cmd_backup(args=""): _py("conny_cli.py","backup",args or "")
def cmd_bridge(args=""): _py("conny_cli.py","bridge",args or "")
def cmd_pair(args=""): _py("conny_cli.py","pair",args or "")
def cmd_reporte(args=""): _py("conny_weekly_report.py",args or "default")
def cmd_gaps(args=""):
    from datetime import datetime
    f=Path("knowledge_gaps")/f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    if not f.exists(): con.print(f"  {ICON_OK} [dim]no gaps[/dim]"); return
    con.print()
    for line in open(f):
        g=json.loads(line)
        con.print(f"  {ICON_WARN} {g.get('user_msg','')[:55]} [dim]({g.get('confidence',0):.0%})[/dim]")
    con.print()
def cmd_aprender(args=""):
    if not args or ("→" not in args and "->" not in args):
        con.print(f'  [dim]uso: conny aprender "pregunta" → "respuesta"[/dim]'); return
    sep="→" if "→" in args else "->"
    q,a=args.split(sep,1); q=q.strip().strip('"'); a=a.strip().strip('"')
    Path("teachings").mkdir(exist_ok=True)
    with open("teachings/default.jsonl","a") as f:
        f.write(json.dumps({"ts":time.time(),"question":q,"answer":a})+"\n")
    con.print(f"  {ICON_OK} [m]{q[:35]}[/m] → {a[:35]}")
def cmd_config(args=""):
    argv = ["config"]
    if args.strip():
        argv.extend(args.split())
    _py("conny_cli.py", *argv)


# ─── Router ──────────────────────────────────────────────────────────────────

CMDS = {
    "help":cmd_help,"--help":cmd_help,"-h":cmd_help,"?":cmd_help,
    "status":cmd_status,"s":cmd_status,
    "list":cmd_list,"l":cmd_list,
    "new":cmd_new,"init":cmd_new,"n":cmd_new,
    "doctor":cmd_doctor,"d":cmd_doctor,"doc":cmd_doctor,
    "chat":cmd_chat,"c":cmd_chat,"studio":cmd_chat,
    "persona":cmd_persona,"logs":cmd_logs,"demo":cmd_demo,
    "modelo":cmd_modelo,"sync":cmd_sync,"sincronizar":cmd_sync,
    "config":cmd_config,"gaps":cmd_gaps,"aprender":cmd_aprender,
    "reporte":cmd_reporte,"restart":cmd_restart,"r":cmd_restart,
    "stop":cmd_stop,"backup":cmd_backup,"bridge":cmd_bridge,"pair":cmd_pair,
}

def route(cmd, args=""):
    if cmd in ("--version","-v"): con.print(f"  conny v{VERSION}"); return
    fn = CMDS.get(cmd.lower())
    if fn: fn(args)
    else: _py("conny_cli.py", cmd, args)


# ─── Onboarding ──────────────────────────────────────────────────────────────

def first_run():
    return not Path(os.path.expanduser("~/.conny/initialized")).exists()

def onboard():
    con.print(); con.print(LOGO_FULL)
    con.print(f"\n  [bold]First time setup.[/bold] [dim]~3 minutes.[/dim]\n")
    cmd_new()
    Path(os.path.expanduser("~/.conny")).mkdir(parents=True,exist_ok=True)
    Path(os.path.expanduser("~/.conny/initialized")).write_text(time.strftime("%Y-%m-%d"))


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _pm2():
    try:
        r=subprocess.run(["pm2","jlist"],capture_output=True,text=True,timeout=5)
        return json.loads(r.stdout)
    except: return []

def _uptime(ms):
    if not ms: return "-"
    s=(time.time()*1000-ms)/1000
    if s<60: return f"{int(s)}s"
    if s<3600: return f"{int(s/60)}m"
    if s<86400: return f"{int(s/3600)}h"
    return f"{int(s/86400)}d"

def _py(*a):
    try:
        env = os.environ.copy()
        env.setdefault("CONNY_DIR", str(APP_DIR))
        env.setdefault("INSTANCES_DIR", str(INSTANCES_DIR))
        subprocess.run([sys.executable]+[str(x) for x in a],cwd=str(APP_DIR),env=env)
    except Exception as e: con.print(f"  [err]{e}[/err]")

def _sh(*a):
    try: subprocess.run(list(a))
    except Exception as e: con.print(f"  [err]{e}[/err]")


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    if len(sys.argv) <= 1:
        if first_run():
            onboard()
            return
        cmd_chat()
        return
    else:
        route(sys.argv[1], " ".join(sys.argv[2:]))

if __name__ == "__main__":
    main()
