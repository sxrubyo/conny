#!/usr/bin/env python3
"""
Conversación de prueba con Bublee - Simula un lead real
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import bublee as bublee_module
from bublee import Config

async def chat_with_bublee(message: str, user_id: str = "human_test"):
    """Envía un mensaje a Bublee y retorna la respuesta"""
    try:
        bublee = bublee_module.bublee
        
        if bublee is None:
            await bublee_module.init_bublee()
        
        # Llamar process_message
        result = await bublee.process_message(
            message=message,
            chat_id=user_id,
            platform="telegram",
            sender_name="Lead de Prueba"
        )
        
        # Extraer la respuesta
        if isinstance(result, dict):
            return result.get("response", result.get("message", str(result)))
        return str(result)
    except Exception as e:
        import traceback
        return f"Error: {e}\n{traceback.format_exc()}"

async def main():
    print("💬 CONVERSACIÓN CON BUBLEE - MODO DEMO")
    print("=" * 50)
    
    user_id = "human_lead_demo_001"
    
    # Mensaje inicial - lead que no sabe qué es Bublee
    messages = [
        "Hola, me llegó un link de ti pero no sé qué es esto",
    ]
    
    for msg in messages:
        print(f"\n👤 LEAD: {msg}")
        response = await chat_with_bublee(msg, user_id)
        print(f"\n🤖 BUBLEE: {response}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())