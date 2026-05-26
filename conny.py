# -*- coding: utf-8 -*-
"""Conny AI - Monolithic Bootstrap Facade."""
from __future__ import annotations

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force full reload of submodules for dynamic test environments to maintain perfect isolation
if __name__ != "__main__":
    for k in list(sys.modules.keys()):
        if k.startswith("src.core") or k.startswith("src.interfaces"):
            del sys.modules[k]

# 1. Import all globals dynamically
import src.core.globals as globals_module
globals_module.__facade_name__ = __name__
for name in dir(globals_module):
    if not name.startswith("__"):
        globals()[name] = getattr(globals_module, name)

# 2. Import all runtime attributes dynamically
import src.core.runtime as runtime_module
runtime_module.__facade_name__ = __name__
for name in dir(runtime_module):
    if not name.startswith("__"):
        globals()[name] = getattr(runtime_module, name)

# 3. Import all web app attributes dynamically
import src.interfaces.web.app as app_module
app_module.__facade_name__ = __name__
for name in dir(app_module):
    if not name.startswith("__"):
        globals()[name] = getattr(app_module, name)

# 4. Define conny global instance and initialization helpers
conny: ConnyUltra = None
ADMIN_PENDING_CONFIRMATIONS: Dict[str, Dict] = {}
db = None
llm_engine = None
anti_robot_filter = None
conversation_simulator = None
response_variation = None
hallucination_guard = None
owner_style_controller = None
auth_engine = None
mcp_manager = None
prompt_evolver = None
trainer_gateway = None
v8_build_quality_system_prompt_addon = None
trainer_get_system_prompt_addon = None
task_manager = None
v8_process_response = None
v8_process_agentic_intent = None

async def init_conny():
    """Inicializa Conny Ultra."""
    global conny
    conny = ConnyUltra()
    await conny.initialize()
    
    import src.core.globals as g
    global db, llm_engine, auth_engine, mcp_manager
    db = g.db
    llm_engine = g.llm_engine
    auth_engine = getattr(g, "auth_engine", None)
    mcp_manager = getattr(g, "mcp_manager", None)


# 5. CLI entrypoint
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     ██████╗  ██████╗ ███╗   ██╗███╗   ██╗██╗   ██╗             ║
    ║    ██╔════╝ ██╔═══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝             ║
    ║    ██║      ██║   ██║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝              ║
    ║    ██║      ██║   ██║██║╚██╗██║██║╚██╗██║  ╚██╔╝               ║
    ║    ╚██████╗ ╚██████╔╝██║ ╚████║██║ ╚████║   ██║                ║
    ║     ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝                ║
    ║                                                                  ║
    ║                    U L T R A   v 9 . 7 . 0                       ║
    ║                                                                  ║
    ║        Agente de Recepción Hipernaturalmente Humana             ║
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  • AntiRobotFilter — elimina cada patrón de bot antes de enviar ║
    ║  • ConversationIntelligence — etapas, emociones, compromiso     ║
    ║  • HyperHumanEngine — valida humanidad en cada respuesta        ║
    ║  • SmartVariety — nunca repite apertura ni cierre igual         ║
    ║  • /modelo — admin cambia el LLM en caliente                    ║
    ║  • Ortografía perfecta forzada (tildes, puntuación)             ║
    ║  • PersonaEvolution — aprende el estilo de cada cliente         ║
    ║  • ConversionFunnelTracker — sabe en qué etapa está cada lead   ║
    ║  • Demo V2 — comportamiento idéntico al de producción           ║
    ║  • MultilingualHandler — español/inglés/portugués automático    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "conny:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
