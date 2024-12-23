from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import django_setup
from telegram_bot.core import db_request
from telegram_bot.core.keyboards import get_callback_btns
from telegram_bot.core.middlewares import CheckAndAddUserMiddleware
from telegram_bot.core.websocket_request import send_to_websocket


# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())


main_btns = {
    "Про нашу школу ❤️": "about",
    "Наші курси 💻": "courses",
    "Найпоширеніші запитання 🤔": "questions",
    "Правила школи 📜": "rules",
    "Написати адміністраторові 👨🏻‍💻": "admin",
}

admin_btn = {
    "Написати адміністраторові 👨🏻‍💻": "admin",
}

back_btn = {
    "Назад ⬅️": "back",
}

# handlers


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), "/start"
    )
    photo = FSInputFile("images/placeholder-image.jpg", filename="image.jpg")
    text = "Привітальне повідомлення"

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=get_callback_btns(btns=main_btns, sizes=(1,)),
    )


@router.callback_query(F.data == "back")
async def cmd_back(callback: CallbackQuery):
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), "/start"
    )
    photo = FSInputFile("images/placeholder-image.jpg", filename="image.jpg")
    text = "Привітальне повідомлення"

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=get_callback_btns(btns=main_btns, sizes=(1,)),
    )


@router.callback_query(or_f(F.data == "questions", F.data == "back_to_questions"))
async def questions(callback: CallbackQuery):
    btns = await db_request.get_questions_btns()
    btns.update(back_btn)

    await callback.message.delete()
    await callback.message.answer(
        text="Популярні питання",
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.message(Command("questions"))
async def questions(message: Message):
    btns = await db_request.get_questions_btns()
    btns.update(back_btn)

    await message.delete()
    await message.answer(
        text="Популярні питання",
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.callback_query(F.data.startswith("question_"))
async def question_info(callback: CallbackQuery, bot: Bot):
    question_id = callback.data.split("_")[1]
    question = await db_request.get_question(int(question_id))
    btns = {}

    btns.update(admin_btn)
    btns["Назад до питань ⬅"] = "back_to_questions"
    btns["Назад в головне меню ⬅️"] = "back"

    await callback.message.edit_text(
        text=f"{question.question}\n\n{question.answer}",
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.callback_query(or_f(F.data == "courses", F.data == "back_to_courses"))
async def courses(callback: CallbackQuery, bot: Bot):
    btns = {
        "Польська мова 🇵🇱": "course_0",
        "Іспанська мова 🇪🇸": "course_1",
        "Англійська мова 🇬🇧": "course_2",
        "Назад ⬅️": "back",
    }

    await callback.message.delete()
    await callback.message.answer(
        text="Оберіть мову і дізнайтеся більше про доступні курси 👇",
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.message(Command("courses"))
async def courses(message: Message):
    btns = {
        "Польська мова 🇵🇱": "course_0",
        "Іспанська мова 🇪🇸": "course_1",
        "Англійська мова 🇬🇧": "course_2",
        "Назад ⬅️": "back",
    }

    await message.delete()
    await message.answer(
        text="Оберіть мову і дізнайтеся більше про доступні курси 👇",
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.callback_query(F.data.startswith("course_"))
async def course_info(callback: CallbackQuery, bot: Bot):
    course_id = callback.data.split("_")[1]

    btns = {
        "Для дорослих 👨‍🦰👩‍🦳": f"course_{course_id}_adults",
        "Для підлітків 🧑‍🦱👩‍🦱": f"course_{course_id}_children",
        "Для дітей 👦👧": f"course_{course_id}_kids",
        "Назад до курсів ⬅️": "back_to_courses",
        "Назад в меню ⬅️": "back",
    }

    await bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=InputMediaPhoto(
            media=FSInputFile("images/placeholder-image.jpg", filename="image.jpg"),
            caption="Інформація про курс",
        ),
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.callback_query(F.data == "about")
async def cmd_about(callback: CallbackQuery, bot: Bot):
    text = """
    Ми українська онлайн школа UKnow. 🇺🇦Працюємо з 2022 року і допомагаємо українцям в різних куточках світу оволодіти мовою і інтегруватися в суспільство. Сьогодні ми пропонуємо уроки з англійської, іспанської, польської, французької, італійської, чеської, словацької, німецької та турецької мов 🌎

Ми вже випустили більше 4000 студентів 🎉

Наші викладачі проходять 4 етапи відбору, перед тим як приступити до занять. 

Ми можемо підготувати Вас до екзаменів на знання мови, до екзамену на вступ у ВНЗ, допомогти Вам заговорити за 36 уроків, або отримати найвищу оцінку при оформлені документів.🎯
    """
    image_path = FSInputFile("images/placeholder-image.jpg")
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await bot.edit_message_media(
        media=InputMediaPhoto(media=image_path, caption=text),
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.message(Command("about"))
async def cmd_about(message: Message, bot: Bot):
    text = """
    Ми українська онлайн школа UKnow. 🇺🇦Працюємо з 2022 року і допомагаємо українцям в різних куточках світу оволодіти мовою і інтегруватися в суспільство. Сьогодні ми пропонуємо уроки з англійської, іспанської, польської, французької, італійської, чеської, словацької, німецької та турецької мов 🌎

Ми вже випустили більше 4000 студентів 🎉

Наші викладачі проходять 4 етапи відбору, перед тим як приступити до занять. 

Ми можемо підготувати Вас до екзаменів на знання мови, до екзамену на вступ у ВНЗ, допомогти Вам заговорити за 36 уроків, або отримати найвищу оцінку при оформлені документів.🎯
    """
    image_path = FSInputFile("images/placeholder-image.jpg")
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await bot.edit_message_media(
        media=InputMediaPhoto(media=image_path, caption=text),
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


class AdminMessage(StatesGroup):
    message = State()


class TeacherMessage(StatesGroup):
    message = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await message.answer("Введіть повідомлення для адміністрації")

    await state.set_state(AdminMessage.message)


@router.message(AdminMessage.message)
async def cmd_admin_first(message: Message, state: FSMContext):
    chat_with = "telegram_user"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(
        obj_tg_user, chat_with
    )

    if chat_created is None:
        await message.answer("Не вдалося створити чат.")
        return

    socket_result = await send_to_websocket(
        obj_chat.pk,
        obj_tg_user.pk,
        message.text,
        message.message_id,
        chat_with=chat_with,
    )

    if socket_result:
        await message.answer("Ваше повідомлення було надіслано користувачу Telegram.")
        await cmd_admin(message, state, loop=True)
    else:
        await message.answer("Не вдалося надіслати повідомлення користувачу Telegram.")


@router.message(Command("teacher"))
async def cmd_teacher(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await message.answer("Введіть повідомлення для вчителя")

    await state.set_state(TeacherMessage.message)


@router.message(TeacherMessage.message)
async def cmd_teacher_first(message: Message, state: FSMContext):
    chat_with = "student"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(
        obj_tg_user, chat_with
    )

    if chat_created is None:
        await message.answer("Не вдалося створити чат.")
        return

    socket_result = await send_to_websocket(
        obj_chat.pk,
        obj_tg_user.pk,
        message.text,
        message.message_id,
        chat_with=chat_with,
    )

    if socket_result:
        await message.answer("Ваше повідомлення було надіслано студенту.")
        await cmd_teacher(message, state, loop=True)
    else:
        await message.answer("Не вдалося надіслати повідомлення студенту.")


@router.callback_query(or_f(F.data == "rules"))
async def rules(callback: CallbackQuery):
    text = "Правила школи 🚨\nз повним переліком правил роботи школи ви можете ознайомитися у договорі який вам надав ваш менеджер ✅\nДля вашої зручності додаємо сюди основні моменти:\n\n"
    text += await db_request.get_rules_txt()
    
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)
    
    await callback.message.delete()
    await callback.message.answer(
        text=text,
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )


@router.message(Command("rules"))
async def rules(message: Message):
    text = "Правила школи 🚨\nз повним переліком правил роботи школи ви можете ознайомитися у договорі який вам надав ваш менеджер ✅\nДля вашої зручності додаємо сюди основні моменти:\n\n"
    text += await db_request.get_rules_txt()
    
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)
    
    await message.delete()
    await message.answer(
        text=text,
        reply_markup=get_callback_btns(btns=btns, sizes=(1,)),
    )
