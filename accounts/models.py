from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserProfile(models.Model):
    """Розширений профіль користувача"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_("Користувач"))
    
    # Додаткова інформація
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Номер телефону повинен бути у форматі: '+999999999'. До 15 цифр.")
    )
    phone = models.CharField(_("Телефон"), validators=[phone_regex], max_length=17, blank=True)
    birth_date = models.DateField(_("Дата народження"), null=True, blank=True)
    
    # Адреса доставки за замовчуванням
    default_address_line1 = models.CharField(_("Адреса (рядок 1)"), max_length=255, blank=True)
    default_address_line2 = models.CharField(_("Адреса (рядок 2)"), max_length=255, blank=True)
    default_city = models.CharField(_("Місто"), max_length=100, blank=True)
    default_postal_code = models.CharField(_("Поштовий індекс"), max_length=20, blank=True)
    
    # Налаштування повідомлень
    email_notifications = models.BooleanField(_("Email повідомлення"), default=True)
    sms_notifications = models.BooleanField(_("SMS повідомлення"), default=False)
    newsletter_subscription = models.BooleanField(_("Підписка на розсилку"), default=True)
    
    # Статистика
    total_orders = models.PositiveIntegerField(_("Всього замовлень"), default=0)
    total_spent = models.DecimalField(_("Всього витрачено"), max_digits=10, decimal_places=2, default=0)
    
    # Інші поля
    notes = models.TextField(_("Примітки"), blank=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    
    class Meta:
        verbose_name = _("Профіль користувача")
        verbose_name_plural = _("Профілі користувачів")
    
    def __str__(self):
        return f"Профіль {self.user.username}"
    
    def get_full_name(self):
        """Повне ім'я користувача"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    def get_default_address(self):
        """Повна адреса за замовчуванням"""
        parts = [
            self.default_address_line1,
            self.default_address_line2,
            self.default_city,
            self.default_postal_code
        ]
        return ", ".join(filter(None, parts))
    
    def update_statistics(self):
        """Оновлення статистики користувача"""
        from shop.models import Order
        orders = Order.objects.filter(user=self.user, status='delivered')
        self.total_orders = orders.count()
        self.total_spent = sum(order.total_amount for order in orders)
        self.save()


# Сигнали для автоматичного створення профілю
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()