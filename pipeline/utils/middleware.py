from django.http.response import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import json
import settings
from component.status_code import error, ErrorStatusCode

from config import BK_URL, APP_CODE
from pipeline.models import UserInfo
from component.esb_api import EsbApi


ENV = {"dev": "", "prod": "o", "stag": "t"}


class CreateUserMiddleware(MiddlewareMixin):
    def process_view(self, request, view, arg, kwarg):

        import platform
        # print("platform.system()", platform.system())
        if (not request.COOKIES.get("bk_token")) and (platform.system() == "Windows"):
            # request.COOKIES.update(**{"bk_token": "LJF1ufk4Gtyn8zUs66WBVGCbgxIbequ17_kGNDzyyhs"})
            request.COOKIES.update(**{"bk_token": "HAGKhjq6Fxlyxrgk0vuUH7L5QQkL_c4Q5lzzFRs-_sE"})

        if getattr(view, 'login_exempt_v2', False):
            return None
        username = None
        if request.method == "GET":
            operator = request.GET.get("operator")
            if operator:
                username = operator
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                operator = data.get("operator")
                if operator:
                    username = operator
            except Exception:
                # 上传文件
                pass
        if not username:
            token = request.COOKIES.get("bk_token")
            # bk_user = EsbApi(token).get_user_info_from_workbench()
            bk_user = EsbApi(token).get_user_info_from_workbench_or_login()
            if not bk_user:
                login_out_url = "https%3A//" + BK_URL.split("https://")[-1] + "/" + ENV.get(getattr(settings, "run_env", "dev")) +"/{}/&is_from_logout=1".format(APP_CODE)
                return JsonResponse(error(ErrorStatusCode.INVALID_TOKEN, login_out_url))
            username = bk_user.get("username")
            bk_user.pop('id', None)

            # mongo
            user = UserInfo.fetch_one(username=username)
            if not user:
                user = UserInfo.create(**bk_user)
            else:
                user = user.update(**bk_user)
            request.COOKIES["user_id"] = user.id
        else:
            user = UserInfo.fetch_one(username=username)
            token = request.COOKIES.get("bk_token")
            if not user and token:
                # bk_user = EsbApi(token).get_user_info_from_workbench()
                bk_user = EsbApi(token).get_user_info_from_workbench_or_login()
                bk_user.pop('id', None)
                username = bk_user.get("username")
                user = UserInfo.fetch_one(username=username)
                if not user:
                    user = UserInfo.create(**bk_user)
                else:
                    user = user.update(**bk_user)
                request.COOKIES["user_id"] = user.id
            elif user:
                request.COOKIES["user_id"] = user.id
            else:
                login_out_url = "https%3A//" + BK_URL.split("https://")[-1] + "/" + ENV.get(getattr(settings, "run_env", "dev")) +"/{}/&is_from_logout=1".format(APP_CODE)
                return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, login_out_url))
        return None
