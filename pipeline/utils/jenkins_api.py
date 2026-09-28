import base64
import urllib.parse
import json
import re

import jenkins, requests
from component.status_code import ErrorStatusCode
try:
    from pipeline.utils import constant
    from pipeline.utils.gitlab_api import GitLabApi
except:
    pass

DELETE_FOLDER = "%(folder_url)sjob/%(short_name)s/doDelete"
TO_JSON = "/pipeline-model-converter/toJson"
TO_JENKINS = "/pipeline-model-converter/toJenkinsfile"
BUILD_JOB = "%(folder_url)sjob/%(short_name)s/buildWithParameters"
RE_DESCRIPTION = "%(folder_url)sjob/%(short_name)s/description"
# JOB_BUILD_ABORT = "/job/{job_name}/{num}/input/2b45e2de44d2a6208e2f9a20687e5176/abort"
JOB_BUILD_PROCEED_EMPTY = "%(folder_url)sjob/%(short_name)s/{num}/input/70dec298c610c2ed5b1807c3bd8e529f/proceedEmpty"
JOB_BUILD_ABORT = "%(folder_url)sjob/%(short_name)s/{num}/input/C96c3a89e8559145209c2b792ef1cbbc/abort"
GET_LIST_CREDENTIALS = "credentials/store/system/domain/_/api/json?depth=1"
CREATE_CREDENTIALS = "credentials/store/system/domain/_/createCredentials"

UPDATE_TOKEN = "credentials/store/system/domain/_/credential/{oldId}/update"
UPDATE_CREDENTIALS = "credentials/store/system/domain/_/credential/{oldId}/updateSubmit"
DELETE_CREDENTIALS = "credentials/store/system/domain/_/credential/{credentialsId}/doDelete"

GENERATE_SECRET_TOKEN = "%(folder_url)sjob/%(short_name)s/descriptorByName/com.dabsquared.gitlabjenkins.GitLabPushTrigger/generateSecretToken"
GITLAB_HOOK = "http://git.opsany.cn/womaiyun/opsant-frontend/hooks/182"
MOVE_JOB = "job/{}/move/move"

# 查看指定构建历史中是否有待处理的人工确认步骤
JOB_BUILD_NEXT_PENDING_INPUT = "/job/{folder_name}/job/{job_name}/{num}/wfapi/nextPendingInputAction?_={timestamp}"
# 人工确认-继续
JOB_BUILD_PROCEED_EMPTY_V2 = "%(folder_url)sjob/%(short_name)s/{num}/input/{input_id}/proceedEmpty"
# 人工确认-终止
JOB_BUILD_ABORT_V2 = "%(folder_url)sjob/%(short_name)s/{num}/input/{input_id}/abort"
# 获取构建历史指定阶段
JOB_BUILD_STAGE = "/job/{folder_name}/job/{job_name}/wfapi/runs?fullStages=true&_={timestamp}"
# 获取指定构建记录完整日志
JOB_BUILD_FULL_INFO = "/job/{folder_name}/job/{job_name}/{num}/consoleText"
# JOB_BUILD_FULL_INFO = "/job/{folder_name}/job/{job_name}/{num}/consoleFull"


def flash_all_tool_status(request, tool_queryset):
    """刷新状态(jenkins, git, repository)"""
    error_count, success_count = 0, 0
    for tool_query in tool_queryset:
        tool_dic = tool_query.link_tool_dict()
        try:
            if tool_query.tool_type == "jenkins":
                jenkins_api = JenkinsApi(request, **tool_dic)
                status = jenkins_api.jenkins_status()
            elif tool_query.tool_type == "git":
                gitlab_api = GitLabApi(**tool_query.link_git_dict())
                status = gitlab_api.status()
            # if tool_query.tool_type == "repository":
            #     status = NexusApi(request, **tool_dic).status()
            else:
                status = False
        except Exception as e:
            print("flash_all_tool_status_error", e)
            status = False
        if status == True:
            tool_query.update(link_status=constant.TOOL_LINK_STATUS_SUCCESS)
            success_count += 1
        else:
            tool_query.update(link_status=constant.TOOL_LINK_STATUS_ERROR)
            error_count += 1
    return success_count, error_count


class JenkinsApi(object):
    def __init__(self, request=None, url=None, username=None, password=None, timeout=5):
        self.request = request
        self.url = url
        self.timeout = timeout
        self.username = username
        self.password = password
        self.server = jenkins.Jenkins(
            url=self.url,
            username=self.username,
            password=self.password,
            timeout=self.timeout)
        self.server._session.verify = False

    def jenkins_status(self):
        try:
            get_whoami = self.server.get_whoami()
            get_version = self.server.get_version()
            status = True
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "Unauthorized" in str(e):
                status = ErrorStatusCode.USER_OR_PASSWORD_ERROR, str(e)
            else:
                status = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            status = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            status = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
        except Exception as e:
            status = ErrorStatusCode.OPERATION_ERROR, str(e)
        return status

    # 获取全部文件夹（文件夹名称是应用唯一标识）
    def get_folders(self, folder_depth=0):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_jobs = self.server.get_all_jobs(folder_depth=folder_depth)
            data["status"] = 1
            folders_list = []
            for folder in all_jobs:
                jobs = []
                if folder.get("_class") == constant.FOLDER_CLASS:
                    for job in folder.get("jobs"):
                        if job.get("_class") == constant.JOB_CLASS:
                            jobs.append(job)
                folder["jobs"] = jobs
                folders_list.append(folder)
            data["data"] = folders_list
        except jenkins.JenkinsException as e:
            print("获取全部文件夹jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            # 503 Server Error: Service Unavailable for url: http://jenkins.hu27.cn/crumbIssuer/api/json
            # 502 Server Error: Bad Gateway for url
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取全部视图
    def get_views(self):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_views = self.server.get_views()
            data["status"] = 1
            data["data"] = all_views
        except jenkins.JenkinsException as e:
            print("获取全部视图jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取指定文件夹
    def get_folder_info(self, name):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_folders = self.server.get_job_info(name=name)
            data["status"] = 1
            data["data"] = all_folders
        except jenkins.JenkinsException as e:
            print("获取指定文件夹jenkins.JenkinsException", e)
            if "not exist" in str(e):
                data["message"] = ErrorStatusCode.FOLDER_NOT_FOUNT, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取指定流水线作业
    def get_job_info(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.get_job_info(name=name)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("获取指定流水线作业jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 新建文件夹（文件夹名称是应用唯一标识）
    def create_folder(self, name, ignore_failures=True):
        data = {"status": 0, "message": "success", "data": None}
        try:
            create_folder = self.server.create_folder(name, ignore_failures)
            data["status"] = 1
            data["data"] = "create success"
        except jenkins.JenkinsException as e:
            print("新建文件夹jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 删除文件夹
    def delete_folder(self, name):
        data = {"status": 0, "message": "success", "data": None}
        try:
            folder_url, short_name = self.server._get_job_folder(name)
            url = self.server._build_url(DELETE_FOLDER, locals())
            result = self.server.jenkins_request(requests.Request('POST', url, data={"Submit": "是"}))
            if result.status_code == 200:
                data["status"] = 1
                return data

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            print("删除文件夹jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取所有的流水线作业
    def get_all_jobs(self):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_jobs = self.server.get_all_jobs()
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("获取所有的流水线作业jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取指定文件夹下的流水线
    def get_jobs(self, view_name=None, folder_depth=0):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_jobs = self.server.get_jobs(view_name=view_name, folder_depth=folder_depth)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def job_exists(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.job_exists(name=name)
            if all_jobs:
                data["status"] = 1
                data["data"] = all_jobs
            else:
                data["message"] = "error"
                data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取指定构建历史详情
    def get_build_info(self, name, number: int, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            number = int(number)
        except Exception as e:
            data["message"] = ErrorStatusCode.MUST_INPUT_MESSAGE, str(e)

        try:
            build_info = self.server.get_build_info(name, number)
            data["status"] = 1
            data["data"] = build_info
        except jenkins.JenkinsException as e:
            print("获取指定构建历史详情jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.BUILD_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_build_console_output(self, name, number, folder_name=""):
        data = {"status": 0, "message": "success", "data": "..."}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.get_build_console_output(name, number)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.BUILD_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_plugins_info(self, name):
        data = {"status": 0, "message": "success", "data": None}
        try:
            plugin_info = self.server.get_plugin_info(name)
            data["status"] = 1
            data["data"] = plugin_info
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def create_job(self, name, config_xml, folder_name=""):
        # config_xml = constant.EMPTY_VIEW_CONFIG_XML.format(name)
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.create_job(name, config_xml)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("创建job--jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            print("Exception", str(e))
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def build_job(self, name, parameters=None, folder_name=""):
        # parameters = {"delay": "0sec"}
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            job_name = self.server.get_job_name(name)
            if job_name:
                build_job = self.server.build_job(name, parameters=parameters)
                # queue_item = self.server.cancel_queue(1769)
                # print("queue_item", queue_item)
                data["status"] = 1
                data["data"] = build_job
            else:
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, ""
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_queue_item(self, number):
        data = {"status": 0, "message": "success", "data": None}
        try:
            queue_item = self.server.get_queue_item(number)
            data["status"] = 1
            data["data"] = queue_item
        except jenkins.JenkinsException as e:
            # print("jenkins.JenkinsException", e)
            if "not exist" in str(e):
                data["message"] = ErrorStatusCode.MESSAGE_NOT_FIND, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_queue_info(self):
        data = {"status": 0, "message": "success", "data": None}
        try:
            queue_info = self.server.get_queue_info()
            data["status"] = 1
            data["data"] = queue_info
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        s = [{'_class': 'hudson.model.Queue$BuildableItem', 'actions': [], 'blocked': False, 'buildable': True,
              'id': 3366, 'inQueueSince': 1623755704093, 'params': '', 'stuck': False,
              'task': {'_class': 'org.jenkinsci.plugins.workflow.support.steps.ExecutorStepExecution$PlaceholderTask'},
              'url': 'queue/item/3366/', 'why': 'Waiting for next available executor',
              'buildableStartMilliseconds': 1623755704094, 'pending': False},
             {'_class': 'hudson.model.Queue$BuildableItem', 'actions': [], 'blocked': False, 'buildable': True,
              'id': 3364, 'inQueueSince': 1623755699321, 'params': '', 'stuck': False,
              'task': {'_class': 'org.jenkinsci.plugins.workflow.support.steps.ExecutorStepExecution$PlaceholderTask'},
              'url': 'queue/item/3364/', 'why': 'Waiting for next available executor',
              'buildableStartMilliseconds': 1623755699322, 'pending': False}]
        return data

    def stop_build(self, name, number, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            job_name = self.server.get_job_name(name)
            if job_name:
                stop_build = self.server.stop_build(name, number)
                data["status"] = 1
                data["data"] = stop_build
            else:
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, ""
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.BUILD_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 删除构建历史
    def delete_build(self, name, number, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            job_name = self.server.get_job_name(name)
            if job_name:
                # delete_build = self.server.delete_build(name, number)
                folder_url, short_name = self.server._get_job_folder(name)
                delete_build = self.server.jenkins_open(requests.Request('POST',
                                                        self.server._build_url(jenkins.DELETE_BUILD, locals())))

                data["status"] = 1
                data["data"] = "delete success"
            else:
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, ""
        except jenkins.JenkinsException as e:
            print("删除构建历史jenkins.JenkinsException", e)
            if "does not exist" in str(e):
                data["message"] = ErrorStatusCode.BUILD_NOT_EXISTED, str(e)
                data["status"] = 1
            elif "not be found" in str(e):
                data["message"] = ErrorStatusCode.BUILD_NOT_EXISTED, str(e)
                data["status"] = 1
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_running_builds(self):
        data = {"status": 0, "message": "success", "data": None}
        try:
            delete_build = self.server.get_running_builds()
            data["status"] = 1
            data["data"] = delete_build
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def desc_job(self, name, description, folder_name=""):
        # "{optionalFolderPath}job/{name}/description"
        # RE_REDESCRIPTION = "/job/{}/description".format(name)
        name = folder_name + "/" + name
        the_data = {
            "description": description
        }
        data = {"status": 0, "message": "success", "data": None}
        try:
            job_name = self.server.get_job_name(name)
            if job_name:
                folder_url, short_name = self.server._get_job_folder(name)
                url = self.server._build_url(RE_DESCRIPTION, locals())
                result = self.server.jenkins_request(requests.Request('POST', url, data=the_data))
                data["status"] = 1
            else:
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, ""

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_job_config(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            job_config = self.server.get_job_config(name)
            data["status"] = 1
            data["data"] = job_config
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "not be found" in str(e):
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_job_config_old(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        try:
            job_config = self.server.get_job_config(name)
            data["status"] = 1
            data["data"] = job_config
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "not be found" in str(e):
                data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def reconfig_job(self, name, config_xml, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.reconfig_job(name, config_xml)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)

            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def rename_job(self, from_name, to_name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        from_name = folder_name + "/" + from_name
        to_name = folder_name + "/" + to_name
        try:
            all_jobs = self.server.rename_job(from_name, to_name)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
            data["status"] = 1
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def delete_job(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.delete_job(name)
            data["status"] = 1
            data["data"] = all_jobs
        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
            data["status"] = 1
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def to_json(self, jenkins_file):
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"
        the_data = {
            "jenkinsfile": jenkins_file
        }
        data = {"status": 0, "message": "success", "data": None}
        try:
            url = self.server._build_url(TO_JSON, locals())
            result = self.server.jenkins_request(requests.Request('POST', url, data=the_data))

            result = result.json()

            if result.get("status") == "ok":
                # data - result - failure or success
                if result.get("data").get("result") == "success":
                    data["status"] = 1
                    data["data"] = result.get("data").get("json")
                else:
                    data["message"] = ErrorStatusCode.SYNTAX_ERROR, result.get("data").get("errors")
                    data["data"] = result.get("data").get("errors")

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.REQUEST_API_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def to_jenkins_file(self, json_file):
        # TO_JENKINS = "/pipeline-model-converter/toJenkinsfile"
        the_data = {
            "json": json_file
        }
        data = {"status": 0, "message": "success", "data": None}
        try:
            url = self.server._build_url(TO_JENKINS, locals())
            result = self.server.jenkins_request(requests.Request('POST', url, data=the_data))
            # try:
            result = result.json()
            # print("to_json", result)
            # except Exception as e:
            #     raise str(e)
            if result.get("status") == "ok":
                # data - result - failure or success
                if result.get("data").get("result") == "success":
                    data["status"] = 1
                    data["data"] = result.get("data").get("jenkinsfile")
                else:
                    data["message"] = ErrorStatusCode.SYNTAX_ERROR, result.get("data").get("errors")
                    data["data"] = result.get("data").get("errors")

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.REQUEST_API_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def check_jenkinsfile_syntax(self, jenkins_file):
        data = {"status": 0, "message": "success", "data": None}
        try:
            all_jobs = self.server.check_jenkinsfile_syntax(jenkins_file)
            if not all_jobs:
                data["status"] = 1
                data["data"] = all_jobs
            else:
                data["message"] = ErrorStatusCode.SYNTAX_ERROR, all_jobs
        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def build_proceed_empty_old(self, job_name, num, folder_name=""):
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"

        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            folder_url, short_name = self.server._get_job_folder(job_name)
            url = self.server._build_url(JOB_BUILD_PROCEED_EMPTY.format(num=num), locals())
            result = self.server.jenkins_request(requests.Request('POST', url, data={}))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.JOB_NOT_FOUNT, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def build_abort_old(self, job_name, num, folder_name=""):
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"

        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            folder_url, short_name = self.server._get_job_folder(job_name)
            url = self.server._build_url(JOB_BUILD_ABORT.format(num=num), locals())
            result = self.server.jenkins_request(requests.Request('POST', url))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_promotions(self, job_name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            build_job = self.server.get_promotions(job_name)
            data["status"] = 1
            data["data"] = build_job
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "already exists" in str(e):
                data["message"] = ErrorStatusCode.JOB_NAME_HAS_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def get_credentials_list(self):
        """获取凭据列表"""
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"

        data = {"status": 0, "message": "success", "data": None}
        try:
            url = self.server._build_url(GET_LIST_CREDENTIALS, locals())
            result = self.server.jenkins_request(requests.Request('GET', url))

            result_test = result.json()
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def create_credentials(self, params, type):
        """创建凭据列表"""
        credentials_id = params.get("credentials_id")
        data = {"status": 0, "message": "success", "data": None}
        try:
            if type in [0, 2, 4, 6]:
                json_data = self._create_credentials(type, params)
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"
                return data
            the_data = {"json": json.dumps(json_data)}

            credentials_list_result = self.get_credentials_list()
            if credentials_list_result.get("status"):
                credentials_list = list()
                for credentials in credentials_list_result.get("data", {}).get("credentials"):
                    credentials_list.append(credentials.get("id"))
                if credentials_id and credentials_id in credentials_list:
                    data["message"] = ErrorStatusCode.JENKINS_CREDENTIALS_HAS_EXISTED, "error"
                else:
                    create_url = self.server._build_url(CREATE_CREDENTIALS, locals())
                    result = self.server.jenkins_request(requests.Request('POST', create_url, data=the_data))

                    result_test = result.text
                    print("result", result.status_code)
                    data["status"] = 1
                    data["data"] = "success"
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", str(e)[: 100] + "-------------")
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)[:100]
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def _create_credentials(self, type, params):
        if type == 0:
            return {"": str(type),
                    "credentials":
                        {"scope": "GLOBAL",
                         "username": params.get("username"),
                         "password": params.get("password"),
                         "$redact": "password",
                         "id": params.get("credentials_id", ""),
                         "description": params.get("description"),
                         "stapler-class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl",
                         "$class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"}}
        elif type == 2:
            return {"": str(type),
                    "credentials":
                        {"scope": "GLOBAL",
                         "apiToken": params.get("apiToken"),
                         "$redact": "apiToken",
                         "id": params.get("credentials_id", ""),
                         "description": params.get("description"),
                         "stapler-class": "com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl",
                         "$class": "com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl"}}
        elif type == 4:
            return {"": str(type),
                    "credentials":
                        {"scope": "GLOBAL",
                         "username": params.get("username"),
                         "privateKeySource": {
                             "value": "0",
                             "privateKey": params.get("privateKey"),
                             "stapler-class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey$DirectEntryPrivateKeySource",
                             "$class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey$DirectEntryPrivateKeySource"
                         },
                         "privateKey": params.get("privateKey"),
                         "passphrase": params.get("passphrase"),
                         "$redact": "passphrase",
                         "id": params.get("credentials_id", ""),
                         "description": params.get("description"),
                         "stapler-class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey",
                         "$class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey"}}
        elif type == 6:
            return {"": str(type),
                    "credentials":
                        {"scope": "GLOBAL",
                         "secret": params.get("secret"),
                         "$redact": "secret",
                         "id": params.get("credentials_id", ""),
                         "description": params.get("description"),
                         "stapler-class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl",
                         "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}

    def update_credentials(self, credentials_id, params, type):
        """获取凭据列表"""
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"

        data = {"status": 0, "message": "success", "data": None}
        try:
            if type == 0:
                json_data = {
                    "scope": "GLOBAL",
                    "username": params.get("username", ""),
                    "password": params.get("password", ""),
                    "$redact": "password",
                    "id": params.get("credentials_id", ""),
                    "description": params.get("description", ""),
                    "stapler-class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"}
            elif type == 2:
                json_data = {
                    "scope": "GLOBAL",
                    "apiToken": params.get("apiToken", ""),
                    "$redact": "apiToken",
                    "id": params.get("credentials_id", ""),
                    "description": params.get("description", ""),
                    "stapler-class": "com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl",
                    "$class": "com.dabsquared.gitlabjenkins.connection.GitLabApiTokenImpl"}
            elif type == 4:
                json_data = {
                    "scope": "GLOBAL",
                    "username": params.get("username", ""),
                    "privateKeySource": {
                        "value": "0",
                        "privateKey": params.get("privateKey", ""),
                        "stapler-class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey$DirectEntryPrivateKeySource",
                        "$class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey$DirectEntryPrivateKeySource"
                    },
                    "passphrase": params.get("passphrase", ""),
                    "$redact": "passphrase",
                    "id": params.get("credentials_id", ""),
                    "description": params.get("description", ""),
                    "stapler-class": "com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey"}
            elif type == 6:
                json_data = {
                    "scope": "GLOBAL",
                    "secret": params.get("secret", ""),
                    "$redact": "secret",
                    "id": params.get("credentials_id", ""),
                    "description": params.get("description", ""),
                    "stapler-class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl",
                    "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
                }

            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"
                return data

            url = self.server._build_url(UPDATE_CREDENTIALS.format(oldId=params.get("credentials_id", "")), locals())
            the_data = {"json": json.dumps(json_data)}
            result = self.server.jenkins_request(requests.Request('POST', url, data=the_data))

            result_test = result.text

            data["status"] = 1
            data["data"] = "success"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        # except Exception as e:
        #     data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def delete_credentials(self, credentialsId):
        """获取凭据列表"""
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"

        data = {"status": 0, "message": "success", "data": None}
        try:
            url = self.server._build_url(DELETE_CREDENTIALS.format(credentialsId=credentialsId), locals())
            result = self.server.jenkins_request(requests.Request('POST', url))

            result_test = result.text

            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["status"] = 1
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def move_job_to_folder(self, job_name, folder_name=""):
        """移动流水线"""

        data = {"status": 0, "message": "success", "data": None}
        try:
            dic = {"destination": "/" + folder_name, "Submit": "移动"}
            create_url = self.url + MOVE_JOB.format(job_name)
            result = self.server.jenkins_request(requests.Request('POST', create_url, params=dic))
            result_test = result.text
            data["status"] = 1
            data["data"] = result_test

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", str(e)[: 100] + "-------------")
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)[:100]
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        # except Exception as e:
        #     data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def delete_view(self, name):
        data = {"status": 0, "message": "success", "data": None}
        try:
            delete_view = self.server.delete_view(name)
            data["status"] = 1
            data["data"] = "delete success"
            data["data"] = delete_view
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            if "not be found" in str(e):
                data["message"] = ErrorStatusCode.MESSAGE_NOT_FIND, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def build_job_with_parameters(self, name, parameters=None, token=None, folder_name=""):
        """带参数构建"""

        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            the_data = json.dumps({"parameters": parameters})
            folder_url, short_name = self.server._get_job_folder(name)
            create_url = self.server._build_url(BUILD_JOB, locals())
            result = self.server.jenkins_request(requests.Request('POST', create_url, params=parameters))
            result_test = result.text

            data["status"] = 1
            data["data"] = result_test

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", str(e)[: 100] + "-------------")
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)[:100]
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        # except Exception as e:
        #     data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    def generate_secret_token(self, job_name, folder_name=""):
        """获取TOKEN"""

        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            folder_url, short_name = self.server._get_job_folder(job_name)
            url = self.server._build_url(GENERATE_SECRET_TOKEN, locals())
            result = self.server.jenkins_request(requests.Request('POST', url))

            if result.status_code == 200:
                headers_script = result.headers.get("script")

                secret_token_list = re.findall(r"\.value='(.*)'", headers_script)
                if secret_token_list:
                    secret_token = secret_token_list[0]
                    data["status"] = 1
                    data["data"] = secret_token
                else:
                    data["message"] = ErrorStatusCode.OPERATION_ERROR, "re error"
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, "error"

        except jenkins.NotFoundException as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except jenkins.JenkinsException as e:
            print("jenkins.JenkinsException", e)
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError", e)
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError", e)
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = ErrorStatusCode.JENKINS_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.JENKINS_HTTP_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        return data

    # 获取构建历史详情-阶段
    def get_build_stage_info(self, name, number: int, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        try:
            number = int(number)
        except Exception as e:
            data["message"] = str(e)

        try:
            import time
            int_timestamp = int((time.time()) * 1000)
            url = self.server._build_url(JOB_BUILD_STAGE.format(
                folder_name=folder_name, job_name=name, num=number, timestamp=int_timestamp))

            build_stage_info = self.server.jenkins_request(requests.Request("GET", url=url))
            # 获取的是所有的构建记录
            result_test = build_stage_info.json()
            # 取出指定构建记录
            result_end_data = next((item for item in result_test if item["id"] == str(number)), None)

            data["status"] = 1
            data["data"] = result_end_data
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 获取指定构建历史详情-阶段-日志
    def get_build_stage_log_info(self, execution_log_url):
        data = {"status": 0, "message": "success", "data": None}

        try:
            url = self.server._build_url(execution_log_url)

            build_stage_info = self.server.jenkins_request(requests.Request("GET", url=url))
            result_test = build_stage_info.json()

            data["status"] = 1
            data["data"] = result_test
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 获取指定构建记录完整日志
    def get_build_full_log_info(self, folder_name="", job_name="", num=None):
        data = {"status": 0, "message": "success", "data": None}
        try:
            job_build_full_url = JOB_BUILD_FULL_INFO.format(folder_name=folder_name, job_name=job_name, num=num)
            url = self.server._build_url(job_build_full_url)

            build_stage_info = self.server.jenkins_request(requests.Request("GET", url=url))
            result_test = build_stage_info.text
            data["status"] = 1
            data["data"] = result_test
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            data["message"] = str(e)
        except Exception as e:
            print("eeeeeeeeeeeeeeeeeee", str(e))
            data["message"] = str(e)
        return data

    # 获取指定阶段日志（人工确认）中的继续和终止地址
    def get_build_stage_log_proceed_and_abort_info(self, execution_log_url):
        data = {"status": 0, "message": "success", "data": None}

        try:
            url = self.server._build_url(execution_log_url)

            build_stage_info = self.server.jenkins_request(requests.Request("GET", url=url))
            result_test = build_stage_info.json()

            if "onclick" and "atob" in result_test["text"]:
                encoded_urls = re.findall(r"atob\('([^']+)'\)", result_test['text'])
                # 解码所有匹配到的 Base64 编码的 URL
                decoded_urls = []
                for encoded_url in encoded_urls:
                    decoded_url = base64.b64decode(encoded_url).decode('utf-8')  # Base64 解码
                    decoded_url = urllib.parse.unquote(decoded_url)  # URL 解码
                    decoded_urls.append(decoded_url)
                decoded_and_unquoted_urls = decoded_urls
            else:
                # 提取 text 中的所有 data-encoded-url 属性值
                encoded_urls = re.findall(r"data-encoded-url='([^']+)'", result_test['text'])
                # 解码所有的 URL，并存入列表
                decoded_urls = [base64.b64decode(encoded_url).decode('utf-8') for encoded_url in encoded_urls]
                # 对解码后的 URL 进行 URL 解码
                decoded_and_unquoted_urls = [urllib.parse.unquote(url) for url in decoded_urls]
            data["status"] = 1
            data["data"] = decoded_and_unquoted_urls
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 获取指定构建历史详情-阶段-日志-input_id（如果是等待人工确认的步骤，就返回这个人工确认的input_id）
    def get_build_stage_log_input_id_info(self, execution_log_url):
        data = {"status": 0, "message": "success", "data": None}

        try:
            url = self.server._build_url(execution_log_url)

            build_stage_info = self.server.jenkins_request(requests.Request("GET", url=url))
            result_test = build_stage_info.json()

            decoded_url = None
            if "onclick" and "atob" in result_test["text"]:
                encoded_urls = re.findall(r"atob\('([^']+)'\)", result_test['text'])
                # 解码所有匹配到的 Base64 编码的 URL
                decoded_urls = []
                for encoded_url in encoded_urls:
                    decoded_url = base64.b64decode(encoded_url).decode('utf-8')  # Base64 解码
                    decoded_url = urllib.parse.unquote(decoded_url)  # URL 解码
                    decoded_urls.append(decoded_url)
                if decoded_urls:
                    decoded_url = decoded_urls[0]
            else:
                encoded_url = re.search(r"data-encoded-url='([^']+)'", result_test['text'])
                if encoded_url:
                    # 解码 Base64 编码的 URL
                    decoded_url = base64.b64decode(encoded_url.group(1)).decode('utf-8')
                    # URL 解码
                    decoded_url = urllib.parse.unquote(decoded_url)

            input_id = None
            if decoded_url:
                match = re.search(r"input/([^/]+)", decoded_url)
                if match:
                    # 输出匹配的结果
                    input_id = match.group(1)

            data["status"] = 1
            data["data"] = input_id
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 人工确认-继续
    def build_proceed_empty(self, job_name, num, folder_name, input_id):
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"
        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            folder_url, short_name = self.server._get_job_folder(job_name)
            url = self.server._build_url(JOB_BUILD_PROCEED_EMPTY_V2.format(num=num, input_id=input_id), locals())
            result = self.server.jenkins_request(requests.Request('POST', url, data={}))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = "error"

        except jenkins.NotFoundException as e:
            data["message"] = str(e)
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = str(e)
            else:
                data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 人工确认-继续-取日志中的地址执行
    def build_proceed_empty_v2(self, proceed_url, tool_url=None):
        data = {"status": 0, "message": "success", "data": None}
        try:
            try:
                if tool_url and not tool_url.endswith("/"):
                    tool_url += "/"
                tool_url += "crumbIssuer/api/json"
            except Exception as e:
                tool_url = None
            crumb = None
            try:
                if tool_url:
                    # 获取 Jenkins Crumb
                    crumb_response = self.server.jenkins_request(requests.Request('GET', tool_url))
                    if crumb_response.status_code == 200:
                        crumb_data = crumb_response.json()
                        crumb = crumb_data['crumb']
                    else:
                        print("继续人工确认-获取Crumb失败")
            except Exception as e:
                crumb = None
                print("继续人工确认-获取Crumb失败，Error：", str(e))

            headers = {
                'Jenkins-Crumb': crumb  # 添加 Crumb 到请求头
            }
            if crumb:
                result = self.server.jenkins_request(requests.Request('POST', proceed_url, headers=headers, data={}))
            else:
                result = self.server.jenkins_request(requests.Request('POST', proceed_url, data={}))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = "error"

        except jenkins.NotFoundException as e:
            data["message"] = str(e)
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = str(e)
            else:
                data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 人工确认-终止
    def build_abort(self, job_name, num, folder_name, input_id):
        # to_json_url = os.path.join(self.url, "/pipeline-model-converter/toJson/")
        # TO_JSON = "/pipeline-model-converter/toJson"
        data = {"status": 0, "message": "success", "data": None}
        job_name = folder_name + "/" + job_name
        try:
            folder_url, short_name = self.server._get_job_folder(job_name)
            url = self.server._build_url(JOB_BUILD_ABORT_V2.format(num=num, input_id=input_id), locals())
            result = self.server.jenkins_request(requests.Request('POST', url))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = "error"

        except jenkins.NotFoundException as e:
            data["message"] = str(e)
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = str(e)
            else:
                data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 人工确认-终止-取日志中的地址执行
    def build_abort_v2(self, abort_url, tool_url=None):
        data = {"status": 0, "message": "success", "data": None}
        try:
            try:
                if tool_url and not tool_url.endswith("/"):
                    tool_url += "/"
                tool_url += "crumbIssuer/api/json"
            except Exception as e:
                tool_url = None
            crumb = None
            try:
                if tool_url:
                    # 获取 Jenkins Crumb
                    crumb_response = self.server.jenkins_request(requests.Request('GET', tool_url))
                    if crumb_response.status_code == 200:
                        crumb_data = crumb_response.json()
                        crumb = crumb_data['crumb']
                    else:
                        print("终止人工确认-获取Crumb失败")
            except Exception as e:
                crumb = None
                print("终止人工确认-获取Crumb失败，Error：", str(e))

            headers = {
                'Jenkins-Crumb': crumb  # 添加 Crumb 到请求头
            }
            if crumb:
                result = self.server.jenkins_request(requests.Request('POST', abort_url, headers=headers, data={}))
            else:
                result = self.server.jenkins_request(requests.Request('POST', abort_url, data={}))

            result_test = result.text
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test
            else:
                data["message"] = "error"

        except jenkins.NotFoundException as e:
            data["message"] = str(e)
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except requests.exceptions.ConnectionError as e:
            data["message"] = str(e)
        except requests.exceptions.HTTPError as e:
            if "502 Server Error: Bad Gateway for url" in str(e):
                data["message"] = str(e)
            else:
                data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 获取指定流水线最新构建历史
    def get_job_newest_build_number(self, name, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            all_jobs = self.server.get_job_info(name=name)
            build_list = all_jobs.get("builds", [])
            data["status"] = 1
            data["data"] = build_list[0].get("number") if build_list else None
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 获取指定构建历史的时间戳timestamp
    def get_build_number_timestamp(self, name, number: int, folder_name=""):
        data = {"status": 0, "message": "success", "data": None}
        name = folder_name + "/" + name
        try:
            number = int(number)
        except Exception as e:
            data["message"] = str(e)

        try:
            build_info = self.server.get_build_info(name, number)
            data["status"] = 1
            data["data"] = build_info.get("timestamp")
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data

    # 查询指定构建历史中是否存在待处理的人工确认步骤-获取请求id
    def get_build_pending_input_id(self, folder_name, job_name, num):
        data = {"status": 0, "message": "success", "data": None}
        try:
            # res = self.get_build_number_timestamp(job_name, num, folder_name)
            # timestamp = res.get("data")
            import time
            int_timestamp = int((time.time()) * 1000)
            url = self.server._build_url(JOB_BUILD_NEXT_PENDING_INPUT.format(
                folder_name=folder_name, job_name=job_name, num=num, timestamp=int_timestamp), locals())
            result = self.server.jenkins_request(requests.Request('GET', url))

            result_test = result.text
            try:
                if isinstance(result_test, str):
                    # 安全：Jenkins 返回 JSON 字符串，用 json.loads 解析，杜绝 eval 注入
                    result_test = json.loads(result_test)
            except Exception as e:
                result_test = {}
            if result.status_code == 200:
                data["status"] = 1
                data["data"] = result_test.get("id")
            else:
                data["message"] = "error"

        except jenkins.NotFoundException as e:
            data["message"] = str(e)
        except jenkins.JenkinsException as e:
            data["message"] = str(e)
        except Exception as e:
            data["message"] = str(e)
        return data


def git_status(tool_dict):
    data = {"status": 0, "message": "success", "data": None}
    status = False
    if not status:
        data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str("error")
        return data
    else:
        data["status"] = 1
        data["data"] = "success"
        return status


def repository_status(tool_dict):
    print(tool_dict)
    status = True
    return status


if __name__ == '__main__':
    pass
