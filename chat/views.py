from django.db import IntegrityError
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .decorators import role_required
from .models import CustomUser, TelegramUser
from .forms import AdminCreateForm

import secrets
import string


@login_required
def index(request):
    if request.user.role == "super_administrator":
        return render(request, "chat/super_panel/super_admin_panel.html")

    return render(request, "chat/index.html")


@role_required("super_administrator")
@login_required
def admins_panel(request):
    custom_users = CustomUser.objects.filter(role="site_administrator")

    return render(
        request, "chat/super_panel/admins_panel.html", {"custom_users": custom_users}
    )


@role_required("super_administrator")
@login_required
def create_admin(request):
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

        return render(request, "chat/super_panel/result.html", {"context": context})
    else:
        form = AdminCreateForm()

    return render(request, "chat/super_panel/create_admin.html", {"form": form})
