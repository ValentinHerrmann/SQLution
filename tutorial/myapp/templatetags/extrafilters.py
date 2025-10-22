from django import template
import os

register = template.Library()

@register.filter(needs_autoescape=True)
def endswith(value, suffix, autoescape=True):
    return value.endswith(suffix)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter(name='dict_get')
def dict_get(d, key):
    """Return d.get(key, '') in templates (safe for missing keys)."""
    try:
        if d is None:
            return ''
        return d.get(key, '')
    except Exception:
        return ''

@register.simple_tag
def get_version():
    """Read version from VERSION file"""
    version_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'VERSION')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"