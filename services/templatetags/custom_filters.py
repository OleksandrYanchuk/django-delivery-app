# custom_filters.py
from django.template import Library

register = Library()


@register.filter
def zip_lists(a, b):
    return zip(a, b)


@register.filter
def get_total(cart_items):
    return sum(item.total_price() for item in cart_items)


@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return ""
