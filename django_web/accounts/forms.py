"""
Формы для приложения accounts.
Здесь можно создавать кастомные формы для регистрации, редактирования профиля и т.д.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации с дополнительными полями"""
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Введите ваш email адрес'
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label='Имя',
        help_text='Ваше имя (необязательно)'
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Фамилия',
        help_text='Ваша фамилия (необязательно)'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Форма для обновления информации о пользователе"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=False, label='Имя')
    last_name = forms.CharField(max_length=30, required=False, label='Фамилия')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

