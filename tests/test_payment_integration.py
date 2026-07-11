import asyncio
import sys
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class TestPaymentIntegration(unittest.IsolatedAsyncioTestCase):

    @patch("src.core.globals.db")
    async def test_payment_rules_and_amounts(self, mock_db):
        from src.core.globals import PaymentBridge
        bridge = PaymentBridge()
        
        # Test default when no rules
        mock_db.get_clinic.return_value = {"payment_rules": "{}"}
        amount = bridge.get_deposit_amount("Limpieza Facial")
        self.assertEqual(amount, 0)
        
        # Test when rules configured
        mock_db.get_clinic.return_value = {
            "payment_rules": json.dumps({"Limpieza Facial": 50000, "Botox": 100000})
        }
        self.assertEqual(bridge.get_deposit_amount("Limpieza Facial"), 50000)
        self.assertEqual(bridge.get_deposit_amount("Botox"), 100000)
        self.assertEqual(bridge.get_deposit_amount("Otros"), 0)

    @patch("httpx.AsyncClient")
    @patch("src.core.globals.db")
    async def test_create_stripe_payment_link(self, mock_db, mock_client_class):
        mock_db.get_clinic.return_value = {
            "payment_config": json.dumps({
                "provider": "stripe",
                "api_key": "sk_test_12345",
                "webhook_secret": "whsec_abc"
            })
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://checkout.stripe.com/pay/session_abc"}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        from src.core.globals import PaymentBridge
        bridge = PaymentBridge()
        
        link = await bridge.create_payment_link(
            appointment_id=123,
            service="Botox",
            amount=50000,
            chat_id="573001112233@s.whatsapp.net"
        )
        
        self.assertEqual(link, "https://checkout.stripe.com/pay/session_abc")
        
        # Verify Stripe API arguments
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        self.assertEqual(call_args[0][0], "https://api.stripe.com/v1/checkout/sessions")
        payload = call_args[1]["data"]
        self.assertEqual(payload["client_reference_id"], "123")
        self.assertEqual(payload["line_items[0][price_data][unit_amount]"], "5000000") # COP decimal conversion
        self.assertEqual(payload["line_items[0][price_data][currency]"], "cop")

    @patch("httpx.AsyncClient")
    @patch("src.core.globals.db")
    async def test_create_bold_payment_link(self, mock_db, mock_client_class):
        mock_db.get_clinic.return_value = {
            "payment_config": json.dumps({
                "provider": "bold",
                "api_key": "bold_api_key_123",
                "webhook_secret": "bold_secret"
            })
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"url": "https://bold.co/p/link_xyz"}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        from src.core.globals import PaymentBridge
        bridge = PaymentBridge()
        
        link = await bridge.create_payment_link(
            appointment_id=456,
            service="Limpieza",
            amount=30000,
            chat_id="573001112233@s.whatsapp.net"
        )
        
        self.assertEqual(link, "https://bold.co/p/link_xyz")
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        self.assertEqual(call_args[0][0], "https://api.bold.co/v2/payment-links")
        payload = call_args[1]["json"]
        self.assertEqual(payload["amount"], 30000)
        self.assertEqual(payload["reference"], "apt_456")

    @patch("src.interfaces.web.app.db")
    @patch("src.interfaces.web.app.bublee")
    @patch("src.core.globals.calendar_bridge")
    def test_fastapi_webhooks_confirm_and_gcal(self, mock_calendar, mock_bublee, mock_db):
        # Mock database row lookup
        mock_db._conn.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = {
            "id": 999,
            "chat_id": "patient_chat_id",
            "patient_name": "Clara Luna",
            "patient_phone": "573204445555",
            "service": "Laser Co2",
            "datetime_slot": "2026-07-20T11:00:00",
            "google_event_id": "gcal_evt_999",
            "notes": "[PENDIENTE DE PAGO - Abono: 100,000 COP]\nLaser Co2",
            "status": "pendiente_pago"
        }
        
        mock_db.get_clinic.return_value = {
            "admin_chat_ids": "[\"admin_tg_123\"]"
        }
        
        # Set up mock async methods
        mock_bublee._send_message = AsyncMock()
        mock_calendar.has_google_calendar.return_value = True
        mock_calendar.update_event = AsyncMock(return_value=True)
        
        from fastapi.testclient import TestClient
        from src.interfaces.web.app import app
        
        client = TestClient(app)
        
        # 1. Test Stripe Webhook
        stripe_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": "999",
                    "payment_status": "paid"
                }
            }
        }
        
        response = client.post("/payment/webhook/stripe", json=stripe_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        
        # Verify db update
        mock_db.update_appointment.assert_any_call(999, status="confirmada", confirmed_at=unittest.mock.ANY)
        
        # Verify patient message sent
        mock_bublee._send_message.assert_any_call(
            "patient_chat_id", 
            "¡Hola Clara Luna! Confirmamos el recibo de tu abono. Tu cita para *Laser Co2* está oficialmente agendada para el 2026-07-20T11:00:00. ¡Te esperamos!"
        )
        
        # Verify admin message sent
        mock_bublee._send_message.assert_any_call(
            "admin_tg_123",
            "✅ *Cita de Clara Luna pagada & confirmada*\n\n• Lead: Clara Luna\n• Servicio: Laser Co2\n• Fecha/Hora: 2026-07-20T11:00:00\n• Teléfono: 573204445555"
        )
        
        # Verify Google Calendar event update (replacing PENDIENTE DE PAGO with PAGO CONFIRMADO)
        mock_calendar.update_event.assert_called_with(
            event_id="gcal_evt_999",
            summary="Cita: Clara Luna — Laser Co2 [CONFIRMADA/PAGADA]",
            description="[PAGO CONFIRMADO]\nLaser Co2"
        )

        # 2. Test Success Page Direct/Dual Confirmation Page
        # We trigger /payment/success?apt_id=999
        response_page = client.get("/payment/success?apt_id=999")
        self.assertEqual(response_page.status_code, 200)
        self.assertTrue("¡Reserva Confirmada!" in response_page.text)
        self.assertTrue("Clara Luna" in response_page.text)
        self.assertTrue("Laser Co2" in response_page.text)

if __name__ == "__main__":
    unittest.main()
