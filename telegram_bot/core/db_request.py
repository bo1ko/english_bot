import datetime
import logging
from asgiref.sync import sync_to_async

from chat.models import (
    SystemAction,
    CustomUser,
    StudentAndTeacherChat,
    TelegramUserAndAdminChat,
    TelegramUser,
    Rule,
    Question,
    Course,
)

logger = logging.getLogger(__name__)


@sync_to_async
def get_or_create_user(tg_id: int, username: str) -> TelegramUser:
    return TelegramUser.objects.get_or_create(
        tg_id=tg_id, defaults={"username": username if username else None}
    )


@sync_to_async
def get_or_create_communication_chat(
    telegram: TelegramUser,
    chat_with: str
):
    try:
        if chat_with == "student":
            user = CustomUser.objects.get(telegram=telegram)
            obj, created = StudentAndTeacherChat.objects.get_or_create(
                student=user
            )
            return obj, created, obj.student.pk
        elif chat_with == "telegram_user":
            obj, created = TelegramUserAndAdminChat.objects.get_or_create(
                telegram_user=telegram
            )
            return obj, created, obj.telegram_user.pk
    except Exception as e:
        logger.error(f"Get or create chat student and admin: {e}")
        return None, None

@sync_to_async
def check_student(tg_id: int) -> StudentAndTeacherChat:
    try:
        telegram = TelegramUser.objects.get(tg_id=tg_id)
        user = CustomUser.objects.get(telegram=telegram)
        chat = StudentAndTeacherChat.objects.get(student=user)
        
        if chat:
            return True
        
        return False
    except Exception as e:
        logger.error(f"Check student: {e}")
        return False

@sync_to_async
def get_telegram_user(tg_id: int) -> TelegramUser:
    return TelegramUser.objects.get(tg_id=tg_id)


@sync_to_async
def create_system_action(telegram: TelegramUser, text: str) -> SystemAction:
    try:
        obj, _ = SystemAction.objects.get_or_create(telegram=telegram)

        if obj.action is None:
            obj.action = []
        obj.action.append(text)
        obj.save()

        return obj
    except Exception as e:
        logger.error(f"Create system action: {e}")


@sync_to_async
def create_message(sender: TelegramUser, chat: TelegramUserAndAdminChat, content: str, message_id) -> CustomUser:
    try:
        message = {
            "sender": sender.username,
            "text": content,
            "tg_user_message_id": message_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        }
        
        if chat.messages is None:
            chat.messages = []

        chat.messages.append(message)
        chat.save()

        created = True
        return sender.pk, created
    except Exception as e:
        logger.error(f"Create message: {e}")
        return None, False

@sync_to_async
def get_rules_txt() -> Rule:
    try:
        rules = Rule.objects.all()
        rules_txt = ""
        
        for rule in rules:
            rules_txt += f"{rule.rule}\n"
        
        return rules_txt
    except Exception as e:
        logger.error(f"Get rules: {e}")
        return None

@sync_to_async
def get_rule(pk: id) -> Rule:
    try:
        return Rule.objects.get(pk=pk)
    except Exception as e:
        logger.error(f"Get rule: {e}")
        return None

@sync_to_async
def get_questions_btns() -> Question:
    try:
        questions = Question.objects.all()
        btns = {}
        
        for question in questions:
            btns[question.question] = f"question_{question.pk}"
        
        return btns
        
    except Exception as e:
        logger.error(f"Get questions: {e}")
        return None

@sync_to_async
def get_question(pk: id) -> Question:
    try:
        return Question.objects.get(pk=pk)
    except Exception as e:
        logger.error(f"Get question: {e}")
        return None

@sync_to_async
def get_courses_btns() -> Course:
    try:
        courses = Course.objects.all()
        btns = {}

        for course in courses:
            btns[course.name] = f"course_{course.pk}"

        return btns
    except Exception as e:
        logger.error(f"Get courses: {e}")
        return None

@sync_to_async
def get_course(pk: id) -> Course:
    try:
        return Course.objects.get(pk=pk)
    except Exception as e:
        logger.error(f"Get course: {e}")
        return None

@sync_to_async
def update_contact(tg_id: int, phone_number: str, first_name: str, last_name: str) -> bool:
    try:
        telegram = TelegramUser.objects.get(tg_id=tg_id)

        if phone_number:
            telegram.phone_number = phone_number
        if first_name:
            telegram.first_name = first_name
        if last_name:
            telegram.last_name = last_name

        telegram.save()
        return True
    except Exception as e:
        logger.error(f"Update contact: {e}")
        return False

@sync_to_async
def check_registration(tg_id: int) -> bool:
    try:
        telegram = TelegramUser.objects.get(tg_id=tg_id)

        if telegram.phone_number:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Check_registration: {e}")
        return None
