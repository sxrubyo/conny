"""
Conny Admin API — Multi-tenant runtime configuration endpoints.

Mounted at /admin on the main FastAPI app.
"""

import json
import os
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

log = logging.getLogger("conny.admin_api")

router = APIRouter(prefix="/admin", tags=["admin"])

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _get_admin_key() -> str:
    return os.environ.get("ADMIN_API_KEY") or os.environ.get("MASTER_API_KEY", "")


def _verify_auth(x_admin_key: Optional[str] = None, request: Optional[Request] = None):
    expected = _get_admin_key()
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured")
    
    token = x_admin_key
    if not token and request:
        token = request.query_params.get("key")
        
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid admin key")


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class PersonaUpdate(BaseModel):
    tone: str = "professional"
    verbosity: str = "concise"
    greeting_style: str = "warm"
    sign_off: str = ""
    forbidden_topics: List[str] = Field(default_factory=list)
    escalation_phrases: List[str] = Field(default_factory=list)


class ModelUpdate(BaseModel):
    provider: str = "anthropic"
    model_id: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 1024
    thinking_budget: int = 0


class TeachRequest(BaseModel):
    question: str
    answer: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_DIR = Path(__file__).resolve().parent
_PERSONAS_DIR = _BASE_DIR / "personas"
_MODEL_CONFIG_DIR = _BASE_DIR / "model_configs"
_KNOWLEDGE_GAPS_DIR = _BASE_DIR / "knowledge_gaps"
_TEACHINGS_DIR = _BASE_DIR / "teachings"


def _read_jsonl(path: Path, limit: int = 100) -> list:
    """Read last N lines from a JSONL file."""
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{instance_id}/persona")
async def update_persona(
    instance_id: str,
    body: PersonaUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    """Update personality/persona at runtime for a given instance."""
    _verify_auth(x_admin_key)

    persona_dir = _PERSONAS_DIR / instance_id
    persona_dir.mkdir(parents=True, exist_ok=True)

    override_path = persona_dir / "runtime_override.json"
    payload = body.model_dump()
    payload["updated_at"] = datetime.now().isoformat()

    override_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info(f"[admin] persona updated for {instance_id}")

    return {"ok": True, "applied": payload}


@router.post("/{instance_id}/model")
async def update_model(
    instance_id: str,
    body: ModelUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    """Change LLM provider/model configuration at runtime."""
    _verify_auth(x_admin_key)

    _MODEL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = _MODEL_CONFIG_DIR / f"{instance_id}.json"

    payload = body.model_dump()
    payload["updated_at"] = datetime.now().isoformat()

    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info(f"[admin] model config updated for {instance_id}: {body.provider}/{body.model_id}")

    return {"ok": True, "model": payload}


@router.get("/{instance_id}/status")
async def get_status(
    instance_id: str,
    x_admin_key: Optional[str] = Header(None),
):
    """Get current config and recent knowledge gaps for an instance."""
    _verify_auth(x_admin_key)

    # Read persona override
    persona_path = _PERSONAS_DIR / instance_id / "runtime_override.json"
    persona = {}
    if persona_path.exists():
        try:
            persona = json.loads(persona_path.read_text())
        except json.JSONDecodeError:
            persona = {"error": "corrupt persona file"}

    # Read model config
    model_path = _MODEL_CONFIG_DIR / f"{instance_id}.json"
    model = {}
    if model_path.exists():
        try:
            model = json.loads(model_path.read_text())
        except json.JSONDecodeError:
            model = {"error": "corrupt model config file"}

    # Read recent gaps
    today = datetime.now().strftime("%Y-%m-%d")
    gap_file = _KNOWLEDGE_GAPS_DIR / f"{today}.jsonl"
    all_gaps = _read_jsonl(gap_file, limit=200)
    instance_gaps = [g for g in all_gaps if g.get("instance_id") == instance_id][-10:]

    return {
        "instance_id": instance_id,
        "persona": persona,
        "model": model,
        "recent_gaps": instance_gaps,
        "gaps_today": len(instance_gaps),
    }


@router.get("/{instance_id}/gaps")
async def get_gaps(
    instance_id: str,
    x_admin_key: Optional[str] = Header(None),
    limit: int = 50,
):
    """Get knowledge gaps log for an instance."""
    _verify_auth(x_admin_key)

    _KNOWLEDGE_GAPS_DIR.mkdir(parents=True, exist_ok=True)

    # Collect from recent JSONL files
    gap_files = sorted(_KNOWLEDGE_GAPS_DIR.glob("*.jsonl"), reverse=True)[:7]
    all_gaps: list = []

    for gf in gap_files:
        entries = _read_jsonl(gf, limit=500)
        instance_entries = [e for e in entries if e.get("instance_id") == instance_id]
        all_gaps.extend(instance_entries)
        if len(all_gaps) >= limit:
            break

    all_gaps = all_gaps[:limit]

    return {
        "instance_id": instance_id,
        "total": len(all_gaps),
        "gaps": all_gaps,
    }


@router.post("/{instance_id}/teach")
async def teach_fact(
    instance_id: str,
    body: TeachRequest,
    x_admin_key: Optional[str] = Header(None),
):
    """Admin teaches Conny a new fact (question/answer pair)."""
    _verify_auth(x_admin_key)

    _TEACHINGS_DIR.mkdir(parents=True, exist_ok=True)
    teachings_file = _TEACHINGS_DIR / f"{instance_id}.jsonl"

    entry = {
        "ts": datetime.now().isoformat(),
        "question": body.question,
        "answer": body.answer,
    }

    with open(teachings_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    log.info(f"[admin] new teaching for {instance_id}: Q='{body.question[:60]}'")

    return {
        "ok": True,
        "instance_id": instance_id,
        "taught": entry,
    }


# ===========================================================================
# Real-Time Dashboard and Chat retrieval features
# ===========================================================================

def _get_db_path(instance_id: str) -> Path:
    """Robustly resolve SQLite database path for client sub-instances and main base dir."""
    instances_dir = Path("/home/ubuntu/conny-instances")
    instance_db = instances_dir / instance_id / "conny.db"
    if instance_db.exists():
        return instance_db
    
    base_dir = Path("/home/ubuntu/conny")
    ultra_db = base_dir / "conny_ultra.db"
    if ultra_db.exists():
        return ultra_db
        
    return base_dir / "conny_ultra.db"


def _query_db(db_path: Path, query: str, args: tuple = (), one: bool = False):
    """Run safety query against the SQLite database."""
    if not db_path.exists():
        return [] if not one else None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        log.error(f"[admin_api] DB Query Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")
    finally:
        conn.close()


@router.get("/{instance_id}/chats")
async def list_chats(
    instance_id: str,
    request: Request,
    x_admin_key: Optional[str] = Header(None),
):
    """Retrieve all active conversations and their latest messages for the sidebar."""
    _verify_auth(x_admin_key, request)
    db_path = _get_db_path(instance_id)
    
    query = """
        SELECT c.chat_id, c.role, c.content, c.model_used, c.tokens_used, c.latency_ms, c.ts
        FROM conversations c
        INNER JOIN (
            SELECT chat_id, MAX(id) as max_id
            FROM conversations
            GROUP BY chat_id
        ) latest ON c.id = latest.max_id
        ORDER BY c.id DESC;
    """
    rows = _query_db(db_path, query)
    
    count_query = "SELECT chat_id, COUNT(*) as msg_count FROM conversations GROUP BY chat_id;"
    counts = {r["chat_id"]: r["msg_count"] for r in _query_db(db_path, count_query)}
    
    chats = []
    for r in rows:
        chats.append({
            "chat_id": r["chat_id"],
            "last_role": r["role"],
            "last_content": r["content"],
            "model_used": r["model_used"],
            "tokens_used": r["tokens_used"],
            "latency_ms": r["latency_ms"],
            "ts": r["ts"],
            "msg_count": counts.get(r["chat_id"], 0)
        })
        
    return {"chats": chats}


@router.get("/{instance_id}/chats/{chat_id}")
async def get_chat_details(
    instance_id: str,
    chat_id: str,
    request: Request,
    x_admin_key: Optional[str] = Header(None),
):
    """Retrieve chronological turn-by-turn history of a specific conversation."""
    _verify_auth(x_admin_key, request)
    db_path = _get_db_path(instance_id)
    
    query = """
        SELECT id, role, content, analysis, tokens_used, model_used, latency_ms, ts
        FROM conversations
        WHERE chat_id = ?
        ORDER BY id ASC;
    """
    rows = _query_db(db_path, query, (chat_id,))
    
    messages = []
    for r in rows:
        analysis_data = {}
        if r["analysis"]:
            try:
                analysis_data = json.loads(r["analysis"])
            except Exception:
                analysis_data = {"raw": r["analysis"]}
                
        messages.append({
            "id": r["id"],
            "role": r["role"],
            "content": r["content"],
            "analysis": analysis_data,
            "tokens_used": r["tokens_used"],
            "model_used": r["model_used"],
            "latency_ms": r["latency_ms"],
            "ts": r["ts"],
        })
        
    return {
        "chat_id": chat_id,
        "messages": messages,
    }


@router.get("/{instance_id}/dashboard", response_class=HTMLResponse)
async def serve_dashboard(
    instance_id: str,
):
    """Serve the premium, real-time WhatsApp-styled chat dashboard."""
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conny Dashboard — Live Streams</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent: #00a884;
            --accent-hover: #008f72;
            --transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
            
            /* Dark Theme (Default) */
            --bg-main: #0b141a;
            --bg-sidebar: #111b21;
            --bg-header: #202c33;
            --bg-active: #2a3942;
            --bg-hover: #202c33;
            --text-primary: #e9edef;
            --text-secondary: #8696a0;
            --bubble-user: #005c4b;
            --bubble-conny: #202c33;
            --border: #222d34;
            --modal-bg: #222e35;
            --input-bg: #2a3942;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}

        body.light-theme {{
            /* Light Theme */
            --bg-main: #efeae2;
            --bg-sidebar: #ffffff;
            --bg-header: #f0f2f5;
            --bg-active: #ebebeb;
            --bg-hover: #f5f6f6;
            --text-primary: #111b21;
            --text-secondary: #667781;
            --bubble-user: #d9fdd3;
            --bubble-conny: #ffffff;
            --border: #e9edef;
            --modal-bg: #ffffff;
            --input-bg: #f0f2f5;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        body {{
            background-color: var(--bg-main);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            overflow: hidden;
            transition: var(--transition);
        }}

        /* Layout Structure */
        .sidebar {{
            width: 380px;
            min-width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            height: 100%;
            z-index: 10;
        }}

        .main-chat {{
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            background-color: var(--bg-main);
            position: relative;
        }}

        /* Headers styling */
        .header {{
            height: 64px;
            background-color: var(--bg-header);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
        }}

        .brand-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .live-indicator {{
            display: inline-block;
            width: 9px;
            height: 9px;
            background-color: var(--accent);
            border-radius: 50%;
            position: relative;
            box-shadow: 0 0 0 rgba(0, 168, 132, 0.4);
            animation: pulse-green 2s infinite;
        }}

        @keyframes pulse-green {{
            0% {{
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 168, 132, 0.7);
            }}
            70% {{
                transform: scale(1);
                box-shadow: 0 0 0 6px rgba(0, 168, 132, 0);
            }}
            100% {{
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 168, 132, 0);
            }}
        }}

        .brand-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }}

        .theme-toggle {{
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }}

        .theme-toggle:hover {{
            background-color: var(--bg-hover);
            color: var(--text-primary);
        }}

        /* Search area */
        .search-container {{
            padding: 8px 14px;
            border-bottom: 1px solid var(--border);
        }}

        .search-box {{
            width: 100%;
            background-color: var(--input-bg);
            border: none;
            border-radius: 8px;
            padding: 8px 12px 8px 36px;
            font-size: 0.9rem;
            color: var(--text-primary);
            outline: none;
            position: relative;
        }}

        .search-wrapper {{
            position: relative;
        }}

        .search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 0.95rem;
            pointer-events: none;
        }}

        /* Chat list */
        .chat-list {{
            flex: 1;
            overflow-y: auto;
        }}

        .chat-item {{
            display: flex;
            padding: 12px 16px;
            gap: 12px;
            cursor: pointer;
            border-bottom: 1px solid var(--border);
            transition: var(--transition);
        }}

        .chat-item:hover {{
            background-color: var(--bg-hover);
        }}

        .chat-item.active {{
            background-color: var(--bg-active);
        }}

        .avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00a884, #056162);
            color: white;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}

        .chat-info {{
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 4px;
        }}

        .chat-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chat-name {{
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .chat-time {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            flex-shrink: 0;
        }}

        .chat-bottom {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chat-preview {{
            font-size: 0.82rem;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
            margin-right: 8px;
        }}

        .badge {{
            background-color: var(--accent);
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            text-align: center;
        }}

        /* Chat window pane */
        .chat-pane {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background-image: radial-gradient(var(--border) 1px, transparent 0);
            background-size: 24px 24px;
            overflow-y: auto;
            padding: 24px;
            gap: 16px;
        }}

        .splash-screen {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: var(--bg-main);
            color: var(--text-secondary);
            gap: 16px;
            padding: 40px;
            text-align: center;
        }}

        .splash-logo {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent), #056162);
            color: white;
            font-size: 2.2rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow);
            margin-bottom: 8px;
        }}

        /* Message bubbles */
        .message-row {{
            display: flex;
            width: 100%;
            margin-bottom: 4px;
        }}

        .message-row.user-row {{
            justify-content: flex-end;
        }}

        .message-row.conny-row {{
            justify-content: flex-start;
        }}

        .bubble {{
            max-width: 65%;
            padding: 8px 12px 6px 12px;
            border-radius: 8px;
            font-size: 0.92rem;
            line-height: 1.45;
            position: relative;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            animation: fadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .user-row .bubble {{
            background-color: var(--bubble-user);
            color: var(--text-primary);
            border-top-right-radius: 0;
        }}

        .conny-row .bubble {{
            background-color: var(--bubble-conny);
            color: var(--text-primary);
            border-top-left-radius: 0;
            border: 1px solid var(--border);
        }}

        .bubble-text {{
            word-wrap: break-word;
            white-space: pre-wrap;
        }}

        .bubble-meta {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 4px;
            font-size: 0.68rem;
            color: var(--text-secondary);
            margin-top: 4px;
            user-select: none;
        }}

        /* Insights panel under Conny bubbles */
        .insights-container {{
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: -6px;
            margin-bottom: 12px;
            padding-left: 12px;
        }}

        .insights-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }}

        .pill {{
            font-size: 0.72rem;
            font-weight: 500;
            background-color: var(--bg-header);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 2px 8px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            user-select: none;
            transition: var(--transition);
        }}

        .pill-interactive {{
            cursor: pointer;
        }}

        .pill-interactive:hover {{
            background-color: var(--bg-active);
            color: var(--text-primary);
            border-color: var(--accent);
        }}

        /* Modals and forms */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(4px);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s ease;
        }}

        .modal-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .modal-content {{
            background-color: var(--modal-bg);
            width: 650px;
            max-width: 90%;
            max-height: 80vh;
            border-radius: 12px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transform: scale(0.95);
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .modal-overlay.active .modal-content {{
            transform: scale(1);
        }}

        .modal-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .modal-title {{
            font-size: 1.15rem;
            font-weight: 700;
        }}

        .modal-close {{
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
        }}

        .modal-close:hover {{
            color: var(--text-primary);
        }}

        .modal-body {{
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }}

        .json-viewer {{
            background-color: #0d1117;
            color: #c9d1d9;
            padding: 14px;
            border-radius: 8px;
            font-family: "Courier New", Courier, monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid var(--border);
            line-height: 1.4;
        }}

        /* API Key Overlay */
        .auth-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: var(--bg-main);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 20px;
            padding: 20px;
        }}

        .auth-card {{
            background-color: var(--bg-sidebar);
            border: 1px solid var(--border);
            border-radius: 12px;
            width: 400px;
            max-width: 100%;
            padding: 30px;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .auth-title {{
            font-size: 1.25rem;
            font-weight: 700;
            text-align: center;
        }}

        .auth-input {{
            width: 100%;
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background-color: var(--input-bg);
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: var(--transition);
        }}

        .auth-input:focus {{
            border-color: var(--accent);
        }}

        .auth-button {{
            background-color: var(--accent);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }}

        .auth-button:hover {{
            background-color: var(--accent-hover);
        }}

        .auth-error {{
            color: #ef4444;
            font-size: 0.85rem;
            text-align: center;
            display: none;
        }}

        /* Scrollbars */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(120, 120, 120, 0.3);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(120, 120, 120, 0.5);
        }}
    </style>
</head>
<body class="dark-theme">

    <!-- Auth Key Dialog Overlay -->
    <div id="auth-overlay" class="auth-overlay" style="display: none;">
        <div class="auth-card">
            <h2 class="auth-title">🔒 Acceso Requerido</h2>
            <p style="color: var(--text-secondary); font-size: 0.85rem; text-align: center; line-height: 1.4;">
                Ingresa tu MASTER_API_KEY o ADMIN_API_KEY para autenticar la transmisión en tiempo real.
            </p>
            <input type="password" id="auth-input" class="auth-input" placeholder="Ingresa Admin Key...">
            <button id="auth-submit" class="auth-button">Autenticar</button>
            <div id="auth-error" class="auth-error">Clave de administrador incorrecta. Inténtalo de nuevo.</div>
        </div>
    </div>

    <!-- Main Workspace -->
    <div class="sidebar">
        <div class="header">
            <div class="brand-section">
                <span class="live-indicator"></span>
                <span class="brand-title">Conny Live Streams</span>
            </div>
            <button id="theme-btn" class="theme-toggle">🌓</button>
        </div>
        
        <div class="search-container">
            <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" id="search-input" class="search-box" placeholder="Buscar conversación...">
            </div>
        </div>

        <div id="chat-list" class="chat-list">
            <!-- Dynamic Active Chats Render -->
            <div style="padding: 20px; text-align: center; color: var(--text-secondary); font-size: 0.85rem;">
                Cargando conversaciones...
            </div>
        </div>
    </div>

    <div class="main-chat">
        <!-- Selected Chat Header -->
        <div id="chat-header" class="header" style="display: none;">
            <div class="brand-section">
                <div class="avatar" id="header-avatar">C</div>
                <div>
                    <div class="brand-title" id="header-chat-id">chat_id</div>
                    <span id="header-msg-count" style="font-size: 0.75rem; color: var(--text-secondary)">0 mensajes</span>
                </div>
            </div>
            <div id="header-details" style="font-size: 0.8rem; color: var(--text-secondary)"></div>
        </div>

        <!-- Chat messages screen -->
        <div id="chat-pane" class="chat-pane">
            <div class="splash-screen">
                <div class="splash-logo">🤖</div>
                <h2>Transmisión de Conversaciones</h2>
                <p style="max-width: 400px; line-height: 1.4; font-size: 0.9rem;">
                    Selecciona una conversación del panel izquierdo para monitorear las respuestas de Conny en tiempo real, latencias y análisis cognitivo.
                </p>
            </div>
        </div>
    </div>

    <!-- Modal for Cognitive Raw Analysis -->
    <div id="analysis-modal" class="modal-overlay">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">🧠 Análisis Cognitivo de Conny</h3>
                <button id="modal-close-btn" class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.4;">
                    Representa el razonamiento interno en tiempo real realizado por Conny (confianza, intenciones, triggers de anti-loops y resguardos).
                </p>
                <div id="json-viewer" class="json-viewer"></div>
            </div>
        </div>
    </div>

    <script>
        const instanceId = "{instance_id}";
        let currentChatId = null;
        let adminKey = null;
        let chatsData = [];
        let pollingInterval = null;
        let lastMessageCount = 0;

        // Auto theme detection/handling
        const themeBtn = document.getElementById("theme-btn");
        themeBtn.addEventListener("click", () => {{
            document.body.classList.toggle("light-theme");
            localStorage.setItem("conny_theme", document.body.classList.contains("light-theme") ? "light" : "dark");
        }});
        
        if (localStorage.getItem("conny_theme") === "light") {{
            document.body.classList.add("light-theme");
        }}

        // Resolve Authorization Key
        function initAuth() {{
            const urlParams = new URLSearchParams(window.location.search);
            const keyParam = urlParams.get("key");
            const storedKey = localStorage.getItem("conny_admin_key");
            
            if (keyParam) {{
                adminKey = keyParam;
                localStorage.setItem("conny_admin_key", keyParam);
                startDashboard();
            }} else if (storedKey) {{
                adminKey = storedKey;
                startDashboard();
            }} else {{
                showAuthDialog();
            }}
        }}

        function showAuthDialog() {{
            const overlay = document.getElementById("auth-overlay");
            overlay.style.display = "flex";
            
            document.getElementById("auth-submit").addEventListener("click", submitAuth);
            document.getElementById("auth-input").addEventListener("keypress", (e) => {{
                if (e.key === "Enter") submitAuth();
            }});
        }}

        async function submitAuth() {{
            const input = document.getElementById("auth-input").value.trim();
            if (!input) return;
            
            // Validate admin key by fetching chats list
            try {{
                const res = await fetch(`/admin/${{instanceId}}/chats`, {{
                    headers: {{ "X-Admin-Key": input }}
                }});
                if (res.ok) {{
                    adminKey = input;
                    localStorage.setItem("conny_admin_key", input);
                    document.getElementById("auth-overlay").style.display = "none";
                    startDashboard();
                }} else {{
                    document.getElementById("auth-error").style.display = "block";
                }}
            }} catch (err) {{
                document.getElementById("auth-error").style.display = "block";
            }}
        }}

        // Run dashboard features
        function startDashboard() {{
            fetchChats();
            pollingInterval = setInterval(() => {{
                fetchChats(true);
                if (currentChatId) {{
                    fetchChatDetails(currentChatId, true);
                }}
            }}, 4000);
        }}

        // Fetch active chats for sidebar
        async function fetchChats(isPoll = false) {{
            try {{
                const res = await fetch(`/admin/${{instanceId}}/chats`, {{
                    headers: {{ "X-Admin-Key": adminKey }}
                }});
                if (res.status === 401) {{
                    clearInterval(pollingInterval);
                    localStorage.removeItem("conny_admin_key");
                    location.reload();
                    return;
                }}
                if (!res.ok) return;
                const data = await res.json();
                chatsData = data.chats || [];
                renderSidebar(isPoll);
            }} catch (err) {{
                console.error("Error fetching chats:", err);
            }}
        }}

        // Render left sidebar chat list
        function renderSidebar(isPoll = false) {{
            const searchVal = document.getElementById("search-input").value.toLowerCase();
            const container = document.getElementById("chat-list");
            
            const filtered = chatsData.filter(c => {{
                return c.chat_id.toLowerCase().includes(searchVal) || 
                       (c.last_content || "").toLowerCase().includes(searchVal);
            }});
            
            if (filtered.length === 0) {{
                container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-secondary); font-size:0.85rem;">Ningún chat encontrado</div>`;
                return;
            }}
            
            let html = "";
            filtered.forEach(chat => {{
                const isActive = chat.chat_id === currentChatId ? "active" : "";
                const dateStr = formatTimestamp(chat.ts);
                const roleIcon = chat.last_role === "user" ? "👤 " : "🤖 ";
                const initials = chat.chat_id.slice(-4);
                
                html += `
                    <div class="chat-item ${{isActive}}" onclick="selectChat('${{chat.chat_id}}')">
                        <div class="avatar">${{initials}}</div>
                        <div class="chat-info">
                            <div class="chat-top">
                                <span class="chat-name">${{chat.chat_id}}</span>
                                <span class="chat-time">${{dateStr}}</span>
                            </div>
                            <div class="chat-bottom">
                                <span class="chat-preview">${{roleIcon}}${{escapeHtml(chat.last_content || "")}}</span>
                                <span class="badge">${{chat.msg_count}}</span>
                            </div>
                        </div>
                    </div>
                `;
            }});
            
            container.innerHTML = html;
        }}

        // Search filter handling
        document.getElementById("search-input").addEventListener("input", () => renderSidebar(false));

        // Format dates beautifully
        function formatTimestamp(tsStr) {{
            if (!tsStr) return "";
            try {{
                const d = new Date(tsStr.replace(" ", "T"));
                if (isNaN(d.getTime())) return tsStr;
                return d.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
            }} catch (e) {{
                return tsStr;
            }}
        }}

        function escapeHtml(unsafe) {{
            return unsafe
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }}

        // Selection of active conversation
        function selectChat(chatId) {{
            currentChatId = chatId;
            lastMessageCount = 0;
            
            // Highlight active sidebar item
            const items = document.querySelectorAll(".chat-item");
            items.forEach(el => {{
                const name = el.querySelector(".chat-name").innerText;
                if (name === chatId) el.classList.add("active");
                else el.classList.remove("active");
            }});
            
            // Prepare header
            document.getElementById("chat-header").style.display = "flex";
            document.getElementById("header-chat-id").innerText = chatId;
            document.getElementById("header-avatar").innerText = chatId.slice(-4);
            
            const pane = document.getElementById("chat-pane");
            pane.innerHTML = `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--text-secondary);">Cargando mensajes de ${{chatId}}...</div>`;
            
            fetchChatDetails(chatId, false);
        }}

        // Fetch details from sqlite for selected chat_id
        async function fetchChatDetails(chatId, isPoll = false) {{
            if (chatId !== currentChatId) return;
            try {{
                const res = await fetch(`/admin/${{instanceId}}/chats/${{chatId}}`, {{
                    headers: {{ "X-Admin-Key": adminKey }}
                }});
                if (!res.ok) return;
                const data = await res.json();
                renderMessages(data.messages || [], isPoll);
            }} catch (err) {{
                console.error("Error fetching chat details:", err);
            }}
        }}

        // Render bubbles in thread pane
        function renderMessages(messages, isPoll = false) {{
            const pane = document.getElementById("chat-pane");
            
            if (messages.length === 0) {{
                pane.innerHTML = `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--text-secondary);">Ningún mensaje en esta conversación</div>`;
                return;
            }}

            // Only update DOM if message count or last message content has changed
            if (isPoll && messages.length === lastMessageCount) {{
                return;
            }}

            const wasAtBottom = pane.scrollHeight - pane.scrollTop <= pane.clientHeight + 100;
            
            let html = "";
            let connyTurns = [];
            
            messages.forEach((msg, idx) => {{
                const timeStr = formatTimestamp(msg.ts);
                
                if (msg.role === "user") {{
                    // Render user bubbles directly
                    html += `
                        <div class="message-row user-row">
                            <div class="bubble">
                                <div class="bubble-text">${{escapeHtml(msg.content)}}</div>
                                <div class="bubble-meta">
                                    <span>${{timeStr}}</span>
                                    <span>✓✓</span>
                                </div>
                            </div>
                        </div>
                    `;
                }} else {{
                    // Split Conny bubbles using " ||| " separator
                    const bubbles = msg.content.split(" ||| ");
                    bubbles.forEach((bubbleText, bIdx) => {{
                        html += `
                            <div class="message-row conny-row">
                                <div class="bubble">
                                    <div class="bubble-text">${{escapeHtml(bubbleText)}}</div>
                                    <div class="bubble-meta">
                                        <span>${{timeStr}}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }});
                    
                    // Render cognitive insights pills directly under final bubble of the assistant turn
                    const latencySec = msg.latency_ms ? (msg.latency_ms / 1000).toFixed(1) + "s" : "N/A";
                    const modelName = msg.model_used || "conny-brain";
                    const tokens = msg.tokens_used ? msg.tokens_used + " tokens" : "N/A";
                    const analysisStr = JSON.stringify(msg.analysis);
                    
                    html += `
                        <div class="insights-container">
                            <div class="insights-row">
                                <div class="pill">🤖 ${{modelName}}</div>
                                <div class="pill">⚡ ${{latencySec}}</div>
                                <div class="pill">🪙 ${{tokens}}</div>
                                <div class="pill pill-interactive" onclick='showAnalysis(${{escapeHtmlAttribute(analysisStr)}})'>🧠 Razonamiento</div>
                            </div>
                        </div>
                    `;
                }}
            }});
            
            pane.innerHTML = html;
            document.getElementById("header-msg-count").innerText = `${{messages.length}} mensajes`;
            
            // Auto scroll down if user was already at the bottom or if it's the first click
            if (!isPoll || wasAtBottom || lastMessageCount === 0) {{
                pane.scrollTop = pane.scrollHeight;
            }}
            
            lastMessageCount = messages.length;
        }}

        function escapeHtmlAttribute(str) {{
            return str
                .replace(/'/g, "&apos;")
                .replace(/"/g, "&quot;");
        }}

        // Cognitive modal functions
        function showAnalysis(analysisObj) {{
            const modal = document.getElementById("analysis-modal");
            const viewer = document.getElementById("json-viewer");
            
            let prettyJson = "";
            try {{
                prettyJson = JSON.stringify(analysisObj, null, 2);
            }} catch (e) {{
                prettyJson = String(analysisObj);
            }}
            
            viewer.innerText = prettyJson;
            modal.classList.add("active");
        }}

        // Modal triggers
        document.getElementById("modal-close-btn").addEventListener("click", hideModal);
        document.getElementById("analysis-modal").addEventListener("click", (e) => {{
            if (e.target.id === "analysis-modal") hideModal();
        }});

        function hideModal() {{
            document.getElementById("analysis-modal").classList.remove("active");
        }}

        // Fire auth on page load
        window.addEventListener("DOMContentLoaded", initAuth);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)
