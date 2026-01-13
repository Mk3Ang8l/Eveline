import asyncio
import json
import logging
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)

class RealtimeService:
    # Class-level storage for events (shared across instances)
    _recent_events = []
    _MAX_EVENTS = 50
    _active_task = None

    @classmethod
    def get_events(cls):
        """Return the current buffer of events."""
        return cls._recent_events

    @classmethod
    async def start_certstream(cls):
        """Start the background task if not already running."""
        if cls._active_task is None or cls._active_task.done():
            cls._active_task = asyncio.create_task(cls._certstream_loop())
            logger.info("📡 CertStream connection initiated.")

    @classmethod
    async def stop_certstream(cls):
        """Stop the background task."""
        if cls._active_task:
            cls._active_task.cancel()
            cls._active_task = None
            logger.info("🛑 CertStream connection stopped.")

    @classmethod
    async def _certstream_loop(cls):
        """Internal loop to maintain CertStream connection."""
        uri = "wss://certstream.calidog.io"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info("✅ Connected to CertStream")
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        
                        if data.get("message_type") == "certificate_update":
                            leaf_cert = data.get("data", {}).get("leaf_cert", {})
                            all_domains = leaf_cert.get("all_domains", [])
                            
                            if all_domains:
                                event = {
                                    "timestamp": datetime.now().isoformat(),
                                    "domain": all_domains[0],
                                    "all_domains": all_domains[:5], # Limit count
                                    "issuer": leaf_cert.get("issuer", {}).get("O"),
                                    "type": "SSL_CERT_ISSUED"
                                }
                                
                                cls._recent_events.append(event)
                                # Keep buffer within limits
                                if len(cls._recent_events) > cls._MAX_EVENTS:
                                    cls._recent_events.pop(0)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ CertStream connection closed. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ CertStream Error: {e}")
                await asyncio.sleep(10)
