import aiohttp
import logging
import traceback
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def send_to_websocket(chat_id: int, user_id: int, message: str, message_id: int):
    try:
        domain = os.getenv("DOMAIN")

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"ws://{domain}/ws/chat/{chat_id}/") as ws:
                await ws.send_json(
                    {
                        "user_id": user_id,
                        "message": message,
                        "source": "telegram",
                        "message_id": message_id,
                    }
                )
                logger.info(f"Message sent to websocket: {chat_id} / {user_id} / {message}")
                return True
    except Exception as e:
        logger.error(f"#" * 50)
        logger.error(f"Send to websocket: {e}")
        logger.error(traceback.format_exc())
        logger.error(f"#" * 50)
        
