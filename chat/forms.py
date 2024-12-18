from django import forms
from .models import TelegramUser, CustomUser


class AdminCreateForm(forms.Form):
    username = forms.CharField(max_length=256, label="Юзернейм")
    first_name = forms.CharField(max_length=256, label="First name")
    last_name = forms.CharField(
        max_length=256,
        label="Last name",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Необов'язково"}),
    )

    telegram = forms.ModelChoiceField(
        queryset=TelegramUser.objects.filter(user__isnull=True),
        required=False,
        label="Telegram",
        # widget=forms.Select(attrs={"placeholder": "Необов'язково"}),
        empty_label="Необов'язково",
    )
