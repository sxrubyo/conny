import json
import sys
import logging
from typing import Dict, Any
from src.interfaces.nova_bridge import nova_bridge

log = logging.getLogger("bublee.mcp")

class MCPServer:
    """
    Servidor Model Context Protocol (MCP) sobre stdio.
    Expone las herramientas del Enjambre (Swarm) y AgentDB a la máquina anfitriona.
    """
    def __init__(self):
        self.tools = {
            "agent_spawn": self.tool_agent_spawn,
            "memory_store": self.tool_memory_store,
            "task_orchestrate": self.tool_task_orchestrate
        }
        # Registrar reglas de seguridad con Nova Governance
        nova_bridge.connect(cannot_do_rules=["rm -rf /", "leak patient data"])

    def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        method = req.get("method")
        params = req.get("params", {})
        
        if method == "tools/list":
            return {"tools": list(self.tools.keys())}
            
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name in self.tools:
                # Validar la acción con Nova Governance antes de ejecutarla
                if not nova_bridge.validate_action(tool_name, tool_args):
                    return {"error": f"Acción bloqueada por Nova Governance: {tool_name}"}
                
                result = self.tools[tool_name](tool_args)
                return {"result": result}
            else:
                return {"error": "Tool not found"}

        return {"error": "Unknown method"}

    def tool_agent_spawn(self, args: Dict) -> str:
        role = args.get("role", "coder")
        return f"Agent {role} spawned successfully."

    def tool_memory_store(self, args: Dict) -> str:
        # Aquí se conectaría a src.bublee.brain.memory.AgentDB
        key = args.get("key")
        return f"Memory {key} stored in AgentDB."

    def tool_task_orchestrate(self, args: Dict) -> str:
        task = args.get("task")
        return f"Task '{task}' routed to Swarm Queen."

    def start_stdio(self):
        """Escucha JSON-RPC en stdin."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                res = self.handle_request(req)
                print(json.dumps(res), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)

if __name__ == "__main__":
    server = MCPServer()
    server.start_stdio()
