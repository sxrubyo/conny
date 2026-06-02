from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _safe_id(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.@-]+", "_", str(value or "").strip())
    return clean[:96] or "unknown"


class AdminSoulMemory:
    """Filesystem memory for the operator layer, inspired by OpenClaw-style soul folders."""

    def __init__(self, root: str | Path = "soul/admins"):
        self.root = Path(root)

    def admin_dir(self, chat_id: str) -> Path:
        path = self.root / _safe_id(chat_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def load_context(self, chat_id: str, limit_chars: int = 4000) -> str:
        base = self.admin_dir(chat_id)
        chunks: List[str] = []
        for filename, title in (
            ("profile.json", "Perfil del admin"),
            ("business_facts.md", "Datos enseñados por el admin"),
            ("ops_memory.md", "Memoria operativa"),
        ):
            path = base / filename
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    chunks.append(f"## {title}\n{text[-limit_chars:]}")
        return "\n\n".join(chunks)[-limit_chars:]

    def remember_turn(
        self,
        *,
        chat_id: str,
        admin_text: str,
        conny_reply: str,
        clinic: Dict[str, Any],
    ) -> None:
        base = self.admin_dir(chat_id)
        now = datetime.utcnow().isoformat() + "Z"

        profile_path = base / "profile.json"
        profile = {}
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
            except Exception:
                profile = {}
        profile.update(
            {
                "chat_id": str(chat_id),
                "last_seen_at": now,
                "clinic_name": clinic.get("name", ""),
                "setup_done": bool(clinic.get("setup_done")),
            }
        )
        profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

        conversation_path = base / "conversation_log.jsonl"
        with conversation_path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": now,
                        "admin": admin_text,
                        "conny": conny_reply,
                        "clinic": clinic.get("name", ""),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        text_low = admin_text.lower()
        if any(token in text_low for token in ("precio", "horario", "cliente", "servicio", "api", "instancia", "demo")):
            facts_path = base / "business_facts.md"
            with facts_path.open("a", encoding="utf-8") as fh:
                fh.write(f"\n- {now}: {admin_text.strip()}\n")

        if any(token in text_low for token in ("bug", "error", "falla", "terminal", "pm2", "webhook", "telegram", "whatsapp")):
            ops_path = base / "ops_memory.md"
            with ops_path.open("a", encoding="utf-8") as fh:
                fh.write(f"\n- {now}: {admin_text.strip()}\n")
