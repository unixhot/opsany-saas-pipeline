# -*- coding: utf-8 -*-
"""Django project settings
"""

from config import BK_URL

try:
    from django.conf import settings

    APP_CODE = settings.APP_ID
    SECRET_KEY = settings.APP_TOKEN
    try:
        from config import PAAS_ESB_URL
        COMPONENT_SYSTEM_HOST = PAAS_ESB_URL
    except Exception as e:
        COMPONENT_SYSTEM_HOST = BK_URL + "/api"
    DEFAULT_BK_API_VER = getattr(settings, 'DEFAULT_BK_API_VER', 'v2')
except Exception:
    APP_CODE = ''
    SECRET_KEY = ''
    COMPONENT_SYSTEM_HOST = ''
    DEFAULT_BK_API_VER = 'v2'

CLIENT_ENABLE_SIGNATURE = False
