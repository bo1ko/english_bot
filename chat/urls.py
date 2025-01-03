from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("", views.index, name="index"),
    path("panel/<str:page>/", views.panel, name="panel"),
    path("create/<str:page>/", views.create, name="create"),
    path("remove/<str:page>/<int:pk>/", views.remove, name="remove"),
    path(
        "update_telegram/<str:page>/<int:pk>/",
        views.update_telegram,
        name="update_telegram",
    ),
    path("settings/", views.settings, name="settings"),
    path("logout/", views.custom_logout, name="logout"),
    path("edit_students/", views.edit_students, name="edit_students"),
    path("add_student/", views.add_student, name="add_student"),
    path("remove_student/", views.remove_student, name="remove_student"),
    path("login", views.custom_login, name="login"),
    path("system_actions/", views.system_actions, name="system_actions"),
    path("system_actions/<int:pk>/", views.user_actions, name="user_actions"),
    path("telegram_users/", views.telegram_users, name="telegram_users"),
    path("chat/<str:chat_with>/<int:chat_id>", views.chat_room, name="chat_room"),
    path("inbox/", views.inbox, name="inbox"),
    path("edit-message/", views.edit_message, name="edit_message"),
    path("chat_list/<str:chat_with>", views.chat_list, name="chat_list"),
    path("send_media/", views.send_media, name="send_media"),
]

handler400 = views.custom_400
handler403 = views.custom_403
handler404 = views.custom_404
handler500 = views.custom_500

