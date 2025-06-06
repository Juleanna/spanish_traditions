from .models import Cart

def shop_context(request):
    """Додає інформацію про магазин в контекст"""
    context = {}
    
    # Кошик
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
        else:
            cart = None
    
    if cart:
        context['cart_items_count'] = cart.total_items
        context['cart_total_price'] = cart.total_price
    else:
        context['cart_items_count'] = 0
        context['cart_total_price'] = 0
    
    # Порівняння
    compare_products = request.session.get('compare_products', [])
    context['compare_count'] = len(compare_products)
    
    return context