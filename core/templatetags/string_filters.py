from django import template
from django.utils import timezone
from django.conf import settings
import pytz

register = template.Library()

@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False

@register.filter
def nz_timezone(value):
    """
    Convert a datetime to New Zealand timezone for display.
    Usage: {{ some_datetime|nz_timezone|date:'Y-m-d H:i' }}
    """
    if value is None:
        return value
    
    # If it's already timezone-aware, convert to NZ time
    if timezone.is_aware(value):
        # Use Django's timezone utilities
        nz_tz = timezone.get_default_timezone()
        return value.astimezone(nz_tz)
    
    # If it's naive, assume it's in UTC and make it timezone-aware first
    utc_tz = pytz.UTC
    utc_dt = utc_tz.localize(value)
    nz_tz = timezone.get_default_timezone()
    return utc_dt.astimezone(nz_tz) 