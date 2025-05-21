from .models import MenuItem

def menu_context(request):
    menu_items = MenuItem.objects.filter(parent__isnull=True, is_active=True).order_by('menu_order')
    return {
        'menu_items': menu_items
    }
