from django import template

register = template.Library()

@register.filter
def dictsumby(value, arg):
    """Sum a list of dictionaries by the given key"""
    return sum(item[arg] for item in value) 