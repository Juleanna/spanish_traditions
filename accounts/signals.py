from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order
from .models import UserProfile


@receiver(post_save, sender=Order)
def update_user_statistics(sender, instance, created, **kwargs):
    """Оновлення статистики користувача після створення або оновлення замовлення"""
    if instance.user and instance.status == 'delivered':
        try:
            profile = instance.user.profile
            profile.update_statistics()
        except UserProfile.DoesNotExist:
            # Якщо профіль не існує, створюємо його
            UserProfile.objects.create(user=instance.user)