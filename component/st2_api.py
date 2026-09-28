import json
import os
import sys
import ssl
import requests

ssl._create_default_https_context = ssl._create_unverified_context

import urllib3

urllib3.disable_warnings()

# AUTH_TOKENS = "auth/v1/tokens/"  # 登录 POST
AUTH_TOKENS = "auth/tokens/"  # 登录 POST
VERSION_URL = "api/v1/"  # 获取版本 GET
GET_POST_ACTION = "/api/v1/actions/"  # GET POST
GET_PUT_DELETE_ACTION = "/api/v1/actions/{ref_or_id}/"  # PUT DELETE
EXECUTIONS_ACTION = "api/v1/executions/"
GET_PUT_DELETE_EXECUTION = "/api/v1/executions/{execution_id}/"


class StackStormApi:
    def __init__(self, url="", api_key=None, timeout=5):
        # url="http://120.131.9.34/", username="st2admin", password="Ch@ngeMe"
        if url and url[-1] == '/':
            self.url = url
        else:
            self.url = url + '/'
        self.timeout = timeout
        self.api_key = api_key
        self.headers = {
        }

    def st2_login(self):
        try:
            from pipeline.models import EventStackStormServiceModel
            # EventStackStormServiceModel.create(
            #     tool_name="StackStorm",
            #     api_addr="https://120.131.9.229/",
            #     api_token="MDcxYzU3MmI1NzM2ZDQ2MWMyZTczNDgwNzRiMjExNzkwMmQ1NjQ5MzY2YTBiZmVkNjdlOTc1ODRmZjY1YjEyMg"
            # )
            if not all([self.url, self.api_key]):
                stack_storm_query = EventStackStormServiceModel.fetch_one(tool_name="StackStorm")
                if stack_storm_query:
                    url = stack_storm_query.api_addr
                    if url and url[-1] == '/':
                        self.url = url
                    else:
                        self.url = url + '/'
                    self.api_key = stack_storm_query.api_token
                else:
                    return False, "未配置StackStorm或配置错误"

            self.headers.update({"st2-api-key": self.api_key})
            url = self.url + VERSION_URL
            res = requests.get(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 200:
                return True, "success"
            else:
                return False, "StackStorm服务器错误，请检查StackStorm服务是否运行正常"
        except requests.exceptions.ConnectTimeout as e:
            return False, "连接超时，请检查StackStorm服务是否运行正常"
        except requests.exceptions.ConnectionError as e:
            return False, "连接失败，请检查StackStorm服务是否运行正常"
        except Exception as e:
            return False, "操作失败({})".format(str(e))

    def get_version(self):
        """获取版本号"""
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + VERSION_URL
            # self.headers.update({"x-auth-token": self.tokens.get("data")})
            res = requests.get(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 200 or res.status_code == 204:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def get_workflow(self, ref_or_id):
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_PUT_DELETE_ACTION.format(ref_or_id=ref_or_id)
            res = requests.get(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 200:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def create_workflow(self, data_dic):
        """新建工作流
        {
            "pack": "develop_deploy",
            "name": "test",
            "runner_type": "orquesta",
            "entry_point": "workflows/test.yaml",
            "metadata_file": "actions/test.meta.yaml",
            "enabled": true,
            "data_files": [
                {
                    "file_path": "workflows/test.yaml",
                    "content": "version: 1.0\ntasks:\n  # [384, 193]\n  task1:\n    action: opsany.get_info\n"
                },
                {
                    "file_path": "test.meta.yaml",
                    "content": "pack: develop_deploy\nenabled: true\nrunner_type: orquesta\nname: test\nentry_point: workflows/test.yaml\n"
                }
            ]
        }
        """
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_POST_ACTION
            # self.headers.update({"x-auth-token": self.tokens.get("data")})
            data_dic = json.dumps(data_dic)
            res = requests.post(url, headers=self.headers, timeout=5, data=data_dic, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 201:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def update_workflow(self, data_dic):
        """修改工作流
        {
            "pack": "develop_deploy",
            "name": "test",
            "runner_type": "orquesta",
            "entry_point": "workflows/test.yaml",
            "metadata_file": "actions/test.meta.yaml",
            "enabled": true,
            "data_files": [
                {
                    "file_path": "workflows/test.yaml",
                    "content": "version: 1.0\ntasks:\n  # [384, 193]\n  task1:\n    action: opsany.get_info\n"
                },
                {
                    "file_path": "test.meta.yaml",
                    "content": "pack: develop_deploy\nenabled: true\nrunner_type: orquesta\nname: test\nentry_point: workflows/test.yaml\n"
                }
            ]
        }
        """
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            ref = data_dic.get("pack", "") + "." + data_dic.get("name", "")
            url = self.url + GET_PUT_DELETE_ACTION.format(ref_or_id=ref)
            # self.headers.update({"x-auth-token": self.tokens.get("data")})
            data_dic = json.dumps(data_dic)
            res = requests.put(url, headers=self.headers, timeout=5, data=data_dic, verify=False)

            res.encoding = 'utf-8'
            if res.status_code == 200:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def delete_workflow(self, ref_or_id):
        """删除工作流
        {
            "ref_or_id": "test"
        }
        """
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_PUT_DELETE_ACTION.format(ref_or_id=ref_or_id)
            res = requests.delete(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 204:
                return True, "success"
            if res.status_code == 404:
                return False, "数据不存在"
            else:
                return False, "操作失败"
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def run_workflow(self, data_dic=None):
        """新建执行，执行动作"""
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + EXECUTIONS_ACTION
            # self.headers.update({"x-auth-token": self.tokens.get("data")})
            data_dic = json.dumps(data_dic)
            res = requests.post(url, headers=self.headers, timeout=5, data=data_dic, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 201:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def get_workflow_execution_log(self, execution_id):
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_PUT_DELETE_EXECUTION.format(execution_id=execution_id)
            res = requests.get(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 200:
                return res.json()
            else:
                return res.json()
        except Exception as e:
            return {}

    def get_workflow_step_execution_log(self, execution_id):
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_PUT_DELETE_EXECUTION.format(execution_id=execution_id)
            res = requests.get(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            if res.status_code == 200:
                return True, res.json()
            else:
                return False, res.json()
        except Exception as e:
            return False, "服务异常({})".format(str(e))

    def workflow_execution_cancel(self, execution_id):
        try:
            status, message = self.st2_login()
            if not status:
                return False, message
            url = self.url + GET_PUT_DELETE_EXECUTION.format(execution_id=execution_id)
            res = requests.delete(url, headers=self.headers, timeout=5, verify=False)
            res.encoding = 'utf-8'
            print("res.status_code", res.status_code)
            print(res.content)
            if res.status_code == 200:
                return True, "success"
            if res.status_code == 404:
                return False, "数据不存在"
            else:
                return False, "操作失败"
        except Exception as e:
            return False, "服务异常({})".format(str(e))


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    """
    http://120.131.9.34

    """
    url = "https://120.131.9.229/"
    key = ""

    # os.environ.setdefault("BK_ENV", "production")     # 生产环境解注改行
    # os.environ.setdefault("BK_ENV", "testing")        # 开发环境解注改行
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import django

    django.setup()

    st2 = StackStormApi()
    data_dic = {
        "pack": "develop_deploy",
        "name": "test7",
        "description": "ceshi",
        "runner_type": "orquesta",
        "entry_point": "workflows/test7.yaml",
        "metadata_file": "actions/test7.meta.yaml",
        "enabled": True,
        "data_files": [
            {
                "file_path": "workflows/test7.yaml",
                "content": "version: 1.0\ntasks:\n  # [384, 193]\n  task1:\n    action: opsany.get_info\n"
            },
            {
                "file_path": "test7.meta.yaml",
                "content": "pack: develop_deploy\nenabled: true\nrunner_type: orquesta\nname: test7\nentry_point: workflows/test7.yaml\n"
            }
        ]
    }
    """
    (True, {'tags': [], 'uid': 'action:develop_deploy:test7', 'metadata_file': 'actions/test7.meta.yaml', 'name': 'test7', 'ref': 'develop_deploy.test7', 'description': 'ceshi', 'enabled': True, 'entry_point': 'workflows/test7.yaml', 'pack': 'develop_deploy', 'runner_type': 'orquesta', 'parameters': {}, 'output_schema': {}, 'notify': {}, 'id': '61c2e059a158fcde69f04f17'})
    """
    # print("get", st2.get_workflow("develop_deploy.test8"))
    # print("zzz", st2.create_workflow(data_dic))
    # print("zzz", st2.delete_workflow("develop_deploy.test8"))
    dic = {
        "action": "opsany_workflow.demo123",
    }
    print("ccc", st2.get_workflow_execution_log("6221aa7949134d82ac91c0b31"))
