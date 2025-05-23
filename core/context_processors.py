from .models import MenuItem

def build_menu_tree(parent):
    """
    Рекурсивно строит дерево меню, добавляя дочерние элементы.
    """
    children = parent.children.filter(is_active=True).order_by('menu_order')
    return [
        {'item': child, 'children': build_menu_tree(child)}
        for child in children
    ]

def menu_context(request):
    """
    Формирует контекст для меню, добавляя дерево пунктов меню.
    """
    root_items = MenuItem.objects.filter(parent__isnull=True, is_active=True).order_by('menu_order')
    menu_tree = [
        {'item': item, 'children': build_menu_tree(item)}
        for item in root_items
    ]
    return {
        'menu_tree': menu_tree
    }
