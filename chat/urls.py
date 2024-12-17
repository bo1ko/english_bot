from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("", views.index, name="index"),
    path("admins_panel/", views.admins_panel, name="admins_panel"),
    path("create_admin/", views.create_admin, name="create_admin"),
]
