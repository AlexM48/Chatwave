# mychat/templatetags/my_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Возвращает значение словаря по ключу"""
    return dictionary.get(key)
