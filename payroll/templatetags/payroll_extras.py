from django import template

register = template.Library()


@register.filter
def euro(value):
    try:
        return f"€{value:,.2f}"
    except (TypeError, ValueError):
        return "€0.00"


@register.filter
def lookup(mapping, key):
    return mapping.get(key)
