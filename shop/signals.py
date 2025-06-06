from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review, Product, OrderItem


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    """
    Автоматично оновлює рейтинг товару при додаванні/видаленні відгуку
    """
    product = instance.product
    
    # Обчислюємо новий рейтинг
    reviews = Review.objects.filter(product=product, is_approved=True)
    avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
    reviews_count = reviews.count()
    
    # Оновлюємо товар
    product.rating = round(avg_rating, 2) if avg_rating else 0.00
    product.reviews_count = reviews_count
    product.save()


@receiver(post_save, sender=OrderItem)
def update_product_stock(sender, instance, created, **kwargs):
    """
    Зменшує кількість товару на складі при створенні замовлення
    """
    if created and instance.product.track_stock:
        product = instance.product
        if product.stock >= instance.quantity:
            product.stock -= instance.quantity
            product.save()


@receiver(post_save, sender=Review)
def mark_verified_purchase(sender, instance, created, **kwargs):
    """
    Позначає відгук як підтверджену покупку, якщо користувач купував товар
    """
    if created:
        # Перевіряємо, чи користувач купував цей товар
        has_purchased = OrderItem.objects.filter(
            order__user=instance.user,
            product=instance.product,
            order__status='delivered'
        ).exists()
        
        if has_purchased and not instance.is_verified_purchase:
            instance.is_verified_purchase = True
            instance.save()