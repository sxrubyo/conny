from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Dict, List

class AdminSoulMemory:
    """Professional SQL-based memory for the operator layer."""

    def __init__(self):
        try:
            from src.core.globals import db
            self.db = db
            self._ensure_tables()
        except ImportError:
            pass

    def _ensure_tables(self):
        if not self.db: return
        with self.db._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS admin_soul_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                ts TEXT DEFAULT (datetime('now'))
            )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_admin_soul_chat ON admin_soul_memory(chat_id)")

    def load_context(self, chat_id: str, limit_chars: int = 4000) -> str:
        if not hasattr(self, 'db') or not self.db: return ""
        chunks: List[str] = []
        
        profile = self.db.get_admin_profile(chat_id)
        if profile and (profile.get("name") or profile.get("preferences")):
            profile_lines = []
            if profile.get("name"): profile_lines.append(f"Name: {profile['name']}")
            if profile.get("preferences"): profile_lines.append(f"Prefs: {json.dumps(profile['preferences'], ensure_ascii=False)}")
            chunks.append(f"## Perfil del admin\n" + "\n".join(profile_lines))

        with self.db._conn() as c:
            for cat, title in [("business_facts", "Datos enseñados por el admin"), ("ops_memory", "Memoria operativa")]:
                rows = c.execute("SELECT ts, content FROM admin_soul_memory WHERE chat_id=? AND category=? ORDER BY id DESC LIMIT 50", (str(chat_id), cat)).fetchall()
                if rows:
                    rows.reverse()
                    lines = [f"- {r['ts']}: {r['content']}" for r in rows]
                    chunks.append(f"## {title}\n" + "\n".join(lines)[-limit_chars:])
                    
        return "\n\n".join(chunks)[-limit_chars:]

    def remember_turn(
        self,
        *,
        chat_id: str,
        admin_text: str,
        bublee_reply: str,
        clinic: Dict[str, Any],
    ) -> None:
        if not hasattr(self, 'db') or not self.db: return
        now = datetime.utcnow().isoformat() + "Z"
        text_low = admin_text.lower()
        
        with self.db._conn() as c:
            if any(token in text_low for token in ("precio", "horario", "cliente", "servicio", "api", "instancia", "demo", "token", "llave", "key")):
                c.execute(
                    "INSERT INTO admin_soul_memory (chat_id, category, content, ts) VALUES (?, ?, ?, ?)",
                    (str(chat_id), "business_facts", admin_text.strip(), now)
                )

            if any(token in text_low for token in ("bug", "error", "falla", "terminal", "pm2", "webhook", "telegram", "whatsapp", "fallo", "excepcion", "memoria")):
                c.execute(
                    "INSERT INTO admin_soul_memory (chat_id, category, content, ts) VALUES (?, ?, ?, ?)",
                    (str(chat_id), "ops_memory", admin_text.strip(), now)
                )
