# -*- coding: utf-8 -*-
import logging
import traceback

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.db import IntegrityError

from blueapps.account import get_user_model
from blueapps.account.conf import ConfFixture
from blueapps.account.utils.http import send
from blueapps.utils import client
from config import APP_CODE

logger = logging.getLogger('component')

ROLE_TYPE_ADMIN = '1'


class TokenBackend(ModelBackend):
    error_msg = "token认证失败"
    def authenticate(self, request=None, bk_token=None, request_api_from=None, url_path=None, url_method=None):
        logger.debug(u"Enter in TokenBackend")
        # 判断是否传入验证所需的bk_token,没传入则返回None
        if not bk_token:
            self.error_msg = "token认证失败：Cookies中未发现bk_token"
            return None
        # login/accounts/get_user/ 接口增加 bk_role 字段
        verify_result, username, bk_role, msg = self.verify_bk_token(bk_token, request_api_from, url_path, url_method)
        # print("verify_result", verify_result, username, bk_role, bk_token)
        # 判断bk_token是否验证通过,不通过则返回None
        if not verify_result:
            self.error_msg = "token认证失败："+ str(msg)
            return None

        user_model = get_user_model()
        # print("获取用户模型get_user_model:", user_model)
        try:
            user, _ = user_model.objects.get_or_create(username=username)
            # print("获取用户信息get_or_create:", user, username)
            # 注释前往ESB拉取用户信息操作, verify_bk_token已经有了用户信息
            user_info = {
                "username": username,
                "role": bk_role,
            }
            request.user_info = user_info
            user.set_property(key='role', value=user_info.get('role') or "0")

            # 用户如果不是管理员，则需要判断是否存在平台权限，如果有则需要加上
            if not user.is_superuser and not user.is_staff:
                role = user_info.get('role', '')
                is_admin = True if str(role) == ROLE_TYPE_ADMIN else False
                user.is_superuser = is_admin
                user.is_staff = is_admin
                user.save()

            return user

        except IntegrityError:
            logger.exception(
                u"get_or_create UserModel fail or update_or_create UserProperty"
            )
            self.error_msg = "token认证失败：get_or_create UserModel fail or update_or_create UserProperty"
            return None
        except Exception:
            logger.exception(u"Auto create & update UserModel fail")
            self.error_msg = "token认证失败：Auto create & update UserModel fail"
            return None

    @staticmethod
    def verify_bk_token(bk_token, request_api_from, url_path, url_method):
        """
        请求VERIFY_URL,认证bk_token是否正确
        request_api_from: esb or web
        url_path: /api/v1_0/get-menu/
        url_method: GET
        @param bk_token: "_FrcQiMNevOD05f8AY0tCynWmubZbWz86HslzmOqnhk"
        @type bk_token: str
        @return: False,None True,username
        @rtype: bool,None/str
        """
        api_params = {
            'url_app_code': APP_CODE,
            'request_api_from': request_api_from,
            'url_path': url_path,
            'url_method': url_method,
            'bk_token': bk_token,
        }

        try:
            import time
            t1 = time.time()
            # print("验证Token是否有效参数", ConfFixture.VERIFY_URL, api_params)
            response = send(ConfFixture.VERIFY_URL, 'GET', api_params, verify=False)
            t2 = time.time()
            # print("验证Token是否有效返回, 耗时: ", t2 - t1, response)

        except Exception as e:
            logger.exception(f"Abnormal error in verify_bk_token{e}...")
            return False, None, None, f"Abnormal error in verify_bk_token({e})"

        if response.get('result'):
            data = response.get('data')
            username = data.get('username')
            bk_role = data.get('bk_role')
            return True, username, bk_role, ""
        else:
            error_msg = response.get('message', '')
            error_data = response.get('data', '')
            logger.error(u"Fail to verify bk_token, error=%s, ret=%s" % (
                error_msg, error_data))
            return False, None, None, error_msg
