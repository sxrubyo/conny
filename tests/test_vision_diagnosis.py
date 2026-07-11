import sys
import unittest
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Eagerly import bublee so it runs its module-level reload loop before mocks are applied
import bublee

class TestVisionDiagnosis(unittest.IsolatedAsyncioTestCase):

    async def test_download_image_base64_decoding(self):
        from src.core.vision_handler import download_image
        
        sample_bytes = b"fake-image-bytes"
        b64_str = base64.b64encode(sample_bytes).decode("utf-8")
        
        attachment = {
            "kind": "image",
            "platform": "whatsapp",
            "base64": b64_str
        }
        
        res = await download_image(attachment)
        self.assertEqual(res, sample_bytes)

    @patch("src.core.vision_handler.httpx.AsyncClient")
    async def test_download_image_telegram(self, mock_client_class):
        from src.core.vision_handler import download_image
        from src.core.globals import Config
        Config.TELEGRAM_TOKEN = "test_bot_token"
        
        mock_client = MagicMock()
        mock_response_getfile = MagicMock()
        mock_response_getfile.json.return_value = {"result": {"file_path": "photos/photo_xyz.jpg"}}
        mock_response_content = MagicMock()
        mock_response_content.content = b"telegram-image-data"
        
        mock_client.get = AsyncMock(side_effect=[mock_response_getfile, mock_response_content])
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        attachment = {
            "kind": "image",
            "platform": "telegram",
            "file_id": "tg_file_123"
        }
        
        res = await download_image(attachment)
        self.assertEqual(res, b"telegram-image-data")
        
        # Verify getFile call
        mock_client.get.assert_any_call(
            "https://api.telegram.org/bottest_bot_token/getFile",
            params={"file_id": "tg_file_123"}
        )

    @patch("src.core.vision_handler.httpx.AsyncClient")
    async def test_download_image_whatsapp_cloud(self, mock_client_class):
        from src.core.vision_handler import download_image
        from src.core.globals import Config
        Config.WA_ACCESS_TOKEN = "fb_access_token_abc"
        
        mock_client = MagicMock()
        mock_response_metadata = MagicMock()
        mock_response_metadata.json.return_value = {"url": "https://cdn.fb.com/media/download/123"}
        mock_response_content = MagicMock()
        mock_response_content.content = b"wa-cloud-image-data"
        
        mock_client.get = AsyncMock(side_effect=[mock_response_metadata, mock_response_content])
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        attachment = {
            "kind": "image",
            "platform": "whatsapp_cloud",
            "media_id": "wa_media_999"
        }
        
        res = await download_image(attachment)
        self.assertEqual(res, b"wa-cloud-image-data")
        
        # Verify metadata call
        mock_client.get.assert_any_call(
            "https://graph.facebook.com/v20.0/wa_media_999",
            headers={"Authorization": "Bearer fb_access_token_abc"}
        )

    @patch("src.core.vision_handler.httpx.AsyncClient")
    async def test_analyze_skin_image_gemini_success(self, mock_client_class):
        from src.core.vision_handler import analyze_skin_image
        from src.core.globals import Config
        Config.GEMINI_API_KEY = "gemini_key_123"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Tu piel luce un poco deshidratada. Te sugerimos Hidratación Profunda."}
                        ]
                    }
                }
            ]
        }
        
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        res = await analyze_skin_image(b"fake-bytes", "image/jpeg")
        self.assertEqual(res, "Tu piel luce un poco deshidratada. Te sugerimos Hidratación Profunda.")
        
        # Verify Gemini URL and structure
        mock_client.post.assert_called_once()
        url_arg = mock_client.post.call_args[0][0]
        self.assertTrue("models/gemini-2.5-flash:generateContent" in url_arg)
        self.assertTrue("key=gemini_key_123" in url_arg)

    @patch("src.core.vision_handler.httpx.AsyncClient")
    async def test_analyze_skin_image_openai_fallback(self, mock_client_class):
        from src.core.vision_handler import analyze_skin_image
        from src.core.globals import Config
        Config.GEMINI_API_KEY = "" # Empty to trigger fallback, or we make it fail
        Config.GEMINI_API_KEYS = []
        Config.OPENAI_API_KEY = "openai_key_xyz"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Análisis de OpenAI: Vemos líneas de expresión. Sugerimos Botox."
                    }
                }
            ]
        }
        
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        res = await analyze_skin_image(b"fake-bytes", "image/jpeg")
        self.assertEqual(res, "Análisis de OpenAI: Vemos líneas de expresión. Sugerimos Botox.")
        
        # Verify OpenAI call arguments
        mock_client.post.assert_called_once()
        url_arg = mock_client.post.call_args[0][0]
        self.assertEqual(url_arg, "https://api.openai.com/v1/chat/completions")
        headers = mock_client.post.call_args[1]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer openai_key_xyz")

    @patch("bublee.db")
    @patch("src.core.vision_handler.download_image")
    @patch("src.core.vision_handler.analyze_skin_image")
    async def test_production_monitor_intercepts_image(self, mock_analyze, mock_download, mock_db):
        from src.core.production_monitor import BubleeProduction
        
        mock_download.return_value = b"image-content-bytes"
        mock_analyze.return_value = "Resultado del Análisis Estético."
        
        mock_bublee = MagicMock()
        mock_bublee._split_bubbles = lambda msg, chat_id: [msg]
        mock_bublee._typing_action = AsyncMock()
        
        monitor = BubleeProduction(bublee=mock_bublee)
        
        attachments = [
            {
                "kind": "image",
                "platform": "whatsapp",
                "base64": "dummy_b64"
            }
        ]
        
        res = await monitor.handle(
            chat_id="patient_vision",
            text="Mira mi piel",
            clinic={"google_maps_review_url": "http://g.co"},
            history=[],
            conv_state={},
            attachments=attachments
        )
        
        # Should call download and analyze
        mock_download.assert_called_once_with(attachments[0])
        mock_analyze.assert_called_once_with(b"image-content-bytes", mime_type="image/jpeg")
        
        # Should return vision assessment
        self.assertEqual(res, ["Resultado del Análisis Estético."])
        
        # Should save user and bot messages
        mock_db.save_message.assert_any_call("patient_vision", "user", "Mira mi piel")
        mock_db.save_message.assert_any_call("patient_vision", "assistant", "Resultado del Análisis Estético.")

if __name__ == "__main__":
    unittest.main()
