# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib import auth

from blueapps.account.components.bk_token.backends import TokenBackend
from pipeline.models import UserInfo

try:
    from django.utils.deprecation import MiddlewareMixin
except Exception:
    MiddlewareMixin = object
import json
from config import BK_URL, APP_CODE, SECRET_KEY
import settings as env_config
from blueapps.account.conf import ConfFixture
from blueapps.account.handlers.response import ResponseHandler, JsonResponse
from blueapps.account.components.bk_token.forms import AuthenticationForm
from component.status_code import error, ErrorStatusCode

logger = logging.getLogger('component')

ENV = {"dev": "", "prod": "o", "stag": "t"}

esb_api_startswith = f"/api/{APP_CODE}/esb/v0_1/"


class LoginRequiredMiddleware(MiddlewareMixin):
    def process_view(self, request, view, args, kwargs):
        """
        Login paas by two ways
        1. views decorated with 'login_exempt' keyword
        2. User has logged in calling auth.login
        """
        auth = TokenBackend()
        request.COOKIES.update(**{"bk_token_username": None})
        request.COOKIES.update(**{"bk_esb_username": None})
        request.COOKIES.update(**{"request_api_from": "web"})

        # request.COOKIES.update(**{"bk_token": "cZgk12NTU_pwJ-lsm2Jg6ngCv_KFTpHhon6flrPbpGrIn_r3GcipOV5Y-bYtmfEd"})
        # request.COOKIES.update(**{"bk_token": "vlgMLpeyO37iVzf1JDkds_KsqmZfD4LIqzMT1VPrwsBFLrcDXn6Ff_DHWxB-5l5m455J3GsP_-_vsWBX7kveA"})
        app_token, request_api_from = self._check_app_token(request)
        url_method, url_path = request.method, request.path_info
        if url_path.startswith(esb_api_startswith) and request_api_from != "esb":
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_ESB_AUTH))

        if hasattr(request, 'is_wechat') and request.is_wechat(): return None

        if hasattr(request, 'is_bk_jwt') and request.is_bk_jwt():
            return None

        if getattr(view, 'login_exempt', False):
            return None
        form = AuthenticationForm(request.COOKIES)
        login_out_url = "https%3A//" + BK_URL.split("https://")[-1] + "/" + ENV.get(getattr(env_config, "run_env", "dev")) + "/{}/&is_from_logout=1".format(APP_CODE)
        if form.is_valid():
            bk_token = form.cleaned_data['bk_token']
            user = None
            if bk_token:
                user = auth.authenticate(request=request, bk_token=bk_token, request_api_from=request_api_from, url_path=url_path, url_method=url_method)
            if not user:
                if app_token:
                    return None
                return JsonResponse(error(ErrorStatusCode.INVALID_TOKEN, login_out_url, custom_message=str(auth.error_msg)))
            if user.username and user.is_active:
                request.COOKIES.update(**{"bk_token_username": user.username})
                return None
            return JsonResponse(error(ErrorStatusCode.INVALID_TOKEN, login_out_url, custom_message=str(auth.error_msg)))

        if app_token:
            return None
        if request.path_info == "/":
            handler = ResponseHandler(ConfFixture, settings)
            return handler.build_401_response(request)
        else:
            return JsonResponse(error(ErrorStatusCode.INVALID_TOKEN, login_out_url, custom_message=str(auth.error_msg)))

    def _check_app_token(self, request):
        headers = request.headers
        app_code = headers.get("X-APP-CODE")
        app_token = headers.get("X-APP-TOKEN")
        if APP_CODE == app_code and app_token == SECRET_KEY:
            request.COOKIES.update(**{"request_api_from": "esb"})
            try:
                data = json.loads(request.body)
            except:
                data = {}
            bk_esb_username = request.GET.get("operator") or request.POST.get("operator") or data.get("operator")
            query = UserInfo.objects.filter(username=bk_esb_username).first()
            if query:
                if query.username and query.is_activate:
                    request.COOKIES.update(**{"bk_esb_username": bk_esb_username})
                    return True, "esb"
            return False, "esb"
        return False, "web"

    def process_response(self, request, response):
        return response
