from django import template

register = template.Library()

@register.filter
def times(value, arg):
    """
    Multiplies the value by the argument.
    Example: {{ job.exp_min | times:12 }}
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) * float(arg)
        except (ValueError, TypeError):
            return '' # Return empty string on failure
