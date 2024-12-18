from django import forms
from .models import TelegramUser, CustomUser


class CreateForm(forms.Form):
    username = forms.CharField(
        max_length=256,
        label="Юзернейм",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=256,
        label="First name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=256,
        label="Last name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Необов'язково"})
    )
    telegram = forms.ModelChoiceField(
        queryset=TelegramUser.objects.filter(user__isnull=True),
        required=False,
        label="Telegram",
        empty_label="Необов'язково",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ChangeTelegramForm(forms.Form):
    telegram = forms.ModelChoiceField(
        queryset=TelegramUser.objects.filter(user__isnull=True),
        required=True,
        empty_label="Виберіть новий телеграм аккаунт",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
