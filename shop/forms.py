from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from .models import Review


class ReviewForm(forms.ModelForm):
    """Форма для додавання відгуку"""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} зірок') for i in range(1, 6)], attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Заголовок відгуку')
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Ваш відгук про товар')
            }),
        }
        labels = {
            'rating': _('Оцінка'),
            'title': _('Заголовок'),
            'comment': _('Коментар'),
        }


class CheckoutForm(forms.Form):
    """Форма оформлення замовлення"""
    
    # Контактна інформація
    first_name = forms.CharField(
        label=_('Ім\'я'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введіть ваше ім\'я')
        })
    )
    
    last_name = forms.CharField(
        label=_('Прізвище'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введіть ваше прізвище')
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('email@example.com')
        })
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Номер телефону повинен бути у форматі: "+999999999". До 15 цифр дозволено.')
    )
    
    phone = forms.CharField(
    label=_('Телефон'),
    validators=[phone_regex],
    max_length=17,
    widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+380671234567'  # Убрали символ _ перед строкой
    })
    )
    
    # Адреса доставки
    address_line1 = forms.CharField(
        label=_('Адреса (рядок 1)'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Вулиця, номер будинку, квартира')
        })
    )
    
    address_line2 = forms.CharField(
        label=_('Адреса (рядок 2)'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Додаткова адресна інформація (необов\'язково)')
        })
    )
    
    city = forms.CharField(
        label=_('Місто'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Назва міста')
        })
    )
    
    state = forms.CharField(
        label=_('Область'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Назва області')
        })
    )
    
    postal_code = forms.CharField(
        label=_('Поштовий код'),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('12345')
        })
    )
    
    country = forms.CharField(
        label=_('Країна'),
        max_length=100,
        initial='Україна',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )
    
    # Додаткові примітки
    notes = forms.CharField(
        label=_('Примітки до замовлення'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Додаткові побажання або інструкції для доставки')
        })
    )
    
    # Згода з умовами
    terms_agreed = forms.BooleanField(
        label=_('Я погоджуюся з умовами обслуговування'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    privacy_agreed = forms.BooleanField(
        label=_('Я погоджуюся з політикою конфіденційності'),
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Додаткова валідація телефону
        if not phone.startswith('+'):
            if phone.startswith('0'):
                phone = '+38' + phone
            else:
                phone = '+380' + phone
        return phone


class ProductFilterForm(forms.Form):
    """Форма для фільтрації товарів"""
    
    SORT_CHOICES = [
        ('created_at', _('За новизною')),
        ('name', _('За назвою (А-Я)')),
        ('price_low', _('За ціною (зростання)')),
        ('price_high', _('За ціною (спадання)')),
        ('rating', _('За рейтингом')),
    ]
    
    search = forms.CharField(
        label=_('Пошук'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Пошук товарів...')
        })
    )
    
    category = forms.CharField(
        label=_('Категорія'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    min_price = forms.DecimalField(
        label=_('Мінімальна ціна'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('0')
        })
    )
    
    max_price = forms.DecimalField(
        label=_('Максимальна ціна'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('10000')
        })
    )
    
    sort_by = forms.ChoiceField(
        label=_('Сортування'),
        choices=SORT_CHOICES,
        required=False,
        initial='created_at',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    only_available = forms.BooleanField(
        label=_('Тільки в наявності'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    only_featured = forms.BooleanField(
        label=_('Тільки рекомендовані'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class NewsletterSubscriptionForm(forms.Form):
    """Форма підписки на розсилку"""
    
    email = forms.EmailField(
        label=_('Email адреса'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введіть ваш email')
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Тут можна додати додаткову валідацію email
        return email.lower()


class ContactForm(forms.Form):
    """Форма зворотного зв'язку"""
    
    name = forms.CharField(
        label=_('Ім\'я'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ваше ім\'я')
        })
    )
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('email@example.com')
        })
    )
    
    subject = forms.CharField(
        label=_('Тема'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Тема повідомлення')
        })
    )
    
    message = forms.CharField(
        label=_('Повідомлення'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _('Ваше повідомлення...')
        })
    )


class QuickOrderForm(forms.Form):
    """Форма швидкого замовлення"""
    
    name = forms.CharField(
        label=_('Ім\'я'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ваше ім\'я')
        })
    )
    
    phone = forms.CharField(
    label=_('Телефон'),
    max_length=17,
    widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+380671234567'
    })
    )
    
    comment = forms.CharField(
        label=_('Коментар'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Додаткові побажання (необов\'язково)')
        })
    )