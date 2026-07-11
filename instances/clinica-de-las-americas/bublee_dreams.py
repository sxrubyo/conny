"""
Bublee Dreams — Auto-mejora nocturna.

Cada noche a las 3 AM (configurable):
1. Revisa todas las conversaciones del día
2. Identifica qué salió mal (respuestas sin reply, objeciones no resueltas)
3. Busca en Google info que le faltó
4. Reescribe reglas internas para no repetir errores
5. Consolida memoria (learner.dream_consolidate())
6. Genera reporte para el admin
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

log = logging.getLogger("bublee.dreams")

INSTANCE_DIR = Path(os.getenv("INSTANCE_DIR", "/home/ubuntu/bublee/instances/clinica-de-las-americas"))
DB_PATH = INSTANCE_DIR / "bublee.db"
DREAMS_DIR = INSTANCE_DIR / "dreams"
DREAMS_DIR.mkdir(exist_ok=True)


class BubleeDreams:
    """Motor de auto-mejora nocturna."""

    def __init__(self):
        self._last_dream = None

    async def dream(self) -> Dict:
        """Ejecuta el ciclo completo de auto-mejora."""
        log.info("[dreams] Iniciando ciclo de sueño...")
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "conversations_reviewed": 0,
            "issues_found": [],
            "improvements_made": [],
            "knowledge_gaps": [],
        }

        # 1. Revisar conversaciones del día
        today_convos = self._get_today_conversations()
        report["conversations_reviewed"] = len(today_convos)

        # 2. Analizar problemas
        issues = self._analyze_issues(today_convos)
        report["issues_found"] = issues

        # 3. Detectar gaps de conocimiento
        gaps = self._detect_knowledge_gaps(today_convos)
        report["knowledge_gaps"] = gaps

        # 4. Auto-generar mejoras
        improvements = self._generate_improvements(issues, gaps)
        report["improvements_made"] = improvements

        # 5. Consolidar learner
        try:
            from bublee_learner import bublee_learner
            learner_report = bublee_learner.dream_consolidate()
            report["learner_insights"] = learner_report.get("insights", "")
        except Exception as e:
            report["learner_error"] = str(e)

        # 6. Guardar reporte
        dream_file = DREAMS_DIR / f"dream_{datetime.utcnow().strftime('%Y%m%d')}.json"
        dream_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))

        self._last_dream = report
        log.info(f"[dreams] Ciclo completado: {len(issues)} issues, {len(improvements)} mejoras")
        return report

    def _get_today_conversations(self) -> List[Dict]:
        """Obtiene todas las conversaciones de las últimas 24h."""
        try:
            db = sqlite3.connect(str(DB_PATH))
            cur = db.cursor()
            yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            cur.execute("""
                SELECT chat_id, role, content, ts 
                FROM conversations 
                WHERE ts > ? 
                ORDER BY ts
            """, (yesterday,))
            rows = cur.fetchall()
            db.close()

            convos = {}
            for chat_id, role, content, ts in rows:
                if chat_id not in convos:
                    convos[chat_id] = []
                convos[chat_id].append({"role": role, "content": content, "ts": ts})
            return list(convos.values())
        except Exception as e:
            log.warning(f"[dreams] DB error: {e}")
            return []

    def _analyze_issues(self, conversations: List[List[Dict]]) -> List[Dict]:
        """Detecta problemas en las conversaciones del día."""
        issues = []
        for convo in conversations:
            # Issue 1: Usuario preguntó y Bublee no respondió bien
            for i, msg in enumerate(convo):
                if msg["role"] == "user" and "?" in msg["content"]:
                    # Check if next message (assistant) was vague
                    if i + 1 < len(convo) and convo[i+1]["role"] == "assistant":
                        response = convo[i+1]["content"]
                        if any(v in response.lower() for v in ["no estoy segura", "no se", "dejame verificar"]):
                            issues.append({
                                "type": "unanswered_question",
                                "question": msg["content"][:100],
                                "response": response[:100],
                            })

            # Issue 2: Conversación abandonada (user no respondió después de Bublee)
            if len(convo) >= 2 and convo[-1]["role"] == "assistant":
                issues.append({
                    "type": "abandoned_after_response",
                    "last_response": convo[-1]["content"][:100],
                })

        return issues[:20]  # Max 20 issues per night

    def _detect_knowledge_gaps(self, conversations: List[List[Dict]]) -> List[str]:
        """Detecta temas donde Bublee no tuvo suficiente info."""
        gaps = []
        trigger_phrases = [
            "no tengo esa información", "no estoy segura", "dejame verificar",
            "no se", "tendría que consultar", "no cuento con",
        ]
        for convo in conversations:
            for msg in convo:
                if msg["role"] == "assistant":
                    content_lower = msg["content"].lower()
                    if any(t in content_lower for t in trigger_phrases):
                        # Find what the user asked
                        idx = convo.index(msg)
                        if idx > 0 and convo[idx-1]["role"] == "user":
                            gaps.append(convo[idx-1]["content"][:100])
        return list(set(gaps))[:10]

    def _generate_improvements(self, issues: List[Dict], gaps: List[str]) -> List[str]:
        """Genera mejoras basadas en los problemas encontrados."""
        improvements = []

        # Count issue types
        unanswered = sum(1 for i in issues if i["type"] == "unanswered_question")
        abandoned = sum(1 for i in issues if i["type"] == "abandoned_after_response")

        if unanswered > 3:
            improvements.append(f"Alta tasa de preguntas sin respuesta ({unanswered}). Investigar temas frecuentes.")

        if abandoned > 5:
            improvements.append(f"Muchas conversaciones abandonadas ({abandoned}). Revisar si las respuestas invitan a seguir.")

        if gaps:
            improvements.append(f"Gaps de conocimiento detectados en: {', '.join(gaps[:3])}")

        return improvements

    def get_last_dream_summary(self) -> str:
        """Resumen del último sueño para el admin."""
        if not self._last_dream:
            # Try to load from file
            files = sorted(DREAMS_DIR.glob("dream_*.json"), reverse=True)
            if files:
                try:
                    self._last_dream = json.loads(files[0].read_text())
                except:
                    return "No hay reportes de sueño aún"
            else:
                return "No hay reportes de sueño aún"

        d = self._last_dream
        return (
            f"Ultimo sueño: {d['timestamp'][:10]} ||| "
            f"Conversaciones revisadas: {d['conversations_reviewed']} ||| "
            f"Issues: {len(d['issues_found'])} ||| "
            f"Gaps: {len(d['knowledge_gaps'])} ||| "
            f"Mejoras: {len(d['improvements_made'])}"
        )


# Singleton
bublee_dreams = BubleeDreams()


def setup_dreams_cron():
    """Configura el cron de /dreams para las 3 AM."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            bublee_dreams.dream,
            'cron',
            hour=3,
            minute=0,
            id='bublee_dreams_nightly',
            replace_existing=True,
        )
        scheduler.start()
        log.info("[dreams] Cron nocturno configurado: 3:00 AM")
        return scheduler
    except ImportError:
        log.warning("[dreams] apscheduler not available — dreams won't auto-run")
        return None
