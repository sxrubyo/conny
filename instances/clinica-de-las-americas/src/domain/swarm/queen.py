import asyncio
import logging
from typing import Dict, Any, List, Optional
from src.core.globals import llm_engine

log = logging.getLogger("bublee.swarm")

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
            instruction=(
                "Busca en la base de datos de FAQs, historial de la conversación o en el contexto del paciente para extraer hechos exactos. "
                "Pon especial atención en la historia de la conversación para saber qué se ha respondido ya."
            )
        )
        self.response_agent = Agent(
            name="ResponseAgent",
            role="Generador de Respuestas Hipernaturales",
            instruction=(
                "Eres la asesora de la clínica. Tu nombre es el valor de 'agent_name' en la clínica (ej. Lucia).\n"
                "REGLAS CRÍTICAS DE COMUNICACIÓN Y PSICOLOGÍA DE VENTAS:\n"
                "1. NO REPETIR SALUDOS NI PRESENTACIONES: Si en 'history' ya saludaste o te presentaste antes (ya dijiste tu nombre), "
                "bajo ninguna circunstancia vuelvas a decir 'Hola', 'Soy Lucia' ni a presentarte. Ve directo al grano.\n"
                "2. ESTILO DE PRESENTACIÓN ÚNICO Y SIN NOMBRE DE LA CLÍNICA: Si es el primer mensaje de la conversación y corresponde presentarse, usa exactamente: "
                "'Soy {agent_name}, asesora de la clínica.' (Reemplazando {agent_name} por el nombre real, ej. Lucia). Jamás menciones el nombre de la clínica "
                "(no digas 'de la Clínica Las Américas' ni 'en Clínica Las Américas'); las personas ya saben perfectamente en qué chat están. Jamás uses frases robóticas.\n"
                "3. PSICOLOGÍA DE VENTAS Y NATURALIDAD: No listes tratamientos como un catálogo frío o viñetas. Conversa de manera empática y persuasiva. "
                "No digas 'en la clínica ofrecemos...' ni redundancias similares. Menciona solo 1 o 2 opciones relevantes y haz preguntas abiertas para entender qué busca mejorar (ej. '¿Hay algo en específico de tu rostro o cuerpo que te gustaría mejorar hoy?').\n"
                "4. ESTILO DE ESCRITURA WHATSAPP (SÚPER HUMANO): Escribe de forma natural, seria y profesional, pero sin rigidez académica. "
                "No uses puntuación exageradamente perfecta ni coloques puntos finales al final de oraciones cortas o del último mensaje (los humanos en WhatsApp no usan puntos finales siempre). "
                "No uses excesiva ortografía perfecta ni fuerces tildes en palabras cotidianas de forma rígida. "
                "No uses dobles vocales (ej. no digas 'holaaa' ni 'buenaaas') ya que debes mantener la seriedad con los pacientes, "
                "pero mantén un tono conversacional de chat real, directo y fluido.\n"
                "5. PROHIBICIÓN ABSOLUTA DE ASTERISCOS Y MARKDOWN: Jamás utilices asteriscos (*), guiones de viñeta, o formato markdown en tus respuestas. No pongas negritas con asteriscos ni listas formateadas. Todo debe ser texto plano limpio, tal como escribe un humano real en WhatsApp.\n"
                "6. PROHIBICIÓN ABSOLUTA DE INVENTAR (ALUCINACIÓN): Jamás inventes promociones, descuentos, ofertas, precios, servicios o información que no esté explícitamente detallada en el contexto. Si te preguntan por algo que no conoces, o si el usuario pide detalles de promociones que no están documentadas en el soporte, di amablemente que vas a consultar o responderás en breve, pero NUNCA inventes que 'tenemos promociones especiales' ni digas cosas que el administrador no te ha dicho."
            )
        )
        self.reviewer_agent = Agent(
            name="ReviewerAgent",
            role="Auditor de Calidad y Humanización",
            instruction=(
                "Verifica la respuesta generada.\n"
                "REGLAS:\n"
                "1. Asegúrate de que si el asistente se presenta, use el nombre correcto del agente ('agent_name' de la clínica) y use el formato natural: "
                "'Soy {agent_name}, asesora de la clínica.' Jamás permitas que se mencione el nombre de la clínica (ej. elimina frases como 'de la Clínica Las Américas' o 'en Clínica Las Américas').\n"
                "2. ELIMINA REPETICIONES: Verifica el historial ('history'). Si el bot ya se presentó en mensajes anteriores de la historia, "
                "elimina cualquier saludo redundante o nueva presentación en la respuesta actual.\n"
                "3. ESTILO DE ESCRITURA WHATSAPP Y PROHIBICIÓN DE ASTERISCOS: Quita los puntos finales al final de los mensajes cortos. "
                "Asegúrate de que no suene a robot de call center ni a texto formateado académicamente. Quita las dobles vocales (ej. 'holaaa'). "
                "ELIMINA CUALQUIER ASTERISCO (*), NEGRITAS O MARKDOWN de los mensajes. Todo debe salir en texto plano limpio, sin símbolos markdown.\n"
                "4. VERIFICACIÓN DE ALUCINACIONES: Si la respuesta menciona 'promociones', 'descuentos' o datos no confirmados que no estén en la base de datos de la clínica, "
                "corrige la respuesta para no prometer nada falso o di de forma simple y humana que consultarás con el equipo. Jamás inventes ofertas o promociones.\n"
                "5. Devuelve ÚNICAMENTE un array de strings en formato JSON con los mensajes finales (ejemplo: [\"¡Claro que sí!\", \"¿Qué te gustaría tratar hoy?\"]). "
                "No incluyas explicaciones ni bloques de texto fuera del JSON."
            )
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

    async def process(self, user_message: str, clinic_context: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        log.info("[swarm] Queen ha recibido un mensaje, coordinando enjambre...")
        
        # 1. Investigación
        research_context = {**clinic_context, "history": history or []}
        facts = await self.research_agent.execute(f"Extrae datos relevantes para responder a: '{user_message}'", research_context)
        
        # 2. Generación
        draft_context = {"user_message": user_message, "facts": facts, "clinic": clinic_context, "history": history or []}
        draft_response = await self.response_agent.execute("Escribe la respuesta final en JSON", draft_context)
        
        # 3. Revisión
        persona = clinic_context.get("persona_config", {})
        if isinstance(persona, str):
            try:
                import json as _j_persona
                persona = _j_persona.loads(persona) if persona else {}
            except Exception:
                persona = {}
        agent_name = persona.get("name", "Lucía")

        review_context = {
            "draft": draft_response,
            "agent_name": agent_name,
            "clinic": clinic_context,
            "history": history or []
        }
        final_response = await self.reviewer_agent.execute(
            f"Verifica esta respuesta y devuelve el JSON final de mensajes. El nombre real del agente del negocio es '{agent_name}'. Asegúrate de usar ese nombre y no placeholders ni otros nombres.",
            review_context
        )
        
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
