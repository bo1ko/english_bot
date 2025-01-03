import base64
from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import django_setup
from telegram_bot.core import db_request
from telegram_bot.core.keyboards import get_callback_btns, request_contact
from telegram_bot.core.middlewares import CheckAndAddUserMiddleware
from telegram_bot.core.websocket_request import send_to_websocket
from telegram_bot.core.utils import get_contact_info

# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())

main_btns = {
    "Про нашу школу ❤️": "about",
    "Наші курси 💻": "courses",
    "Найпоширеніші запитання 🤔": "questions",
    "Правила школи 📜": "rules",
    "Написати адміністраторові 👨🏻‍💻": "admin",
    "Зв'язок з вчителем": "teacher",
}

admin_btn = {
    "Написати адміністраторові 👨🏻‍💻": "admin",
}

back_btn = {
    "Назад ⬅️": "back",
}

back_to_menu = {
    "Головне меню 🏠": "back",
}

# handlers


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), "/start")
    photo = FSInputFile("media/images/placeholder-image.jpg",
                        filename="image.jpg")
    text = "Привітальне повідомлення"

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=get_callback_btns(btns=main_btns, sizes=(1, )),
    )


@router.callback_query(F.data == "back")
async def cmd_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), "Назад")
    photo = FSInputFile("media/images/placeholder-image.jpg",
                        filename="image.jpg")
    text = "Привітальне повідомлення"

    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=get_callback_btns(btns=main_btns, sizes=(1, )),
    )


@router.callback_query(
    or_f(F.data == "questions", F.data == "back_to_questions"))
async def questions(callback: CallbackQuery):
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), "questions")
    btns = await db_request.get_questions_btns()
    btns.update(back_btn)

    await callback.message.delete()
    await callback.message.answer(
        text="Популярні питання",
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.message(Command("questions"))
async def questions(message: Message, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), "/questions")
    btns = await db_request.get_questions_btns()
    btns.update(back_btn)

    await message.delete()
    await message.answer(
        text="Популярні питання",
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
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
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.callback_query(or_f(F.data == "courses", F.data == "back_to_courses"))
async def courses(callback: CallbackQuery, bot: Bot):
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), "courses")
    btns = await db_request.get_courses_btns()
    btns.update(back_btn)

    await callback.message.delete()
    await callback.message.answer(
        text="Оберіть мову і дізнайтеся більше про доступні курси 👇",
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.message(Command("courses"))
async def courses(message: Message, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), "/courses")
    btns = await db_request.get_courses_btns()
    btns.update(back_btn)

    await message.delete()
    await message.answer(
        text="Оберіть мову і дізнайтеся більше про доступні курси 👇",
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.callback_query(F.data.startswith("course_"))
async def course_info(callback: CallbackQuery, bot: Bot):
    course_id = callback.data.split("_")[1]
    course = await db_request.get_course(int(course_id))
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id),
        f"Course {course.name}")
    text = f"{course.name}\n\n{course.description}"
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
            media=FSInputFile(course.image_url.path, filename="image.jpg"),
            caption=text,
        ),
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.callback_query(F.data == "about")
async def cmd_about(callback: CallbackQuery, bot: Bot):
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), f"About")
    text = """
    Ми українська онлайн школа UKnow. 🇺🇦Працюємо з 2022 року і допомагаємо українцям в різних куточках світу оволодіти мовою і інтегруватися в суспільство. Сьогодні ми пропонуємо уроки з англійської, іспанської, польської, французької, італійської, чеської, словацької, німецької та турецької мов 🌎

Ми вже випустили більше 4000 студентів 🎉

Наші викладачі проходять 4 етапи відбору, перед тим як приступити до занять. 

Ми можемо підготувати Вас до екзаменів на знання мови, до екзамену на вступ у ВНЗ, допомогти Вам заговорити за 36 уроків, або отримати найвищу оцінку при оформлені документів.🎯
    """
    image_path = FSInputFile("media/images/placeholder-image.jpg")
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await bot.edit_message_media(
        media=InputMediaPhoto(media=image_path, caption=text),
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.message(Command("about"))
async def cmd_about(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), f"/about")
    text = """
    Ми українська онлайн школа UKnow. 🇺🇦Працюємо з 2022 року і допомагаємо українцям в різних куточках світу оволодіти мовою і інтегруватися в суспільство. Сьогодні ми пропонуємо уроки з англійської, іспанської, польської, французької, італійської, чеської, словацької, німецької та турецької мов 🌎

Ми вже випустили більше 4000 студентів 🎉

Наші викладачі проходять 4 етапи відбору, перед тим як приступити до занять. 

Ми можемо підготувати Вас до екзаменів на знання мови, до екзамену на вступ у ВНЗ, допомогти Вам заговорити за 36 уроків, або отримати найвищу оцінку при оформлені документів.🎯
    """
    image_path = FSInputFile("media/images/placeholder-image.jpg")
    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await bot.edit_message_media(
        media=InputMediaPhoto(media=image_path, caption=text),
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


class AdminMessage(StatesGroup):
    message = State()


class TeacherMessage(StatesGroup):
    message = State()


@router.callback_query(F.data == "admin")
async def admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), f"Admin")

    is_registered = await db_request.check_registration(callback.from_user.id)
    if is_registered is None:
        await callback.message.answer(
            "Виникла помилка при провірці на реєстрацію...")
        return
    elif is_registered is False:
        await db_request.create_system_action(
            await db_request.get_telegram_user(callback.from_user.id),
            f"Registration")
        await callback.message.answer("Для початку потрібно зареєструватись 👌")
        await registration(callback.message)
    else:
        await callback.message.answer(
            "Введіть повідомлення для адміністрації",
            reply_markup=get_callback_btns(btns=back_to_menu))
        await state.set_state(AdminMessage.message)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        is_registered = await db_request.check_registration(
            message.from_user.id)
        if is_registered is None:
            await message.answer(
                "Виникла помилка при провірці на реєстрацію...")
            return
        elif is_registered is False:
            await db_request.create_system_action(
                await db_request.get_telegram_user(message.from_user.id),
                f"Registration")
            await message.answer("Для початку потрібно зареєструватись 👌")
            await registration(message)

            return

        await message.answer("Введіть повідомлення для адміністрації",
                             reply_markup=get_callback_btns(btns=back_to_menu))
    await state.set_state(AdminMessage.message)


@router.message(AdminMessage.message)
async def cmd_admin_first(message: Message, state: FSMContext):
    chat_with = "telegram_user"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(
        obj_tg_user, chat_with)

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
        await message.answer("Ваше повідомлення було надіслано адміністрації.",
                             reply_markup=get_callback_btns(btns=back_to_menu))
        await cmd_admin(message, state, loop=True)
    else:
        await message.answer(
            "Не вдалося надіслати повідомлення адміністрації.",
            reply_markup=get_callback_btns(btns=back_to_menu))


@router.callback_query(F.data == "teacher")
async def teacher(callback: CallbackQuery, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await callback.message.delete()
        await db_request.create_system_action(
            await db_request.get_telegram_user(callback.from_user.id),
            f"teacher")
        result = await db_request.check_student(callback.from_user.id)
        if not result:
            await callback.message.answer(
                "Ви не є студентом нашої школи. Для початку потрібно зареєструватись 👌",
                reply_markup=get_callback_btns(btns=back_to_menu))
            return

        await callback.message.answer(
            "Введіть повідомлення для вчителя",
            reply_markup=get_callback_btns(btns=back_to_menu))

    await state.set_state(TeacherMessage.message)


@router.message(Command("teacher"))
async def cmd_teacher(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await db_request.create_system_action(
            await db_request.get_telegram_user(message.from_user.id),
            f"/teacher")
        result = await db_request.check_student(message.from_user.id)
        if not result:
            await message.answer(
                "Ви не є студентом нашої школи. Для початку потрібно зареєструватись 👌",
                reply_markup=get_callback_btns(btns=back_to_menu))
            return
        await message.answer("Введіть повідомлення для вчителя")

    await state.set_state(TeacherMessage.message)


@router.message(TeacherMessage.message)
async def cmd_teacher_first(message: Message, state: FSMContext):
    chat_with = "student"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(
        obj_tg_user, chat_with)

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
        await message.answer("Ваше повідомлення було надіслано вчителю.",
                             reply_markup=get_callback_btns(btns=back_to_menu))
        await cmd_teacher(message, state, loop=True)
    else:
        await message.answer("Не вдалося надіслати повідомлення вчителю.",
                             reply_markup=get_callback_btns(btns=back_to_menu))


@router.callback_query(or_f(F.data == "rules"))
async def rules(callback: CallbackQuery):
    await db_request.create_system_action(
        await db_request.get_telegram_user(callback.from_user.id), f"Rules")
    text = "Правила школи 🚨\nз повним переліком правил роботи школи ви можете ознайомитися у договорі який вам надав ваш менеджер ✅\nДля вашої зручності додаємо сюди основні моменти:\n\n"
    text += await db_request.get_rules_txt()

    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await callback.message.delete()
    await callback.message.answer(
        text=text,
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.message(Command("rules"))
async def rules(message: Message, state: FSMContext):
    await state.clear()
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), f"/rules")
    text = "Правила школи 🚨\nз повним переліком правил роботи школи ви можете ознайомитися у договорі який вам надав ваш менеджер ✅\nДля вашої зручності додаємо сюди основні моменти:\n\n"
    text += await db_request.get_rules_txt()

    btns = {}
    btns.update(admin_btn)
    btns.update(back_btn)

    await message.delete()
    await message.answer(
        text=text,
        reply_markup=get_callback_btns(btns=btns, sizes=(1, )),
    )


@router.message(Command("registration"))
async def registration(message: Message):
    await message.answer('Надайте свої контаксти для реєстрації 👇',
                         reply_markup=request_contact('Надати контактні дані'))


@router.message(F.contact)
async def registration_result(message: Message, state: FSMContext):
    result = await get_contact_info(message)
    if result:
        await db_request.create_system_action(
            await db_request.get_telegram_user(message.from_user.id),
            f"Success Registration")
        await message.answer('Реєстрація пройшла успішно!',
                             reply_markup=ReplyKeyboardRemove())
        await message.answer('Введіть повідомлення для адміністрації',
                             reply_markup=get_callback_btns(btns=back_to_menu))
        await cmd_admin(message, state, True)


class SendMedia(StatesGroup):
    data = State()


@router.callback_query(F.data.startswith("send_"))
async def send_media(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    media_type = data[1]
    send_to_id = int(data[2])
    chat_with = "_".join([data[3], data[4]])

    await state.clear()
    await callback.answer()

    if media_type == "image":
        await callback.message.answer("Відправте фото")
    elif media_type == "video":
        await callback.message.answer("Відправте відео")
    elif media_type == "audio":
        await callback.message.answer("Відправте аудіо")
    else:
        return

    await state.set_state(SendMedia.data)
    await state.update_data({
        "file_type": media_type,
        "send_to_id": send_to_id,
        "chat_with": chat_with,
    })


@router.message(SendMedia.data)
async def send_media_second(message: Message, state: FSMContext):
    data = await state.get_data()
    send_to_id = data["send_to_id"]
    chat_with = data["chat_with"]
    file_type = data["file_type"]
    media_type = message.content_type

    try:
        if media_type == "photo":
            photo = message.photo[-1]
            file_id = photo.file_id
            file_name = f"{photo.file_unique_id}.jpg"

            file = await message.bot.get_file(file_id)
            file_content = await message.bot.download_file(file.file_path)

        elif media_type == "video":
            video = message.video
            file_id = video.file_id
            file_name = f"{video.file_unique_id}.mp4"

            file = await message.bot.get_file(file_id)
            file_content = await message.bot.download_file(file.file_path)

        elif media_type == "voice":
            voice = message.voice
            file_id = voice.file_id
            file_name = f"{voice.file_unique_id}.ogg"

            file = await message.bot.get_file(file_id)
            file_content = await message.bot.download_file(file.file_path)

        # Encode the file content to base64
        encoded_file_content = base64.b64encode(file_content.read()).decode("utf-8")
        files = [{"name": file_name, "data": encoded_file_content}]

        obj_tg_user = await db_request.get_telegram_user(send_to_id)

        if obj_tg_user:
            result = await db_request.get_or_create_communication_chat(
                obj_tg_user, chat_with)
        else:
            await message.answer("Помилка знаходження користувача.")
            return 0

        if result is None:
            await message.answer("Не вдалося створити чат.")
            return
        
        obj_chat, chat_created, sender_pk = result
        
        # Send data via websocket
        socket_result = await send_to_websocket(
            obj_chat.pk,
            sender_pk,
            message.text,
            message.message_id,
            chat_with=chat_with,
            files=files,
            file_type=file_type,
            source="site"
        )

        if socket_result:
            if media_type == "photo":
                await message.bot.send_photo(chat_id=send_to_id,
                                             photo=file_id,
                                             caption=message.caption)
            elif media_type == "video":
                await message.bot.send_video(chat_id=send_to_id,
                                             video=file_id,
                                             caption=message.caption)
            elif media_type == "voice":
                await message.bot.send_voice(chat_id=send_to_id,
                                             voice=file_id,
                                             caption=message.caption)
            else:
                return

            await message.answer(
                "Надіслано.",
                reply_markup=get_callback_btns(btns=back_to_menu))
        else:
            await message.answer(
                "Помилка надсилання.",
                reply_markup=get_callback_btns(btns=back_to_menu))

    except Exception as e:
        await message.answer(f"Виникла помилка при відправці медіа: {str(e)}")
