from django import template

register = template.Library()

@register.filter(needs_autoescape=True)
def endswith(value, suffix, autoescape=True):
    return value.endswith(suffix)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})