from django.contrib.auth import logout
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .decorators import role_required
from .models import CustomUser, TelegramUser
from .forms import CreateForm, ChangeTelegramForm

import secrets
import string


@login_required
def index(request):
    context = {}

    if request.user.role == "super_administrator":
        context['welcome'] = "Головний адміністратор"

        return render(request, "chat/index.html", context)

    return render(request, "chat/index.html")


@role_required("super_administrator")
@login_required
def panel(request):
    custom_users = CustomUser.objects.filter(role="site_administrator")

    update_tg_form = ChangeTelegramForm()

    context = {
        "custom_users": custom_users,
        "update_tg_form": update_tg_form,
    }

    return render(
        request, "chat/panel.html", context
    )


@role_required("super_administrator")
@login_required
def create(request):
    if request.method == "POST":
        data = request.POST
        context = {}

        try:
            alphabet = string.ascii_letters + string.digits
            rand_password = "".join(secrets.choice(alphabet) for i in range(8))
            hash_rand_password = make_password(rand_password)
            tg_pk = data.get("telegram")

            if tg_pk:
                tg_obj = TelegramUser.objects.get(pk=tg_pk)
            else:
                tg_obj = None

            create_admin = CustomUser(
                username=data.get("username"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                telegram=tg_obj,
                role=CustomUser.SITE_ADMIN,
                password=hash_rand_password,
            )
            create_admin.save()
            context["success"] = "Адміна створено"
            context["admin_data"] = create_admin
            context["pwd"] = rand_password

        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                context["success"] = "Користувач з таким ім'ям вже існує"
            else:
                context["success"] = "Сталася помилка при створенні користувача"

        except Exception as e:
            print(e)
            context["success"] = "Адміна не створено"

        return render(request, "chat/result.html", {"context": context})
    else:
        form = CreateForm()

    return render(request, "chat/create.html", {"form": form})

@role_required("super_administrator")
@login_required
def remove(request, pk):
    admin_user = get_object_or_404(CustomUser, pk=pk)

    if admin_user.is_superuser:
        messages.error(request, "Неможливо видалити суперкористувача!")
        return redirect('chat:panel')

    admin_user.delete()
    messages.success(request, "Адміністратора успішно видалено.")
    return redirect('chat:panel')


@role_required("super_administrator")
@login_required
def update_telegram(request, pk):
    if request.method == "POST":
        try:
            data = request.POST
            telegram_id = data.get("telegram")

            if not telegram_id:
                messages.error(request, "Telegram ID не вказано.")
                return redirect("chat:panel")  # Замінити на вашу URL-ідентифікацію

            telegram_user = TelegramUser.objects.get(pk=telegram_id)
            user = CustomUser.objects.get(pk=pk)

            user.telegram = telegram_user
            user.save()

            messages.success(request, "Telegram успішно оновлено!")
            return redirect("chat:panel")  # Замінити на вашу URL-ідентифікацію

        except TelegramUser.DoesNotExist:
            messages.error(request, "Telegram користувача не знайдено.")
            return redirect("chat:panel")  # Замінити на вашу URL-ідентифікацію

        except CustomUser.DoesNotExist:
            messages.error(request, "Користувача не знайдено.")
            return redirect("chat:panel")  # Замінити на вашу URL-ідентифікацію

        except Exception as e:
            messages.error(request, f"Виникла помилка: {str(e)}")
            return redirect("chat:panel")  # Замінити на вашу URL-ідентифікацію

@role_required("super_administrator")
@login_required
def settings(request):
    return render(request, "chat/settings.html")

@login_required
def custom_logout(request):
    logout(request)

    return redirect("chat:panel")