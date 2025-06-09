from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """Форма реєстрації користувача"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email')
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ім\'я')
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Прізвище')
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ім\'я користувача')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Пароль')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Підтвердіть пароль')
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує'))
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Форма оновлення даних користувача"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує'))
        return email


class UserProfileForm(forms.ModelForm):
    """Форма профілю користувача"""
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'birth_date', 
            'default_address_line1', 'default_address_line2',
            'default_city', 'default_postal_code',
            'email_notifications', 'sms_notifications', 'newsletter_subscription'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380991234567'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'default_address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Вулиця, будинок, квартира')
            }),
            'default_address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Додаткова інформація')
            }),
            'default_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Місто')
            }),
            'default_postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Поштовий індекс')
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'newsletter_subscription': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'phone': _('Телефон'),
            'birth_date': _('Дата народження'),
            'default_address_line1': _('Адреса (рядок 1)'),
            'default_address_line2': _('Адреса (рядок 2)'),
            'default_city': _('Місто'),
            'default_postal_code': _('Поштовий індекс'),
            'email_notifications': _('Отримувати email повідомлення'),
            'sms_notifications': _('Отримувати SMS повідомлення'),
            'newsletter_subscription': _('Підписатись на розсилку новин'),
        }