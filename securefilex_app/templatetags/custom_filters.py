from django import template

register = template.Library()

@register.filter
def zip_lists(a, b):
    """Zips two lists together so they can be looped over in templates."""
    try:
        return zip(a, b)
    except Exception:
        return []
