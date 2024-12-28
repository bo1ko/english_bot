import base64
import logging
import os
import uuid
from aiogram.types import Message

import django_setup
from django.conf import settings
from telegram_bot.core import db_request

logger = logging.getLogger(__name__)


async def get_contact_info(message: Message):
    try:
        contact_info = message.contact
        result = await db_request.update_contact(contact_info.user_id,
                                                 contact_info.phone_number,
                                                 contact_info.first_name,
                                                 contact_info.last_name)

        if result:
            logger.info(f'Contact {contact_info.user_id} updated')
            return True

        return False
    except Exception as e:
        logger.error("Utils get_contact_info:", e)
        return False
