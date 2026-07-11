import base64
import logging
import httpx
from typing import Dict, Optional
from src.core.globals import Config

log = logging.getLogger("bublee.vision")

async def download_image(attachment: Dict) -> Optional[bytes]:
    """
    Downloads an image attachment from Baileys WhatsApp, Telegram, or WhatsApp Cloud.
    """
    platform = attachment.get("platform")
    
    # 1. WhatsApp Bridge (Baileys) base64 inline
    if platform == "whatsapp" and attachment.get("base64"):
        try:
            return base64.b64decode(attachment["base64"])
        except Exception as e:
            log.warning(f"[vision] failed to decode base64 image: {e}")
            return None
            
    # 2. Telegram
    if platform == "telegram" and attachment.get("file_id"):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(
                    f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/getFile",
                    params={"file_id": attachment["file_id"]}
                )
                fp = r.json()["result"]["file_path"]
                ar = await client.get(
                    f"https://api.telegram.org/file/bot{Config.TELEGRAM_TOKEN}/{fp}"
                )
                return ar.content
        except Exception as e:
            log.warning(f"[vision] failed to download Telegram image: {e}")
            return None
            
    # 3. WhatsApp Cloud API
    if platform == "whatsapp_cloud" and attachment.get("media_id"):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                mr = await client.get(
                    f"https://graph.facebook.com/v20.0/{attachment['media_id']}",
                    headers={"Authorization": f"Bearer {Config.WA_ACCESS_TOKEN}"}
                )
                url = mr.json().get("url", "")
                if url:
                    dl = await client.get(
                        url, 
                        headers={"Authorization": f"Bearer {Config.WA_ACCESS_TOKEN}"}
                    )
                    return dl.content
        except Exception as e:
            log.warning(f"[vision] failed to download WhatsApp Cloud image: {e}")
            return None
            
    return None

async def analyze_skin_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Sends the patient skin/face photo to Google Gemini 2.5 Flash (or fallback OpenAI GPT-4o-mini)
    to perform a pre-diagnostic assessment, warm assessment, and direct invite to schedule.
    """
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    
    system_prompt = (
        "Eres Bublee, la asistente experta de una prestigiosa clínica de medicina estética y dermatología.\n"
        "El paciente te ha enviado una foto de su piel/rostro para una consulta preliminar.\n"
        "Instrucciones de respuesta:\n"
        "1. Analiza de manera cálida, empática, profesional y cercana la imagen.\n"
        "2. Identifica posibles áreas de oportunidad o condiciones visibles de forma orientativa (ej. deshidratación, líneas de expresión, marcas, manchas, acné, pérdida de luminosidad).\n"
        "3. **IMPORTANTE**: Aclara de manera muy sutil y profesional que esta pre-evaluación no reemplaza un diagnóstico médico presencial, sino que es una guía orientativa.\n"
        "4. Explica qué tipo de tratamientos de la clínica podrían ayudarle (ej. limpieza profunda, peeling, toxina botulínica, ácido hialurónico, láser, etc.) de forma muy atractiva.\n"
        "5. Termina invitando al paciente a agendar una cita de valoración presencial con el especialista para realizar un diagnóstico definitivo en cabina.\n"
        "6. Escribe en español de Colombia de forma muy natural, usando emojis de manera equilibrada y un tono conversacional de WhatsApp (párrafos cortos, amigable)."
    )

    # 1. Primary: Google Gemini
    gemini_key = Config.GEMINI_API_KEY
    if not gemini_key and Config.GEMINI_API_KEYS:
        gemini_key = Config.GEMINI_API_KEYS[0]
        
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": b64_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 1000,
                    "thinkingConfig": {"thinkingBudget": 0}
                }
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=payload)
                r.raise_for_status()
            result = r.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text:
                return text
        except Exception as gemini_err:
            log.warning(f"[vision] Gemini vision request failed, trying OpenAI: {gemini_err}")

    # 2. Secondary/Fallback: OpenAI GPT-4o-mini
    if Config.OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analiza esta imagen y brinda recomendaciones preliminares."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_data}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.4,
                "max_tokens": 1000
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
            result = r.json()
            text = result["choices"][0]["message"]["content"].strip()
            if text:
                return text
        except Exception as openai_err:
            log.error(f"[vision] OpenAI vision request failed: {openai_err}")

    return (
        "¡Hola! He recibido la foto de tu piel/rostro. 📸 Para darte una recomendación "
        "precisa y personalizada, te sugiero agendar una cita de valoración presencial "
        "en nuestra clínica para que el especialista te revise en detalle."
    )
