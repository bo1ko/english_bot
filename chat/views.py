from datetime import datetime, timezone
from django.contrib.auth import logout, authenticate, login
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from .decorators import role_required
from .models import (
    CustomUser,
    TeacherAndAdminChat,
    TelegramUserAndAdminChat,
    TelegramUser,
    StudentAndTeacherChat,
    SystemAction,
)
from .forms import CreateForm, ChangeTelegramForm, UpdateSettingsForm
from .utils import (
    edit_sync_telegram_message,
    reply_sync_telegram_message,
    send_sync_telegram_message,
)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

import secrets
import string


@login_required()
def index(request):
    context = {}

    if request.user.role == "super_administrator":
        context["welcome"] = "Головний адміністратор"
        return render(request, "chat/index.html", context)
    elif request.user.role == "site_administrator":
        context["welcome"] = "Адміністратор"
        return render(request, "chat/index.html", context)

    return render(request, "chat/index.html")


@role_required(["super_administrator", "site_administrator"])
@login_required
def panel(request, page):
    context = {}
    
    
    if page == "admins" and request.user.role == "super_administrator":
        custom_users = CustomUser.objects.filter(role="site_administrator")
        update_tg_form = ChangeTelegramForm()

        context["custom_users"] = custom_users
        context["update_tg_form"] = update_tg_form
        context["title"] = "адміністраторів"
        context["button_create_name"] = "Адмін"
    elif page == "teachers":
        custom_users = CustomUser.objects.filter(role="teacher")
        update_tg_form = ChangeTelegramForm()
        context["custom_users"] = custom_users
        context["update_tg_form"] = update_tg_form
        context["title"] = "вчителів"
        context["button_create_name"] = "Вчитель"
    elif page == "students" and request.user.role == "super_administrator":
        custom_users = CustomUser.objects.filter(role="student")
        update_tg_form = ChangeTelegramForm()
        context["custom_users"] = custom_users
        context["update_tg_form"] = update_tg_form
        context["title"] = "студентів"
        context["button_create_name"] = "Студент"
    elif page == "system_actions":
        return render(request, "chat/system_actions.html", context)
    else:
        raise PermissionDenied

    context["page"] = page

    return render(request, "chat/panel.html", context)


@role_required("super_administrator")
@login_required
def create(request, page):
    context = {}

    if page == "admins":
        context["create"] = "адміністратора"
    elif page == "teachers":
        context["create"] = "вчителя"
    elif page == "students":
        context["create"] = "студента"

    context["page"] = page

    if request.method == "POST":
        data = request.POST

        try:
            form = CreateForm(data)

            if form.is_valid():
                alphabet = string.ascii_letters + string.digits
                if page == "students":
                    rand_password = "".join(secrets.choice(alphabet) for i in range(32))
                else:
                    rand_password = "".join(secrets.choice(alphabet) for i in range(8))
                hash_rand_password = make_password(rand_password)
                tg_pk = data.get("telegram")

                if tg_pk:
                    tg_obj = TelegramUser.objects.get(pk=tg_pk)
                else:
                    tg_obj = None

                create_user = CustomUser(
                    username=data.get("username"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    telegram=tg_obj,
                    role=(
                        CustomUser.SITE_ADMIN
                        if page == "admins"
                        else (
                            CustomUser.TEACHER
                            if page == "teachers"
                            else CustomUser.STUDENT
                        )
                    ),
                    password=hash_rand_password,
                )
                create_user.save()

                if tg_obj:
                    message = f"Ви получили роль {context["create"]}."
                    send_sync_telegram_message(tg_obj.tg_id, message)

                messages.success(request, "Аккаунт створено")
                context["admin_data"] = create_user

                if page != "students":
                    context["pwd"] = rand_password
            else:
                messages.error(
                    request, "При створенні студента потрібно вказати телеграм"
                )

        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                messages.error(request, "Користувач з таким ім'ям вже існує")
            else:
                messages.error(request, "Сталася помилка при створенні користувача")

        except Exception as e:
            print(e)
            messages.error(request, "Аккаунт не створено")

        return render(request, "chat/result.html", {"context": context})
    else:
        form = CreateForm(initial={"role": page})

        if page == "students":
            form.fields["telegram"].required = True

        context["form"] = form

    return render(request, "chat/create.html", {"context": context})


@role_required("super_administrator")
@login_required
def remove(request, page, pk):
    admin_user = get_object_or_404(CustomUser, pk=pk)

    if admin_user.is_superuser:
        messages.error(request, "Неможливо видалити суперкористувача!")
        return redirect("chat:panel")

    admin_user.delete()

    messages.success(request, "Аккаунт успішно видалено.")
    return redirect("chat:panel", page=page)


@role_required("super_administrator")
@login_required
def update_telegram(request, page, pk):
    if request.method == "POST":
        try:
            data = request.POST
            telegram_id = data.get("telegram")

            if telegram_id:
                telegram_user = TelegramUser.objects.get(pk=telegram_id)
            else:
                telegram_user = None
            user = CustomUser.objects.get(pk=pk)

            user.telegram = telegram_user
            user.save()

            if telegram_user:
                message = f"Телеграм аккаунт підключено до нового профілю."
                send_sync_telegram_message(telegram_user.tg_id, message)

            messages.success(request, "Telegram успішно оновлено!")

        except TelegramUser.DoesNotExist:
            messages.error(request, "Telegram користувача не знайдено.")

        except CustomUser.DoesNotExist:
            messages.error(request, "Користувача не знайдено.")

        except Exception as e:
            messages.error(request, f"Виникла помилка: {str(e)}")

        return redirect("chat:panel", page=page)


@role_required("super_administrator")
@login_required
def edit_students(request):
    teachers = CustomUser.objects.filter(role=CustomUser.TEACHER)
    students = CustomUser.objects.filter(role=CustomUser.STUDENT)

    assigned_students = {}

    for teacher in teachers:
        if teacher.student_list:
            assigned_students[teacher.id] = CustomUser.objects.filter(
                id__in=teacher.student_list
            )
        else:
            assigned_students[teacher.id] = CustomUser.objects.none()

    assigned_student_ids = [
        student.id
        for student_list in assigned_students.values()
        for student in student_list
    ]
    unassigned_students = students.exclude(pk__in=assigned_student_ids)

    context = {
        "teachers": teachers,
        "students": students,
        "unassigned_students": unassigned_students,
        "assigned_students": assigned_students,
    }

    return render(request, "chat/edit_students.html", {"context": context})


@role_required("super_administrator")
@login_required
def add_student(request):
    if request.method == "POST":
        try:
            data = request.POST
            student_id = data.get("student_id")
            teacher_id = data.get("teacher_id")

            if student_id and teacher_id:
                student = CustomUser.objects.get(pk=student_id)
                teacher = CustomUser.objects.get(pk=teacher_id)

                if student.is_student() and teacher.is_teacher():
                    if teacher.student_list is None:
                        teacher.student_list = []

                    teacher.student_list.append(student.pk)
                    teacher.save()

                    chat = StudentAndTeacherChat(student=student, teacher=teacher)
                    chat.save()

                    messages.success(
                        request,
                        f"Учень {student.username} успішно доданий до вчителя {teacher.username}",
                    )
                else:
                    messages.error(request, f"Щось пішло не так. Спробуйте знову.")
            else:
                messages.error(request, f"Щось пішло не так. Спробуйте знову.")

            return redirect("chat:edit_students")

        except CustomUser.DoesNotExist:
            return redirect("chat:edit_students")
        except Exception as e:
            print(e)
            return redirect("chat:edit_students")


@role_required("super_administrator")
@login_required
def remove_student(request):
    if request.method == "POST":
        try:
            data = request.POST
            student_id = data.get("student_id")
            teacher_id = data.get("teacher_id")

            if student_id and teacher_id:
                student = CustomUser.objects.get(pk=student_id)
                teacher = CustomUser.objects.get(pk=teacher_id)

                if student.is_student() and teacher.is_teacher():
                    if teacher.student_list is None:
                        teacher.student_list = []

                    teacher.student_list.remove(student.pk)
                    teacher.save()

                    messages.success(
                        request,
                        f"Учня {student.username} видалено у вчителя {teacher.username}",
                    )
                    return redirect("chat:edit_students")
        except Exception as e:
            print(e)
            return redirect("chat:edit_students")


@login_required
def settings(request):
    if request.method == "POST":
        try:
            form = UpdateSettingsForm(request.POST)

            if form.is_valid():
                old_pwd = form.cleaned_data.get("pwd")
                first_name = form.cleaned_data.get("first_name")
                last_name = form.cleaned_data.get("last_name")
                new_pwd = form.cleaned_data.get("new_pwd")
                repeat_new_pwd = form.cleaned_data.get("repeat_new_pwd")

                user = CustomUser.objects.get(pk=request.user.pk)

                if check_password(old_pwd, user.password):
                    if first_name:
                        user.first_name = first_name
                    if last_name:
                        user.last_name = last_name
                    if new_pwd:
                        if new_pwd == repeat_new_pwd:
                            user.password = make_password(new_pwd)

                    user.save()
                    messages.success(request, "Дані успішно оновлені.")
                    return redirect("chat:settings")
                else:
                    messages.error(request, "Пароль не підійшов.")
                    return redirect("chat:settings")
            else:
                messages.error(request, "Дані форми невалідні.")
                return redirect("chat:settings")

        except Exception as e:
            print(e)
            messages.error(request, "Внутрішня помилка сервера.")
            return redirect("chat:settings")
    else:
        form = UpdateSettingsForm()

    return render(request, "chat/settings.html", {"form": form})


def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Перевірка наявності користувача
        user = authenticate(request, username=username, password=password)
        roles = ["super_administrator", "site_administrator", "teacher"]

        if user is not None:
            login(request, user)
            if user.role in roles:
                return redirect("chat:index")
            else:
                messages.error(request, "Невірна роль користувача")
                return redirect("chat:login")
        else:
            messages.error(request, "Невірне ім'я користувача або пароль")
            return redirect("chat:login")

    return render(request, "chat/login.html")


@login_required
def custom_logout(request):
    logout(request)
    return redirect("chat:login")


@login_required
def system_actions(request):
    actions = SystemAction.objects.all()

    context = {"actions": actions}

    return render(request, "chat/system_actions.html", context)


@login_required
def user_actions(request, pk):
    action = SystemAction.objects.get(pk=pk)

    context = {
        "pk": pk,
        "tg_user": (
            action.telegram.username
            if action.telegram.username is not None
            else action.telegram.tg_id
        ),
        "actions_json": action.action,
        "update_at": action.updated_at,
    }

    return render(request, "chat/user_actions.html", context)


@login_required
def telegram_users(request):
    users = TelegramUser.objects.all()
    context = {
        "tg_users": users,
    }

    return render(request, "chat/telegram_accounts.html", context)


@role_required(["super_administrator", "site_administrator"])
@login_required
def inbox(request):
    chats = TelegramUserAndAdminChat.objects.filter(admin=None)

    for chat in chats:
        if chat.messages:
            last_message = chat.messages[-1].get("text", "")
        else:
            last_message = None
        chat.last_message = last_message

    context = {"chats": chats}
    return render(request, "chat/inbox.html", context)


@csrf_protect
@login_required
@require_POST
def edit_message(request):
    chat_id = request.POST.get("chat_id")
    message_id = request.POST.get("message_id")
    chat_with = request.POST.get("chat_with")

    if request.user.role == "super_administrator":
        user_role = f"<b><i>Головний адміністратор</i></b>"
    elif request.user.role == "site_administrator":
        user_role = f"<b><i>Адміністратор {request.user.first_name}</i></b>"
    elif request.user.role == "teacher":
        user_role = f"<b><i>Вчитель {request.user.first_name}</i></b>"

    new_text = request.POST.get("message")

    try:
        tg_chat_id = None
        if chat_with == "telegram_user":
            obj = TelegramUserAndAdminChat
            tg_chat_id = obj.objects.get(pk=chat_id).telegram_user.tg_id
        elif chat_with == "student":
            obj = StudentAndTeacherChat
            tg_chat_id = obj.objects.get(pk=chat_id).student.telegram.tg_id
        
        tg_edit_result = edit_sync_telegram_message(
            int(tg_chat_id), int(message_id), f"{user_role}\n{new_text}"
        )

        if tg_edit_result:
            chat = obj.objects.get(id=chat_id)
            messages = chat.messages

            for message in messages:
                if message.get("message_id") == int(message_id):
                    if "edited_text" in message:
                        message["edited_text"].append(
                            {
                                "edit_text": message["text"],
                                "edit_time": datetime.now(timezone.utc).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        )
                    else:
                        message["edited_text"] = [
                            {
                                "edit_text": message["text"],
                                "edit_time": datetime.now(timezone.utc).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        ]

                    message["text"] = new_text

                    break
            else:
                return JsonResponse({"success": False, "error": "Message not found"})

            chat.messages = messages
            chat.save()

            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"success": False, "error": "Could not edit message in telegram"}
            )
    except Exception as e:
        print("Edit message error", e)
        return JsonResponse({"success": False, "error": "Chat does not exist"})


@login_required
def chat_list(request, chat_with):
    context = {}

    if chat_with == "students":
        if (
            request.user.role == "super_administrator"
            or request.user.role == "site_administrator"
        ):
            chats = StudentAndTeacherChat.objects.all()
        elif request.user.role == "teacher":
            teacher = CustomUser.objects.get(username=request.user.username)
            chats = StudentAndTeacherChat.objects.filter(teacher=teacher)
        else:
            return

        context["title"] = "Чати з учнями"

    elif chat_with == "telegram_users":
        if request.user.role == "super_administrator":
            chats = TelegramUserAndAdminChat.objects.filter(admin__isnull=False)
        elif request.user.role == "site_administrator":
            admin = CustomUser.objects.get(username=request.user.username)
            chats = TelegramUserAndAdminChat.objects.filter(admin=admin)
        else:
            return

        context["title"] = "Чати з телеграм користувачами"
    elif chat_with == "teacher":
        if request.user.role == "super_administrator":
            chats = TeacherAndAdminChat.objects.all()
        elif request.user.role == "site_administrator":
            admin = CustomUser.objects.get(username=request.user.username)
            chats = TeacherAndAdminChat.objects.filter(admin=admin)
        elif request.user.role == "teacher":
            teacher = CustomUser.objects.get(pk=request.user.pk)
            chats = TeacherAndAdminChat.objects.filter(teacher=teacher)
        else:
            return
    else:
        return

    for chat in chats:
        if chat.messages:
            last_message = chat.messages[-1].get("text", "")
        else:
            last_message = "No messages"
        chat.last_message = last_message

    context["chats"] = chats
    context["chat_with"] = chat_with

    return render(request, "chat/chat_list.html", context)


@login_required
def chat_room(request, chat_with, chat_id):
    if chat_with == "telegram_user":
        admin = CustomUser.objects.get(pk=request.user.pk)
        telegram = TelegramUser.objects.get(pk=chat_id)
        chat, _ = TelegramUserAndAdminChat.objects.get_or_create(
            telegram_user=telegram, admin=admin
        )
    elif chat_with == "student":
        chat = get_object_or_404(StudentAndTeacherChat, pk=chat_id)
    elif chat_with == "teacher":
        if request.user.role == "teacher":
            chat = get_object_or_404(TeacherAndAdminChat, pk=chat_id, teacher=request.user)
        else:
            admin = CustomUser.objects.get(pk=request.user.pk)
            teacher = CustomUser.objects.get(pk=chat_id)
            chat, _ = TeacherAndAdminChat.objects.get_or_create(teacher=teacher, admin=admin)

    obj_messages = chat.messages if chat.messages else []

    for message in obj_messages:
        message["created_at"] = datetime.fromisoformat(message["created_at"])

    context = {
        "obj_messages": obj_messages,
        "chat": chat,
        "chat_with": chat_with,
    }

    return render(request, "chat/chat_room.html", context)
