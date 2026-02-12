from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_duration(value):
    """
    Formats a timedelta object into 'xx Dias e xx:xx Horas'.
    Example: 1 day, 2 hours, 30 minutes -> '1 Dias e 02:30 Horas'
    """
    if not isinstance(value, timedelta):
        return value # Return as is if it's not a timedelta (e.g. None or string)
    
    days = value.days
    seconds = value.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    return f"{days} Dias e {hours:02}:{minutes:02} Horas"
