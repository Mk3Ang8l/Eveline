import httpx
import logging
import os
import base64
from PIL import Image
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

class VisionService:
    """
    Service to handle image analysis using Mistral's multimodal capabilities (Pixtral).
    """

    @staticmethod
    async def analyze_image(image_path: Optional[str] = None, image_url: Optional[str] = None, prompt: str = "Describe this image in detail.") -> str:
        """
        Analyzes an image (local path or URL) and returns a textual description.
        """
        if not MISTRAL_API_KEY:
            return "ERROR: MISTRAL_API_KEY is missing."

        if not image_path and not image_url:
            return "ERROR: No image_path or image_url provided."

        try:
            base64_image = ""
            
            # CASE A: Remote URL
            if image_url:
                 async with httpx.AsyncClient() as client:
                     resp = await client.get(image_url)
                     if resp.status_code != 200:
                         return f"ERROR: Failed to fetch image from URL {image_url} (Status {resp.status_code})"
                     
                     with Image.open(BytesIO(resp.content)) as img:
                        # Process same as local
                         max_size = (1024, 1024)
                         img.thumbnail(max_size, Image.Resampling.LANCZOS)
                         buffered = BytesIO()
                         img.save(buffered, format="WEBP", quality=80)
                         base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # CASE B: Local Path
            elif image_path:
                if not os.path.exists(image_path):
                    return f"ERROR: Image file not found at {image_path}"
                
                with Image.open(image_path) as img:
                    max_size = (1024, 1024)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    buffered = BytesIO()
                    img.save(buffered, format="WEBP", quality=80)
                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # 2. Call Mistral Pixtral
            headers = {
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "pixtral-12b-2409",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/webp;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Pixtral API Error: {response.status_code} - {response.text}")
                    return f"ERROR: Vision API failed with status {response.status_code}"
                
                data = response.json()
                description = data["choices"][0]["message"]["content"]
                return description

        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"VISION ERROR: {str(e)}"
