from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(str(key))

@register.filter
def sub(value, arg):
    try:
        return value - arg
    except (ValueError, TypeError):
        return value 