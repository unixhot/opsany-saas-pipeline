# -*- coding: utf-8 -*-
from django.http import JsonResponse

from .models import UserInfo
from component.status_code import error, ErrorStatusCode


def admin_auth(func):
    def wrapper(self, request, *args, **kwargs):
        # ESB 服务间调用（管控平台持有 APP_CODE+APP_TOKEN 已通过 middleware 校验并写入
        # bk_esb_username / request_api_from=esb）视为可信通道，直接放行
        if request.COOKIES.get("request_api_from") == "esb" and request.COOKIES.get("bk_esb_username"):
            return func(self, request, *args, **kwargs)
        bk_token_username = request.COOKIES.get("bk_token_username")
        user_query = UserInfo.fetch_one(username=bk_token_username)
        if (not user_query) or (user_query.role != 1):
            return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER))
        return func(self, request, *args, **kwargs)
    return wrapper
