import asyncio
import os
import sys

sys.path.insert(0, '/home/ubuntu/conny')
import conny as conny_module

async def main():
    await conny_module.init_conny()
    conny = conny_module.conny
    chat_id = "test_melissa_demo_1"
    clinic = {
        "bot_name": "Melissa",
        "bot_personality": "Friendly",
        "name": "melissa-x"
    }

    print("Sending: holaa")
    res = await conny._handle_demo_message(chat_id, "holaa", clinic)
    print("Response:", res)
    
    print("Sending: somos Nova")
    res = await conny._handle_demo_message(chat_id, "somos Nova", clinic)
    print("Response:", res)

    print("Sending: empezar de nuevo")
    res = await conny._handle_demo_message(chat_id, "empezar de nuevo", clinic)
    print("Response:", res)

    print("Sending: reset")
    res = await conny._handle_demo_message(chat_id, "reset", clinic)
    print("Response:", res)

if __name__ == "__main__":
    asyncio.run(main())
