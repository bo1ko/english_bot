from django import forms
from .models import TelegramUser, CustomUser
from django.core.exceptions import ValidationError


class CreateForm(forms.Form):
    username = forms.CharField(
        max_length=256,
        label="Юзернейм",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
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
        empty_label="Необов'язково, якщо не студент",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.CharField(
        widget=forms.HiddenInput(),
        label=""
    )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        telegram = cleaned_data.get("telegram")

        if role == 'students' and not telegram:
            self.add_error('telegram', 'This field is required for students.')

        return cleaned_data

class ChangeTelegramForm(forms.Form):
    telegram = forms.ModelChoiceField(
        queryset=TelegramUser.objects.filter(user__isnull=True),
        required=False,  # Дозволяє null значення
        empty_label="Виберіть новий телеграм аккаунт або залиште порожнім",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class UpdateSettingsForm(forms.Form):
    pwd = forms.CharField(max_length=256, widget=forms.PasswordInput(
        attrs={'id': 'pwd', 'class': 'form-control mb-1', 'placeholder': 'Введіть актуальний пароль'}), label='Актуальний пароль',
                          required=True)
    first_name = forms.CharField(
        max_length=256, widget=forms.TextInput(
            attrs={'id': 'first_name', 'class': 'form-control mb-1', 'placeholder': "Введіть нове ім'я"}), label="Ім'я",
        required=False
    )
    last_name = forms.CharField(max_length=256, widget=forms.TextInput(
        attrs={'last_name': 'last_name', 'class': 'form-control mb-1', 'placeholder': "Введіть нове прізвище"}), label="Прізвище",
                                required=False)

    new_pwd = forms.CharField(max_length=256, widget=forms.TextInput(
        attrs={'id': 'new_pwd', 'class': 'form-control mb-1', 'placeholder': "Введіть новий пароль"}),
                              label="Новий пароль",
                              required=False)

    repeat_new_pwd = forms.CharField(max_length=256, widget=forms.TextInput(
        attrs={'id': 'repeat_new_pwd', 'class': 'form-control mb-1', 'placeholder': "Введіть ще раз новий пароль"}),
                              label="Новий пароль",
                              required=False)

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        old_pwd = cleaned_data.get("pwd")
        new_pwd = cleaned_data.get("new_pwd")
        repeat_new_pwd = cleaned_data.get("repeat_new_pwd")

        if not(first_name or last_name or new_pwd and repeat_new_pwd):
            raise ValidationError("Ви повинні заповнити хоча б одне з полів.")

        if not old_pwd:
            raise ValidationError("Ви повинні ввести старий пароль для зміни даних.")

        if new_pwd:
            if not repeat_new_pwd:
                raise ValidationError("Ви повинні повторно ввести новий пароль.")
            if new_pwd != repeat_new_pwd:
                raise ValidationError("Паролі не співпадають.")

        return cleaned_data
