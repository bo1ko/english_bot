from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("", views.index, name="index"),
    path("panel/", views.panel, name="panel"),
    path("create/", views.create, name="create"),
    path("remove/<int:pk>/", views.remove, name="remove"),
    path("update_telegram/<int:pk>/", views.update_telegram, name="update_telegram"),
    path("settings/", views.settings, name="settings"),
    path('logout/', views.custom_logout, name='logout'),
]
