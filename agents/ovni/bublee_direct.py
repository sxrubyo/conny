#!/usr/bin/env python3
"""
Bublee Direct — Talk to Bublee instantly (no buffer, no WhatsApp).
Uses /test endpoint for instant responses.

Usage:
  python3 bublee_direct.py "Hey what is this"     — single message
  python3 bublee_direct.py --conv                  — interactive chat
  python3 bublee_direct.py --test                  — automated test battery
"""
import asyncio
import httpx
import sys
import time

BUBLEE_URL = "http://127.0.0.1:8003"
MASTER_KEY = "0c7d084e07ce8d912685fe11"


async def send(text: str, user_id: str = "ai2ai_test") -> str:
    """Send message to Bublee via /test endpoint — instant response, no buffer."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{BUBLEE_URL}/test", json={
            "message": text,
            "user_id": user_id,
            "master_key": MASTER_KEY,
        })
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "(empty)")
        return f"(error {r.status_code}: {r.text[:100]})"


async def test_battery():
    """Automated test battery — catches bugs before they reach WhatsApp."""
    tests = [
        # (input, must_not_contain, must_contain_one_of, description)
        ("Holaa", 
         ["Bublee", "recepcionista virtual", "asesora virtual"], 
         ["Bublee", "bublee", "Kimika"],
         "Greeting — should say Bublee not Bublee"),
        
        ("Hey what's up", 
         ["Bublee", "negocio", "clínica", "hola", "cuál"], 
         ["Bublee", "business", "hey", "Hi", "What"],
         "English greeting — should respond in English"),
        
        ("My business name is BarberKing in Miami", 
         ["Bublee", "no entendí", "cuál es"], 
         ["BarberKing", "Miami", "barber", "Got it", "got it", "Listo"],
         "English business name — should recognize and accept"),
        
        ("Cuanto cuesta tener esto para mi negocio?", 
         ["Bublee"], 
         ["Kimika", "plan", "contacto", "equipo", "3124348669"],
         "Purchase intent — should mention Kimika/contact"),
        
        ("Sup", 
         ["ya tengo Sup", "necesito el nombre", "negocio"], 
         [],
         "Slang greeting — should NOT treat as business name"),
        
        ("Para que? no entiendo", 
         ["Bublee", "recepcionista", "asesora virtual"], 
         ["ejemplo", "WhatsApp", "negocio", "IA", "chat", "Bublee"],
         "Confusion — should explain with example, not be rude"),
        
        ("I told you already, it's Luxury Clinic", 
         ["cuál es", "negocio", "dime el nombre"], 
         ["Luxury", "Clinic", "clinic"],
         "Repeated business name in English — should accept"),
        
        ("Jajaja que loco esto", 
         ["Bublee", "asesora"], 
         [],
         "Casual Spanish reaction — should mirror casual tone"),
    ]
    
    print("═══════════════════════════════════════════════════")
    print("  BUBLEE AI — AUTOMATED TEST BATTERY")
    print("═══════════════════════════════════════════════════\n")
    
    passed = 0
    failed = 0
    
    for i, (msg, must_not, must_one, desc) in enumerate(tests):
        user_id = f"test_{i}_{int(time.time())}"
        print(f"[{i+1}/{len(tests)}] {desc}")
        print(f"  Input: \"{msg}\"")
        
        response = await send(msg, user_id)
        
        # Check forbidden
        violations = [w for w in must_not if w.lower() in response.lower()]
        # Check required
        has_required = not must_one or any(w.lower() in response.lower() for w in must_one)
        
        if violations:
            print(f"  ❌ FAIL — Contains forbidden: {violations}")
            print(f"  Response: {response[:150]}")
            failed += 1
        elif not has_required and must_one:
            print(f"  ⚠️  WARN — Missing one of: {must_one}")
            print(f"  Response: {response[:150]}")
            failed += 1
        else:
            print(f"  ✅ PASS")
            print(f"  Response: {response[:150]}")
            passed += 1
        print()
    
    print(f"═══════════════════════════════════════════════════")
    print(f"  Results: {passed}/{len(tests)} passed, {failed} failed")
    print(f"═══════════════════════════════════════════════════")
    return failed == 0


async def interactive():
    """Interactive conversation mode — instant responses."""
    print("═══════════════════════════════════════════════════")
    print("  BUBLEE DIRECT — Instant AI-to-AI")
    print("  Type 'quit' to exit, 'reset' for new session")
    print("═══════════════════════════════════════════════════\n")
    
    user_id = f"direct_{int(time.time())}"
    
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        if msg.lower() == 'quit':
            break
        if msg.lower() == 'reset':
            user_id = f"direct_{int(time.time())}"
            print("  [New session]\n")
            continue
        
        response = await send(msg, user_id)
        for bubble in response.split("\n"):
            bubble = bubble.strip()
            if bubble:
                print(f"Bublee: {bubble}")
        print()


if __name__ == "__main__":
    if "--test" in sys.argv:
        success = asyncio.run(test_battery())
        sys.exit(0 if success else 1)
    elif "--conv" in sys.argv:
        asyncio.run(interactive())
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        msg = " ".join(sys.argv[1:])
        response = asyncio.run(send(msg))
        for bubble in response.split("\n"):
            if bubble.strip():
                print(f"Bublee: {bubble.strip()}")
    else:
        print(__doc__)
