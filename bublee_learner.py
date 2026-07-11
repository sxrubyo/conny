"""
Bublee Learner — Motor de auto-mejora continua.

Cada conversación en demo es una oportunidad de aprendizaje:
1. Registra cómo escriben los humanos reales (patrones, preguntas, objeciones)
2. Detecta situaciones nuevas que no manejó bien
3. Guarda "lecciones" que se inyectan en producción
4. En modo /dreams: consolida todo lo aprendido y reescribe prompts

Esto alimenta directamente la calidad de producción para los clientes del admin.
"""
from __future__ import annotations
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("bublee.learner")

LEARNINGS_DIR = Path(os.getenv("LEARNINGS_DIR", "/home/ubuntu/bublee/instances/clinica-de-las-americas/learnings"))
LEARNINGS_DIR.mkdir(exist_ok=True)


class BubleeLearner:
    """Aprende de cada interacción para mejorar continuamente."""

    def __init__(self):
        self.session_learnings: List[Dict] = []
        self._load_existing()

    def _load_existing(self):
        """Carga lecciones previas."""
        patterns_file = LEARNINGS_DIR / "patterns.json"
        if patterns_file.exists():
            try:
                self.patterns = json.loads(patterns_file.read_text())
            except:
                self.patterns = {"objections": [], "questions": [], "styles": [], "failures": []}
        else:
            self.patterns = {"objections": [], "questions": [], "styles": [], "failures": []}

    def observe_interaction(self, user_msg: str, bublee_response: str,
                           user_reacted_well: bool = True, chat_id: str = ""):
        """
        Observa una interacción y extrae aprendizajes.
        Se llama después de cada respuesta enviada.
        """
        learning = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_msg": user_msg[:200],
            "bublee_response": bublee_response[:200],
            "positive": user_reacted_well,
            "chat_id": chat_id[:20],
        }

        # Detectar tipo de interacción
        user_lower = user_msg.lower().strip()

        # Objeciones detectadas
        objection_signals = [
            "no entiendo", "no me interesa", "es un bot", "eso es spam",
            "para que", "por que", "quien te dio", "no gracias",
            "i don't understand", "not interested", "is this spam",
        ]
        for signal in objection_signals:
            if signal in user_lower:
                learning["type"] = "objection"
                learning["objection"] = signal
                self.patterns["objections"].append(learning)
                break

        # Preguntas frecuentes
        question_signals = ["cuanto cuesta", "como funciona", "que hace", "how much", "how does"]
        for signal in question_signals:
            if signal in user_lower:
                learning["type"] = "faq"
                self.patterns["questions"].append(learning)
                break

        # Estilo de escritura del usuario (para mirroring database)
        style = self._analyze_style(user_msg)
        if style:
            learning["type"] = "style"
            learning["style"] = style
            self.patterns["styles"].append(learning)

        # Si la reacción fue negativa, guardar como failure
        if not user_reacted_well:
            learning["type"] = "failure"
            self.patterns["failures"].append(learning)

        self.session_learnings.append(learning)

        # Auto-save cada 10 interacciones
        if len(self.session_learnings) % 10 == 0:
            self._save()

    def _analyze_style(self, text: str) -> Optional[Dict]:
        """Analiza el estilo de escritura de un usuario."""
        if len(text) < 3:
            return None

        return {
            "length": len(text),
            "has_emoji": any(ord(c) > 0x1F600 for c in text),
            "all_caps": text.isupper(),
            "no_caps": text.islower(),
            "has_question": "?" in text,
            "language": "en" if any(w in text.lower() for w in ["the", "what", "how", "is"]) else "es",
            "formal": any(w in text.lower() for w in ["usted", "quisiera", "podría", "would", "could"]),
        }

    def get_insights(self) -> str:
        """Genera insights para inyectar en el prompt de producción."""
        insights = []

        # Top objeciones
        if self.patterns["objections"]:
            top_obj = {}
            for o in self.patterns["objections"][-50:]:
                key = o.get("objection", "unknown")
                top_obj[key] = top_obj.get(key, 0) + 1
            sorted_obj = sorted(top_obj.items(), key=lambda x: x[1], reverse=True)[:5]
            insights.append(f"Objeciones frecuentes: {', '.join(f'{k}({v}x)' for k,v in sorted_obj)}")

        # Failures para evitar
        if self.patterns["failures"]:
            insights.append(f"Respuestas que no funcionaron: {len(self.patterns['failures'])} registradas")

        # Estilo promedio
        if self.patterns["styles"]:
            recent = self.patterns["styles"][-20:]
            avg_len = sum(s["style"]["length"] for s in recent) / len(recent)
            formal_pct = sum(1 for s in recent if s["style"].get("formal")) / len(recent)
            insights.append(f"Longitud promedio de msgs: {avg_len:.0f} chars, formalidad: {formal_pct:.0%}")

        return " | ".join(insights) if insights else "Sin datos suficientes aún"

    def _save(self):
        """Guarda patrones a disco."""
        try:
            # Keep only last 200 of each type
            for key in self.patterns:
                self.patterns[key] = self.patterns[key][-200:]

            (LEARNINGS_DIR / "patterns.json").write_text(
                json.dumps(self.patterns, ensure_ascii=False, indent=2)
            )
            log.info(f"[learner] saved {sum(len(v) for v in self.patterns.values())} patterns")
        except Exception as e:
            log.warning(f"[learner] save error: {e}")

    def dream_consolidate(self) -> Dict:
        """
        Modo /dreams — consolidación nocturna.
        Analiza todo lo aprendido y genera recomendaciones de mejora.
        """
        self._save()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_interactions": len(self.session_learnings),
            "objections_count": len(self.patterns["objections"]),
            "failures_count": len(self.patterns["failures"]),
            "insights": self.get_insights(),
            "recommendations": [],
        }

        # Generar recomendaciones
        if self.patterns["failures"]:
            report["recommendations"].append(
                "Revisar respuestas que generaron reacción negativa y ajustar tono"
            )

        if self.patterns["objections"]:
            common = {}
            for o in self.patterns["objections"]:
                k = o.get("objection", "")
                common[k] = common.get(k, 0) + 1
            top = max(common, key=common.get) if common else ""
            if top:
                report["recommendations"].append(
                    f"La objeción más común es '{top}' — reforzar respuesta para ese caso"
                )

        # Save dream report
        dream_file = LEARNINGS_DIR / f"dream_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        dream_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))

        return report


# Singleton
bublee_learner = BubleeLearner()
