from django import template
import json
from datetime import datetime

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

@register.filter(name='jsonify')
def jsonify(data, field):
    """Convert a list of dictionaries to a JSON array of values for a specific field"""
    if not data:
        return '[]'
    
    values = []
    for item in data:
        value = item.get(field)
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%d')
        values.append(value)
    
    return json.dumps(values)

@register.filter(name='format_key')
def format_key(value):
    """Convert snake_case to Title Case with spaces"""
    return value.replace('_', ' ').title() 