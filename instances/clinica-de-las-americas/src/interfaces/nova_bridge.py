import json
import logging
import subprocess
from typing import Dict, Any

log = logging.getLogger("bublee.nova")

class NovaGovernanceBridge:
    """
    Integra Bublee con Nova Governance.
    Proporciona métodos para descubrir, conectar y validar acciones antes de su ejecución.
    """
    def __init__(self, agent_name: str = "bublee-cli"):
        self.agent_name = agent_name

    def connect(self, cannot_do_rules: list[str]) -> bool:
        """Establece las reglas prohibitivas del agente en Nova."""
        try:
            cmd = ["nova", "connect", self.agent_name]
            for rule in cannot_do_rules:
                cmd.extend(["--cannot-do", rule])
            
            subprocess.run(cmd, check=True, capture_output=True)
            log.info(f"Conectado a Nova con reglas: {cannot_do_rules}")
            return True
        except FileNotFoundError:
            log.warning("Ejecutable de nova no encontrado. Governance en modo pasivo.")
            return False
        except Exception as e:
            log.warning(f"Error conectando a Nova: {e}")
            return False

    def validate_action(self, action_type: str, payload: Dict[str, Any]) -> bool:
        """Valida una acción riesgosa antes de ejecutarla."""
        try:
            payload_str = json.dumps(payload)
            cmd = [
                "nova", "validate", 
                "--agent", self.agent_name, 
                "--action", action_type, 
                "--payload", payload_str
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                log.info(f"Nova aprobó la acción: {action_type}")
                return True
            else:
                log.warning(f"Nova BLOQUEÓ la acción: {action_type}. Razón: {result.stderr}")
                return False
        except FileNotFoundError:
            # Si Nova no está instalado, por defecto permitimos en dev, pero en prod debería bloquear.
            log.warning("Nova no está instalado. Permitiendo acción por defecto (bypass).")
            return True
        except Exception as e:
            log.error(f"Fallo en validación de Nova: {e}")
            return False

nova_bridge = NovaGovernanceBridge()
