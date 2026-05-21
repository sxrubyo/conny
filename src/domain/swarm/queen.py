import asyncio
import logging
from typing import Dict, Any, List, Optional
from src.core.globals import llm_engine

log = logging.getLogger("conny.swarm")

class Agent:
    def __init__(self, name: str, role: str, instruction: str):
        self.name = name
        self.role = role
        self.instruction = instruction

    async def execute(self, task: str, context: Dict[str, Any]) -> str:
        prompt = f"Role: {self.role}\nInstruction: {self.instruction}\nContext: {context}\nTask: {task}"
        log.info(f"[{self.name}] Executing task...")
        # Llama al motor LLM real usando complete
        messages = [{"role": "user", "content": prompt}]
        response, _ = await llm_engine.complete(messages, model_tier="fast")
        log.info(f"[{self.name}] Raw response: {response}")
        return response

class QueenCoordinator:
    """
    Coordina el enjambre jerárquico (Swarm V3).
    Evita el 'drift' (desvío de instrucciones) dividiendo el trabajo.
    """
    def __init__(self):
        self.research_agent = Agent(
            name="ResearchAgent",
            role="Analista de Conocimiento",
            instruction="Busca en la base de datos de FAQs o en el contexto del paciente para extraer hechos exactos."
        )
        self.response_agent = Agent(
            name="ResponseAgent",
            role="Generador de Respuestas",
            instruction="Sintetiza la respuesta final basándose únicamente en los hechos encontrados, adoptando el tono de la clínica. Evita cualquier frase preprogramada o robótica."
        )
        self.reviewer_agent = Agent(
            name="ReviewerAgent",
            role="Auditor de Calidad",
            instruction="Verifica la respuesta generada. Quita cualquier fragmento que suene a robot o call center. Devuelve ÚNICAMENTE un array de strings en formato JSON con los mensajes finales que recibirá el cliente (ejemplo: [\"¡Hola! Claro que sí.\", \"¿Te viene bien por la tarde?\"]). No devuelvas bloques de auditoría, objetos con llaves o explicaciones extra."
        )

    def _clean_json_text(self, text: str) -> str:
        """Limpia bloques de código markdown si los hay."""
        text = text.strip()
        if text.startswith("```"):
            # Quitar primera línea de bloque de código
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    async def process(self, user_message: str, clinic_context: Dict[str, Any]) -> List[str]:
        log.info("[swarm] Queen ha recibido un mensaje, coordinando enjambre...")
        
        # 1. Investigación
        facts = await self.research_agent.execute(f"Extrae datos relevantes para responder a: '{user_message}'", clinic_context)
        
        # 2. Generación
        draft_context = {"user_message": user_message, "facts": facts, "clinic": clinic_context}
        draft_response = await self.response_agent.execute("Escribe la respuesta final en JSON", draft_context)
        
        # 3. Revisión
        final_response = await self.reviewer_agent.execute("Verifica esta respuesta y devuelve el JSON final de mensajes", {"draft": draft_response})
        
        cleaned = self._clean_json_text(final_response)
        
        try:
            import json
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                # Extraer strings de los elementos (en caso de que sean objetos o arrays anidados)
                result = []
                for item in parsed:
                    if isinstance(item, str):
                        result.append(item)
                    elif isinstance(item, dict):
                        # En caso de que el LLM insista en devolver objetos con llave 'response'
                        val = item.get("response") or item.get("text") or str(item)
                        result.append(val)
                return result
            elif isinstance(parsed, dict):
                val = parsed.get("response") or parsed.get("text")
                if val:
                    return [val]
            return [cleaned]
        except Exception as e:
            log.warning(f"[swarm] Error al parsear JSON del ReviewerAgent ({e}). Usando fallback de texto crudo.")
            return [cleaned]

swarm_queen = QueenCoordinator()
