import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bublee

class TestDemoGreetingLoop(unittest.IsolatedAsyncioTestCase):

    @patch("bublee.db")
    @patch("bublee.llm_engine")
    async def test_greeting_and_pitch_flags_are_set(self, mock_llm, mock_db):
        from src.interfaces.web.demo_handler import handle_demo_message

        # Mock database history
        # Simulate previous assistant greeting + pitch
        mock_db.get_history.return_value = [
            {"role": "user", "content": "Holaa"},
            {"role": "assistant", "content": "soy Bublee, una asistente de IA diseñada para atender el WhatsApp de tu negocio y agendar citas automáticamente ||| quieres ver cómo lo hago? dime el nombre de tu empresa para empezar"}
        ]
        mock_db.get_admin.return_value = None
        mock_db.recall.return_value = None
        
        # Mock LLM complete returning a mock reply
        mock_llm.complete = AsyncMock(return_value=("Claro, te muestro para qué sirve.", {"provider": "mock", "model": "mock-model"}))
        
        # Mock runtime instance
        runtime = MagicMock()
        runtime.__class__.__module__ = "bublee"
        runtime._llm_runtime_available.return_value = True
        runtime._demo_sessions = {}
        runtime._demo_should_use_patient_chat_path.return_value = False
        runtime._split_bubbles = lambda msg, chat_id, **kwargs: [msg]
        runtime._session_mgr.touch_and_cleanup.return_value = (False, [])
        runtime.generator._postprocess = lambda text, *args: text
        
        # Call handle_demo_message
        res = await handle_demo_message(
            runtime,
            chat_id="prospect_123",
            text="Para que? Es un poco raro pero me enviaron tu numero",
            clinic={"name": "Clinica Test", "admin_chat_ids": "[]"}
        )
        
        # Verify complete was called
        mock_llm.complete.assert_called()
        
        # Extract system prompt from call arguments
        call_args = mock_llm.complete.call_args[0][0]
        system_prompt = next(msg["content"] for msg in call_args if msg["role"] == "system")
        
        # Assertions
        # Both flags should be detected as 'sí' because the assistant's previous message
        # contained "asistente de IA" and capability signals
        self.assertIn("ya dijiste que eres IA: sí", system_prompt)
        self.assertIn("ya explicaste capacidades: sí", system_prompt)

    @patch("bublee.db")
    @patch("bublee.llm_engine")
    async def test_greeting_and_pitch_flags_are_set_english(self, mock_llm, mock_db):
        from src.interfaces.web.demo_handler import handle_demo_message

        # Mock database history in English
        mock_db.get_history.return_value = [
            {"role": "user", "content": "Hey"},
            {"role": "assistant", "content": "I'm Bublee, an intelligent business assistant designed to handle your customer chats on WhatsApp and schedule appointments automatically. Want to see how I work? Tell me your business name to start!"}
        ]
        mock_db.get_admin.return_value = None
        mock_db.recall.return_value = None
        
        # Mock LLM complete returning a mock reply
        mock_llm.complete = AsyncMock(return_value=("Sure, let me show you.", {"provider": "mock", "model": "mock-model"}))
        
        # Mock runtime instance
        runtime = MagicMock()
        runtime.__class__.__module__ = "bublee"
        runtime._llm_runtime_available.return_value = True
        runtime._demo_sessions = {}
        runtime._demo_should_use_patient_chat_path.return_value = False
        runtime._split_bubbles = lambda msg, chat_id, **kwargs: [msg]
        runtime._session_mgr.touch_and_cleanup.return_value = (False, [])
        runtime.generator._postprocess = lambda text, *args: text
        
        # Call handle_demo_message
        res = await handle_demo_message(
            runtime,
            chat_id="prospect_123",
            text="I don't know, I'm a business owner and someone sent me your number",
            clinic={"name": "Clinica Test", "admin_chat_ids": "[]"}
        )
        
        # Verify complete was called
        mock_llm.complete.assert_called()
        
        # Extract system prompt from call arguments
        call_args = mock_llm.complete.call_args[0][0]
        system_prompt = next(msg["content"] for msg in call_args if msg["role"] == "system")
        
        # Assertions
        # Both flags should be detected as 'sí'
        self.assertIn("ya dijiste que eres IA: sí", system_prompt)
        self.assertIn("ya explicaste capacidades: sí", system_prompt)

    @patch("bublee.db")
    @patch("bublee.llm_engine")
    async def test_language_detection_spanish_greeting(self, mock_llm, mock_db):
        from src.interfaces.web.demo_handler import handle_demo_message

        # Mock database history
        mock_db.get_history.return_value = []
        mock_db.get_admin.return_value = None
        mock_db.recall.return_value = None
        
        # Mock LLM complete returning a mock reply
        mock_llm.complete = AsyncMock(return_value=("Sure, let me show you.", {"provider": "mock", "model": "mock-model"}))
        
        # Mock runtime instance
        runtime = MagicMock()
        runtime.__class__.__module__ = "bublee"
        runtime._llm_runtime_available.return_value = True
        
        # Set initial language to English and prevent session expiration
        import time
        now = time.time()
        runtime._demo_sessions = {
            "demo_prospect_123_owner_lang": "en",
            "demo_prospect_123_ts": now
        }
        runtime._demo_should_use_patient_chat_path.return_value = False
        runtime._split_bubbles = lambda msg, chat_id, **kwargs: [msg]
        runtime._session_mgr.touch_and_cleanup.return_value = (False, [])
        runtime.generator._postprocess = lambda text, *args: text
        
        # Call handle_demo_message with Spanish greeting
        await handle_demo_message(
            runtime,
            chat_id="prospect_123",
            text="Holaa",
            clinic={"name": "Clinica Test", "admin_chat_ids": "[]"}
        )
        
        # It should switch to Spanish
        self.assertEqual(runtime._demo_sessions["demo_prospect_123_owner_lang"], "es")

        # Now set it back to English and reset timestamp
        runtime._demo_sessions["demo_prospect_123_owner_lang"] = "en"
        runtime._demo_sessions["demo_prospect_123_ts"] = time.time()

        # Call with short message like "ok"
        await handle_demo_message(
            runtime,
            chat_id="prospect_123",
            text="ok",
            clinic={"name": "Clinica Test", "admin_chat_ids": "[]"}
        )
        # It should stick to English
        self.assertEqual(runtime._demo_sessions["demo_prospect_123_owner_lang"], "en")

    @patch("bublee.db")
    @patch("bublee.llm_engine")
    async def test_admin_sets_custom_ttl(self, mock_llm, mock_db):
        from src.interfaces.web.demo_handler import handle_demo_message

        # Mock database history
        mock_db.get_history.return_value = []
        mock_db.get_admin.return_value = None
        mock_db.recall.return_value = None
        
        # Mock LLM complete returning a mock reply
        mock_llm.complete = AsyncMock(return_value=("¡Holaa! Soy Bublee.", {"provider": "mock", "model": "mock-model"}))
        
        # Mock runtime instance
        runtime = MagicMock()
        runtime.__class__.__module__ = "bublee"
        runtime._llm_runtime_available.return_value = True
        runtime._demo_sessions = {}
        runtime._demo_should_use_patient_chat_path.return_value = False
        runtime._split_bubbles = lambda msg, chat_id, **kwargs: [msg]
        runtime._session_mgr.touch_and_cleanup.return_value = (False, [])
        runtime.generator._postprocess = lambda text, *args: text
        
        # Call handle_demo_message as admin activating demo beta with custom 15m duration
        res = await handle_demo_message(
            runtime,
            chat_id="admin_123",
            text="activar demo beta 15 minutos",
            clinic={"name": "Clinica Test", "admin_chat_ids": "[\"admin_123\"]"}
        )
        
        # Verify db.remember was called to save "demo_session_ttl" as "900" (15 * 60)
        mock_db.remember.assert_any_call("demo_session_ttl", "900")
        
        # Verify LLM complete was called with the welcome prompt containing the duration
        mock_llm.complete.assert_called()
        call_args = mock_llm.complete.call_args[0][0]
        system_prompt = next(msg["content"] for msg in call_args if msg["role"] == "system")
        self.assertIn("15 minutos", system_prompt)

if __name__ == "__main__":
    unittest.main()
