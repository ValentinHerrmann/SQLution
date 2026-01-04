from django import template
from django.utils.safestring import mark_safe
import os
import re

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
def version_helper():
    url = "https://github.com/ValentinHerrmann/SQLution/releases/"
    
    version_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'VERSION')
    try:
        with open(version_file, 'r') as f:
            v = f.read().strip()
            if v.startswith("merge/"):
                v = v.replace("merge/", "")
                url = f"https://github.com/ValentinHerrmann/SQLution/pull/{v}"
                version = f"PR #{v}"
            elif re.match(r'^\d+(\.\d+)?(\.\d+)?$', v):
                version = v
                url = f"https://github.com/ValentinHerrmann/SQLution/releases/tag/{v}"
            else:
                version = v
    except Exception:
        version = '0.0.0'
        url = "https://github.com/ValentinHerrmann/SQLution/releases/"
    return (version, mark_safe(url))
    

@register.simple_tag
def get_version():
    return version_helper()[0]
    
@register.simple_tag
def get_version_url():
    return version_helper()[1]