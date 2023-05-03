from django import template

from nf_core.models import UserInfo

register = template.Library()


@register.simple_tag
def getPendingConfigurationCount():
    return UserInfo.objects.filter(config_status=False).count()
