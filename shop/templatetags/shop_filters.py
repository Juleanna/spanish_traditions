from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Отримати значення зі словника за ключем"""
    return dictionary.get(str(key))

@register.filter
def make_list(value):
    """Перетворює рядок на список"""
    return list(value)