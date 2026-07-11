import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class TestNPSFlow(unittest.IsolatedAsyncioTestCase):

    @patch("src.interfaces.web.app.bublee")
    @patch("src.core.globals.db")
    async def test_cron_triggers_nps_question(self, mock_db, mock_bublee):
        # 1. Test when appointment is NOT 2 hours past yet
        now = datetime.now()
        too_recent_start = now - timedelta(hours=1) # Started 1 hr ago, ends now
        
        mock_db._conn.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [
            {
                "id": 1,
                "chat_id": "patient_1",
                "patient_name": "Julio Cortazar",
                "service": "Limpieza Profunda",
                "datetime_slot": too_recent_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "duration_minutes": 60,
                "nps_status": "pending"
            }
        ]
        
        from bublee_cron import _check_finished_appointments
        mock_bublee._send_message = AsyncMock()
        
        await _check_finished_appointments("default")
        
        # Verify no message sent and database not updated (since 2 hours haven't passed)
        mock_bublee._send_message.assert_not_called()
        mock_db.update_appointment.assert_not_called()

        # 2. Test when appointment IS 2 hours past its end time
        finished_start = now - timedelta(hours=3, minutes=10) # Ends 2 hrs 10 mins ago
        mock_db._conn.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = [
            {
                "id": 2,
                "chat_id": "patient_2",
                "patient_name": "Gabriel Marquez",
                "service": "Botox",
                "datetime_slot": finished_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "duration_minutes": 60,
                "nps_status": "pending"
            }
        ]
        
        await _check_finished_appointments("default")
        
        # Should set status to 'sent' and dispatch message
        mock_db.update_appointment.assert_called_with(2, nps_status="sent")
        mock_bublee._send_message.assert_called_once_with(
            "patient_2",
            "¡Hola Gabriel Marquez! 😊 Espero que estés súper bien.\n\n¿Cómo te fue hoy en tu cita para *Botox*? Nos encantaría saber tu opinión del 1 al 5."
        )

    @patch("src.core.globals.db")
    @patch("bublee.llm_engine")
    async def test_positive_nps_response_routing(self, mock_llm, mock_db):
        from src.core.production_monitor import BubleeProduction
        
        # Mock active appointment waiting for NPS
        mock_db._conn.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {
            "id": 50,
            "chat_id": "patient_positive",
            "patient_name": "Lucia Mendez",
            "patient_phone": "573009998888",
            "service": "Masaje Relax",
            "status": "confirmada",
            "nps_status": "sent"
        }
        
        # Mock production monitor and FacadeProxy/bublee instance
        mock_bublee_instance = MagicMock()
        mock_bublee_instance._split_bubbles = lambda msg, chat_id: [msg]
        
        monitor = BubleeProduction(bublee=mock_bublee_instance)
        
        # Patient answers "Un 5, excelente servicio"
        clinic_config = {
            "google_maps_review_url": "https://g.page/r/my_clinic/review",
            "admin_chat_ids": "[\"admin_1\"]"
        }
        
        res = await monitor.handle("patient_positive", "Un 5, excelente servicio", clinic_config, [], {})
        
        # Status should update to answered_positive
        mock_db.update_appointment.assert_any_call(50, nps_status="answered_positive")
        
        # Response should contain the maps review link
        self.assertTrue(len(res) > 0)
        self.assertTrue("https://g.page/r/my_clinic/review" in res[0])
        self.assertTrue("Lucia Mendez" in res[0])

    @patch("src.core.globals.db")
    @patch("bublee.llm_engine")
    async def test_negative_nps_response_routing(self, mock_llm, mock_db):
        from src.core.production_monitor import BubleeProduction
        
        mock_db._conn.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {
            "id": 51,
            "chat_id": "patient_negative",
            "patient_name": "Mario Vargas",
            "patient_phone": "573007776666",
            "service": "Odontologia",
            "status": "confirmada",
            "nps_status": "sent"
        }
        
        mock_bublee_instance = MagicMock()
        mock_bublee_instance._split_bubbles = lambda msg, chat_id: [msg]
        mock_bublee_instance._send_message = AsyncMock()
        
        monitor = BubleeProduction(bublee=mock_bublee_instance)
        
        clinic_config = {
            "google_maps_review_url": "https://g.page/r/my_clinic/review",
            "admin_chat_ids": "[\"admin_1\"]"
        }
        
        res = await monitor.handle("patient_negative", "Fue pésimo, me dolió mucho y tardó bastante", clinic_config, [], {})
        
        # Status should update to answered_negative
        mock_db.update_appointment.assert_any_call(51, nps_status="answered_negative")
        
        # Bot responds politely to patient apologizing
        self.assertTrue(len(res) > 0)
        self.assertTrue("Lamentamos mucho escuchar eso" in res[0])
        
        # Admin is notified immediately
        mock_bublee_instance._send_message.assert_called_once()
        admin_alert_msg = mock_bublee_instance._send_message.call_args[0][1]
        self.assertTrue("⚠️ *Alerta NPS Negativo (1/5)*" in admin_alert_msg)
        self.assertTrue("Mario Vargas" in admin_alert_msg)

if __name__ == "__main__":
    unittest.main()
