from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .models import CustomUser


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
    return render(request, "chat/super_panel/create_admin.html")
