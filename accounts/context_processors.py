from django.db.models import Sum
from shop.models import Wishlist, CartItem, Order


def user_stats(request):
    """Додає статистику користувача до контексту всіх шаблонів"""
    context = {}
    
    if request.user.is_authenticated:
        # Кількість товарів у списку бажань
        context['wishlist_count'] = Wishlist.objects.filter(
            user=request.user
        ).count()
        
        # Кількість товарів у кошику
        cart_items = CartItem.objects.filter(
            cart__user=request.user
        ).aggregate(total=Sum('quantity'))
        context['cart_items_count'] = cart_items['total'] or 0
        
        # Кількість активних замовлень
        context['pending_orders_count'] = Order.objects.filter(
            user=request.user,
            status__in=['pending', 'confirmed', 'processing', 'shipped']
        ).count()
        
        # Кількість товарів для порівняння
        comparison_products = request.session.get('comparison_products', [])
        context['comparison_count'] = len(comparison_products)
    
    return context