from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag
def contrib_identify_enabled():
    return getattr(settings, "USE_CONTRIB_IDENTIFY", False)
