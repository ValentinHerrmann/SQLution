from django import template

register = template.Library()

@register.filter(needs_autoescape=True)
def endswith(value, suffix, autoescape=True):
    return value.endswith(suffix)