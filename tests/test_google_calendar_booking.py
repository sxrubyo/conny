import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class TestGoogleCalendarBooking(unittest.IsolatedAsyncioTestCase):
    
    @patch("httpx.AsyncClient")
    async def test_calendar_bridge_create_event_success(self, mock_client_class):
        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "evt_google_12345"}
        
        # Async methods
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        from src.core.globals import CalendarBridge
        bridge = CalendarBridge()
        
        # Mock ensure token
        bridge._ensure_token = AsyncMock(return_value=True)
        bridge._access_token = "mock_access_token"
        bridge._calendar_id = "primary"
        
        event_id = await bridge.create_event(
            patient_name="Juan Perez",
            phone="573001234567",
            service="Valoracion Botox",
            date_time="2026-07-15 10:00",
            notes="Paciente nuevo"
        )
        
        self.assertEqual(event_id, "evt_google_12345")
        
        # Verify post payload
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        self.assertTrue("events" in call_args[0][0])
        payload = call_args[1]["json"]
        self.assertEqual(payload["summary"], "Cita: Juan Perez — Valoracion Botox")
        self.assertTrue("573001234567" in payload["description"])
        self.assertEqual(payload["start"]["dateTime"], "2026-07-15T10:00:00")
        self.assertEqual(payload["start"]["timeZone"], "America/Bogota")

    @patch("src.core.globals.payment_bridge")
    @patch("src.core.globals.db")
    @patch("src.core.globals.calendar_bridge")
    async def test_extract_actions_triggers_gcal_sync(self, mock_bridge, mock_db, mock_payment):
        from src.core.runtime import BubleeUltra
        
        # Setup runtime and mock globals
        runtime = BubleeUltra()
        runtime._notify_admin_appointment = AsyncMock()
        
        mock_payment.get_deposit_amount.return_value = 0
        mock_bridge.has_google_calendar.return_value = True
        mock_bridge.create_event = AsyncMock(return_value="gcal_evt_id_999")
        
        mock_db.save_appointment.return_value = 42
        
        response_text = (
            "Perfecto! He agendado tu cita.\n"
            "CITA: {\"patient_name\": \"Maria Gomez\", \"patient_phone\": \"573119876543\", "
            "\"service\": \"Limpieza Facial\", \"datetime_slot\": \"2026-07-16T15:30:00\", \"notes\": \"None\"}"
        )
        
        clinic = {"admin_chat_ids": "[\"admin_1\"]"}
        
        clean, actions = runtime._extract_actions(response_text, "patient_chat_id", clinic)
        
        # Clean text should have the JSON part removed
        self.assertEqual(clean, "Perfecto! He agendado tu cita.")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "appointment_created")
        
        # Wait a small moment to let the background task execute
        await asyncio.sleep(0.1)
        
        # Verify DB save and update
        mock_db.save_appointment.assert_called_once()
        mock_bridge.create_event.assert_called_once_with(
            patient_name="Maria Gomez",
            phone="573119876543",
            service="Limpieza Facial",
            date_time="2026-07-16T15:30:00",
            notes="None"
        )
        mock_db.update_appointment.assert_called_once_with(42, google_event_id="gcal_evt_id_999")

if __name__ == "__main__":
    unittest.main()
