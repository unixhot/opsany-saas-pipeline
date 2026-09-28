# -*- coding: utf-8 -*-
"""
Copyright © 2012-2020 OpsAny. All Rights Reserved.
"""  # noqa
import re

import requests
import json

# forms.CharField
import settings
from config import APP_CODE, SECRET_KEY, BK_URL, DEFAULT_LANGUAGE


try:
    from config import PAAS_ESB_URL
    ESB_INNER_URL = PAAS_ESB_URL
except Exception as e:
    ESB_INNER_URL = BK_URL + "/api"
try:
    from config import PAAS_LOGIN_URL
    LOGIN_INNER_URL = PAAS_LOGIN_URL
except Exception as e:
    LOGIN_INNER_URL = BK_URL + "/login"


class EsbApi(object):
    def __init__(self, token=None, language=DEFAULT_LANGUAGE):
        self.token = token if token else ""
        self.app_code = APP_CODE
        self.app_secret = SECRET_KEY
        self.url = ESB_INNER_URL
        self.headers = {
            "Cookie": "bk_token={}; opsany_language={}".format(self.token, language)
        }

    def get_username(self):
        API = "/c/compapi/v2/bk_login/get_user/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            end_data = end_data.get("data").get("bk_username")
        return end_data

    def get_nav_and_collection(self):
        API = "/c/compapi/workbench/get_nav_and_collection/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        dt = {}
        if end_data.get("result"):
            end_data = end_data.get("data")
            return end_data
        return dt

    def get_language_theme_config(self, username):
        API = "/c/compapi/workbench/get_language_theme_config/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "user_token": self.token,
            "username": username,
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        dt = {}
        if end_data.get("result"):
            end_data = end_data.get("data")
            return end_data
        return dt

    def collection_nav(self, nav_id):
        API = "/c/compapi/workbench/post_collection/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "nav_id": nav_id
        }
        URL = self.url + API
        response = requests.post(url=URL, data=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            return end_data
        return None

    def get_user_message_info(self, current=1, pageSize=10):
        API = "/c/compapi/workbench/get_message_info/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "current": str(current),
            "pageSize": str(pageSize)
        }
        URL = self.url + API
        response = requests.post(url=URL, data=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            data = end_data.get("data")
            return data
        return None

    def get_user_group_sync(self):
        API = "/c/compapi/rbac/get_user_group_sync/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_username": "admin",
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            end_data = end_data.get("data")
            return end_data
        return {}

    def get_user_info(self):
        API = "/c/compapi/v2/bk_login/get_user/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        dt = {}
        if end_data.get("result"):
            dt["phone"] = end_data.get("data").get("phone")
            dt["username"] = end_data.get("data").get("bk_username")
            dt["email"] = end_data.get("data").get("email")
            dt["ch_name"] = end_data.get("data").get("chname")
            dt["role"] = end_data.get("data").get("bk_role")
        return dt

    def get_user_menu(self):
        API = "/c/compapi/rbac/post_menu_tree/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "platform_cname": self.app_code,
        }
        URL = self.url + API
        response = requests.post(url=URL, data=json.dumps(req), headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        return end_data.get("data")

    def guide(self, platform_code):
        API = "/c/compapi/workbench/guide/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "platform_code": platform_code
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            end_data = end_data.get("data")
            return end_data
        else:
            return end_data.get("response")

    def get_user_info_from_workbench(self):
        """从工作台ESB获取用户信息"""
        API = "/c/compapi/workbench/get_user_info_from_workbench/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
        }
        URL = self.url + API
        response = requests.post(url=URL, data=json.dumps(req), headers=self.headers, verify=False, timeout=2)
        end_data = json.loads(response.text)

        return end_data.get("data")

    def get_user_info_from_workbench_or_login(self):
        """首先获取工作台数据，获取不到再获取login数据"""
        try:
            end_data = self.get_user_info_from_workbench()
            if not end_data:
                raise Exception("workbench return None")
        except Exception as e:
            print("get_user_info_from_workbench_or_login_error_workbench:", e)
            default_user_icon = getattr(settings, "DEFAULT_USER_ICON",
                                        "uploads/workbench/user_icon/edfb99ee-08d6-41b8-ac5f-117fb86b0912.png")
            end_data = self.get_user_info()
            if end_data and isinstance(end_data, dict):
                end_data['icon_url'] = default_user_icon
        return end_data

    def read_all_message(self):
        API = "/c/compapi/workbench/get_read_all_message/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        return end_data.get("data")

    def get_copyright_config(self):
        API = "/c/compapi/rbac/get_copyright_config/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        dt = {}
        if end_data.get("result"):
            end_data = end_data.get("data")
            return end_data
        return dt

    def encrypt_text(self, text):
        """加密文本数据"""
        API = "/c/compapi/cmdb/encrypt_text/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "text": text
        }
        URL = self.url + API
        response = requests.post(url=URL, data=json.dumps(req), headers=self.headers, verify=False)
        end_data = response.json()
        return end_data

    def business_tree(self):
        API = "/c/compapi/devops/business_tree/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.post(url=URL, data=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            data = end_data.get("data")
            return data
        return []

    def get_agent_group_list(self):
        API = "/c/compapi/control/get_agent_group_list/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            end_data = end_data.get("data")
        return end_data

    def host_group_to_job(self, group_list, filters=None):
        """获取cmdb关联关系数据"""
        API = "/c/compapi/control/host_group_to_job/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "group_list": group_list,
            "filters": filters
        }
        data = json.dumps(req)
        URL = self.url + API
        response = requests.post(url=URL, data=data, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        return end_data

    def get_control_agent_info(self, system_type=None, group_type=None, search_type=None, search_data=None):
        API = "/c/compapi/control/get_control_agent_info/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            'token_data': self.token,
            'system_type': system_type,
            'search_type': search_type,
            'search_data': search_data,
            'group_type': group_type
        }
        URL = self.url + API
        response = requests.post(url=URL, data=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            data = end_data.get("data")
            agent_info = data[0].get("agent_info")
            for i in agent_info:
                re_rule = "^(127\.0\.0\.1)|(localhost)|(10\.\d{1,3}\.\d{1,3}\.\d{1,3})|(172\.((1[6-9])|(2\d)|(3[01]))\.\d{1,3}\.\d{1,3})|(192\.168\.\d{1,3}\.\d{1,3})$"
                c = re.findall(re_rule, i.get("ip"))
                if len(c) > 0:
                    i["ip_type"] = "(内)"
                elif i.get("ip") != "unknown":
                    i["ip_type"] = "(外)"
                else:
                    i["ip_type"] = "(外)"
            end_data = end_data.get("data")
        return end_data

    # 获取自己参与的项目且成员角色大于开发者的项目地址列表
    def get_gitlab_repository_url(self):
        """获取自己参与的项目且成员角色大于开发者的项目地址列表"""
        API = "/c/compapi/code/gitlab_repository_url/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        return end_data

    # 获取当前应用或公共应用下的raw类型的制品
    def get_nexus_repository_esb(self, code, format_type, search_type=None, search_data=None):
        """获取当前应用或公共应用下的raw类型的制品"""
        API = "/c/compapi/repo/get_nexus_repository/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_token": self.token,
            "code": code,
            "format_type": format_type,
            "search_type": search_type,
            "search_data": search_data
        }
        URL = self.url + API
        response = requests.get(url=URL, params=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        return end_data

    def send_out_message(self, temp_id, subscribe_type, parameter, operator, alert_info, result=True):
        API = "/c/compapi/workbench/post_info_to_user/"
        req = {
            "bk_app_code": self.app_code,
            "bk_app_secret": self.app_secret,
            "bk_username": operator,
            "bk_token": self.token,
            "operator": operator,
            "temp_id": temp_id,
            "subscribe_type": subscribe_type,
            "parameter": parameter,
            "result": result,
            "alert_info": json.dumps(alert_info),
        }
        URL = self.url + API
        response = requests.post(url=URL, data=req, headers=self.headers, verify=False)
        end_data = json.loads(response.text)
        if end_data.get("result"):
            return end_data
        return None


if __name__ == '__main__':
    # 业务：BUSINESS      应用：APPLICATION      服务：SERVICE
    pass
