import json
import time

import xmltodict
from django.http import JsonResponse
import requests
from requests.auth import HTTPBasicAuth

from component import return_message
from component.base_views import BaseObject
from component.esb_api import EsbApi
from pipeline.utils import constant
from pipeline.celery_task import celery_build_num_and_run_username, sync_application_pipelines, refresh_pipeline_jobs
from component.libs import GetUserInfo
from component.status_code import success, SuccessStatusCode, error, ErrorStatusCode
from pipeline.utils.filter_data import filter_build_info_data
from pipeline.utils.gitlab_api import GitLabApi
from pipeline.utils.jenkins_api import JenkinsApi
from pipeline.utils.libs import xml_dict, check_variable_name, extract_input_arguments, extract_input_arguments_2
from pipeline.models import ApplicationUserRoleModel, ApplicationJenkinsModel, ApplicationJenkinsJobsModel, \
    ToolsModel, ApplicationModel, JenkinsJobTagsModel, ApplicationJenkinsJobBuildModel, OperationLogModel, \
    JenkinsCredentialsModel, UserJenkinsCredentialsModel, BusinessModel, JenkinsJobOverAllViewModel, \
    JenkinsOverallViewUserModel, DevOpsPipelineGroupModel, UserInfo, JobBuildNumberScriptModel, \
    JobBuildInputMessageModel, RefreshJobModel, SyncBuildingJobModel
from pipeline.utils.oprtation_audit import operation_audit_create_build_operation_log
from pipeline.utils.sync_data import jenkins_sync_credentials


class JenkinsJob(BaseObject):
    # 弃用
    def get_job_v2(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))
        data = request.GET.dict()
        list_type = data.get("list_type", "all")
        search_type = data.get("search_type", None)
        search_data = data.get("search_data", None)
        page = int(data.get("current", 1))
        per_page = int(data.get("pageSize", 10))
        code = data.get("code", None)
        business_code = data.get("business_code", None)
        all_data = data.get("all_data", False)

        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        if user_query.role not in [1]:
            if not ApplicationUserRoleModel.fetch_one(user_info=user_query, application=application_query):
                return JsonResponse(error(ErrorStatusCode.USER_NOT_APPLICATION_POWER, language=self.ops_language()))
        application_name = application_query.get_model_code_name()

        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query,
                                                        jenkins_view_name=application_name)
        dic = {}
        if list_type == "tags":
            tags_queryset = JenkinsJobTagsModel.fetch_all(user_info=user_query)
            app_list = []
            for tags_query in tags_queryset:
                try:
                    app_list.append(tags_query.jenkins_job.code)
                except Exception:
                    res = tags_query.delete()
            dic["code__in"] = app_list
        if search_type and search_data:
            dic[search_type + "__icontains"] = search_data

        if business_code:
            business_query = BusinessModel.fetch_one(code=business_code)
            view_queryset = []  # 存放所有的应用-jenkins view（管理员）
            application_queryset = ApplicationModel.fetch_all(business=business_query)
            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(), "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_queryset.append(view_query)
            dic["view__in"] = view_queryset

            normal_user_view_queryset = []  # 存放普通用户所有的应用-jenkins view
            if user_query.role not in [1]:
                for application_query_ in application_queryset:
                    app_user_role_queryset = ApplicationUserRoleModel.fetch_all(user_info=user_query,
                                                                                application=application_query_)
                    if app_user_role_queryset:
                        view_queryset_ = [view_query_.application for view_query_ in app_user_role_queryset]
                        normal_user_view_queryset.append(view_queryset_)
                dic["view__in"] = normal_user_view_queryset

            current_page, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic)
            jobs_list = [job_query.to_tags_dict_v2(user_query) for job_query in current_page]
            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        if all_data:
            if user_query.role not in [1]:
                all_normal_user_view_queryset = []  # 存放普通用户所有的应用-jenkins view
                all_application_queryset = ApplicationModel.fetch_all()
                for application_query in all_application_queryset:
                    view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                    if not view_query:
                        dt = {"jenkins_view_name": application_query.get_model_code_name(),
                              "application": application_query}
                        view_query = ApplicationJenkinsModel.create(**dt)
                    all_normal_user_view_queryset.append(view_query)
                dic["view__in"] = all_normal_user_view_queryset
            current_page, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic)
            jobs_list = [job_query.to_tags_dict_v2(user_query) for job_query in current_page]
            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        dic["view"] = view_query
        jobs_queryset, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic)

        jobs_list = [job_query.to_tags_dict_v2(user_query) for job_query in jobs_queryset]

        end_data = {
            "current": page,
            "pageSize": per_page,
            "total": total,
            "data": jobs_list
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

    def get_job_name_and_discard_strategy(self, request):
        kwargs = request.GET.dict()
        job_name = kwargs.get("job_name", None)

        code = kwargs.get("code", None)

        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        view_name = application.get_model_code_name()
        job_info_result = jenkins_api.get_job_info(job_name, folder_name=view_name)
        config_result = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if not job_info_result.get("status"):
            return JsonResponse(error(*job_info_result.get("message"), language=self.ops_language()))
        if not config_result.get("status"):
            return JsonResponse(error(*config_result.get("message"), language=self.ops_language()))

        config_xml = config_result.get("data", "")
        old_config = xml_dict(xml_config=config_xml)
        build_discard_dict = self._get_build_discard(old_config=old_config)
        data = {
            "name": job_info_result.get("data", {}).get("name"),
            "description": job_info_result.get("data", {}).get("description"),
        }
        if build_discard_dict:
            data["build_discard"] = {
                "strategy": "LogRotator",
                "daysToKeep": build_discard_dict.get("daysToKeep", ""),
                "numToKeep": build_discard_dict.get("numToKeep", "")
            }
            if build_discard_dict.get("daysToKeep", -1) == "-1":
                data["build_discard"]["daysToKeep"] = ""
            if build_discard_dict.get("numToKeep", -1) == "-1":
                data["build_discard"]["numToKeep"] = ""
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

    def update_job_name_and__discard_strategy(self, request):
        post_data = json.loads(request.body)
        name = post_data.get("name")
        rename = post_data.get("rename", None)
        description = post_data.get("description", "")
        build_discard = post_data.get("build_discard", {})

        code = post_data.get("code", None)
        application = ApplicationModel.fetch_one(code=code)
        view_name = application.get_model_code_name()
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        if not all([rename, name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        job = ApplicationJenkinsJobsModel.fetch_one(job_name=name)

        # 判断权限-编辑-基础信息
        if user_query.role != 1:
            status = job.is_auth_update(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 修改基础信息前

        config_result = jenkins_api.get_job_config(name, folder_name=view_name)
        if not config_result.get("status"):
            return JsonResponse(error(*config_result.get("message"), language=self.ops_language()))

        config_xml = config_result.get("data", "")
        old_config = xml_dict(xml_config=config_xml)
        build_discard_dict = self._get_build_discard(old_config=old_config)
        old_data = {
            "name": name,
            "description": description,
        }
        if build_discard_dict:
            old_data["build_discard"] = {
                "strategy": "LogRotator",
                "daysToKeep": build_discard_dict.get("daysToKeep", ""),
                "numToKeep": build_discard_dict.get("numToKeep", "")
            }
            if build_discard_dict.get("daysToKeep", -1) == "-1":
                old_data["build_discard"]["daysToKeep"] = ""
            if build_discard_dict.get("numToKeep", -1) == "-1":
                old_data["build_discard"]["numToKeep"] = ""

        before_change_dict = old_data

        if rename:
            if name != rename:
                print("name != rename", name, rename)
                # name = parse_url_format(name)
                # rename = parse_url_format(rename)
                result_name = jenkins_api.rename_job(name, rename, folder_name=view_name)
                print("result_name", result_name)

                if not result_name.get("status"):
                    return JsonResponse(error(*result_name.get("message"), language=self.ops_language()))
            result_desc = jenkins_api.desc_job(rename, description, folder_name=view_name)
            print("result_desc", result_desc)
            if not result_desc.get("status"):
                return JsonResponse(error(*result_desc.get("message"), language=self.ops_language()))
            config_result = jenkins_api.get_job_config(rename, folder_name=view_name)
            if not config_result.get("status"):
                return JsonResponse(error(*config_result.get("message"), language=self.ops_language()))

            old_config_xml = config_result.get("data", "")
            new_config_xml = self._reconfig_build_discard(old_config_xml, build_discard)
            res = jenkins_api.reconfig_job(rename, new_config_xml, folder_name=view_name)
            if not res.get("status"):
                return JsonResponse(error(*result_desc.get("message"), language=self.ops_language()))

            if job:
                job.update(job_name=rename, description=description)

            # 修改基础信息后
            config_result_new = jenkins_api.get_job_config(rename, folder_name=view_name)
            if not config_result_new.get("status"):
                return JsonResponse(error(*config_result_new.get("message"), language=self.ops_language()))
            config_xml_new = config_result_new.get("data", "")
            new_config = xml_dict(xml_config=config_xml_new)
            build_discard_dict_new = self._get_build_discard(old_config=new_config)
            new_data = {
                "name": rename,
                "description": description
            }
            if build_discard_dict_new:
                new_data["build_discard"] = {
                    "strategy": "LogRotator",
                    "daysToKeep": build_discard_dict_new.get("daysToKeep", ""),
                    "numToKeep": build_discard_dict_new.get("numToKeep", "")
                }
                if build_discard_dict_new.get("daysToKeep", -1) == "-1":
                    if not old_data.get("build_discard"):
                        old_data["build_discard"] = {}
                    old_data["build_discard"]["daysToKeep"] = ""
                if build_discard_dict_new.get("numToKeep", -1) == "-1":
                    if not old_data.get("build_discard"):
                        old_data["build_discard"] = {}
                    old_data["build_discard"]["numToKeep"] = ""

            after_change_dict = new_data

            job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=rename)

            # 编辑基础配置操作审计
            operation_audit_create_build_operation_log(user_query, job_query, 3, 3, "编辑流水线基础信息", before_change_dict,
                                                       after_change_dict)

            return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, language=self.ops_language()))

    def get_description(self, request):
        kwargs = request.GET.dict()
        job_name = kwargs.get("job_name", None)

        code = kwargs.get("code", None)

        if not code or not ApplicationModel.fetch_one(code=code):
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name
        result = jenkins_api.get_job_info(job_name, folder_name=view_name)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        data = {
            "name": result.get("data", {}).get("name"),
            "description": result.get("data", {}).get("description")
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

    def update_description(self, request):
        post_data = json.loads(request.body)
        name = post_data.get("name")

        code = post_data.get("code", None)

        if not code or not ApplicationModel.fetch_one(code=code):
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        description = post_data.get("description", "")
        if not all([name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name
        result = jenkins_api.desc_job(name, description, folder_name=view_name)
        if result.get("status"):
            return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, language=self.ops_language()))
        return JsonResponse(error(*result.get("message"), language=self.ops_language()))

    def create_job(self, request):
        post_data = json.loads(request.body)
        code = post_data.get("code", None)
        name = post_data.get("name")
        description = post_data.get("description", "")
        config_xml = post_data.get("config_xml", "")
        pipeline_group_code = post_data.get("pipeline_group_code", None)  # 应用视图code
        overall_view_code = post_data.get("overall_view_code", None)  # 全局视图code
        # 暂时用replace将&&替换为&amp;&amp;
        if config_xml:
            config_xml = config_xml.replace("&&", "&amp;&amp;")
        if not all([code, name, config_xml]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        empty_config = constant.CREATE_JOB_EMPTY_CONFIG

        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 新建文件夹，关联应用
        application_jenkins_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not application_jenkins_query:
            application_name = application_query.get_model_code_name()

            dt = {"application": application_query, "jenkins_view_name": application_name}
            application_jenkins_query = ApplicationJenkinsModel.create(**dt)
        else:
            application_name = application_jenkins_query.jenkins_view_name

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        # 连接Jenkins
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        status, message = self._check_required_plugin(jenkins_api)
        if not status:
            messages = "Jenkins需要依赖插件：" + ", ".join(message) + ", 请前往Jenkins插件管理安装相关插件"
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, custom_message=messages,
                                      language=self.ops_language()))
        else:
            plugin_version_dic = message
        # 应用对应Jenkins文件夹-新建流水线名字添加方式 name="folder/name"
        jenkins_api.create_folder(application_name, ignore_failures=True)

        create_dic = {
            "name": name,
            "config_xml": empty_config.format(
                workflow_job=plugin_version_dic.get("workflow-job", ""),
                description=description,
                gitlab_plugin=plugin_version_dic.get("gitlab-plugin", ""),
                workflow_cps=plugin_version_dic.get("workflow-cps", ""),
                config_xml=config_xml),
            "folder_name": application_name
        }
        print("create_dic", create_dic)
        create_job_res = jenkins_api.create_job(**create_dic)
        print("jenkins_api", create_job_res.get("data"))

        if create_job_res.get("status"):
            """增加描述信息"""
            # jenkins_api.desc_job(name, description)

            job_query = ApplicationJenkinsJobsModel.create(view=application_jenkins_query, job_name=name,
                                                           description=description, color="notbuilt")

            # 关联应用视图
            if job_query and pipeline_group_code:
                pipeline_group_query = DevOpsPipelineGroupModel.fetch_one(code=pipeline_group_code)
                if pipeline_group_query:
                    job_code_list = list(pipeline_group_query.job_code_list)
                    job_code_list.append(job_query.code)
                    pipeline_group_query.update(job_code_list=job_code_list)
            # 关联全局视图
            if job_query and overall_view_code:
                overall_view_query = JenkinsJobOverAllViewModel.fetch_one(code=overall_view_code)
                if overall_view_query:
                    job_code_list_2 = list(overall_view_query.job_code_list)
                    job_code_list_2.append(job_query.code)
                    overall_view_query.update(job_code_list=job_code_list_2)

            # 新建流水线操作审计
            operation_audit_create_build_operation_log(user_query, job_query, 1, 1, "新建流水线")

            return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, create_job_res.get("data"),
                                        language=self.ops_language()))
        else:
            return JsonResponse(error(*create_job_res.get("message"), language=self.ops_language()))

    def delete_job(self, request):
        post_data = json.loads(request.body)
        name = post_data.get("name")
        code = post_data.get("code", None)
        if not all([name, code]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        view_name = application_query.get_model_code_name()
        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query,
                                                        jenkins_view_name=view_name)

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name, view=view_query)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_delete(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        result = jenkins_api.delete_job(name=name, folder_name=view_name)

        if result.get("status"):
            if job_query:
                job_query.delete()
            operation_audit_create_build_operation_log(user_query, job_query, 2, 2, "删除流水线")

            folder_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=view_name)
            jobs = ApplicationJenkinsJobsModel.fetch_one(view=folder_query)
            jenkins_job = jenkins_api.get_folder_info(name=view_name)
            if not jenkins_job.get("data", {}).get("jobs") and not jobs:
                jenkins_api.delete_folder(view_name)
            return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))
        return JsonResponse(error(*result.get("message"), language=self.ops_language()))

    def tags_job(self, request):
        data = json.loads(request.body)
        user_query = GetUserInfo().get_user_info(request)
        status, message = self._tags_job(data, user_query)
        if not status:
            return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message=message,
                                      language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))

    def _check_required_plugin(self, jenkins_api):
        plugin_version_dic = {}
        lose_plugin = []
        for plugin in constant.JENKINS_REQUIRED_PLUGIN:
            res = jenkins_api.get_plugins_info(name=plugin)
            if not res.get("data"):
                lose_plugin.append(plugin)
            else:
                plugin_version_dic[plugin] = str(res.get("data", {}).get("version"))
        if lose_plugin:
            return False, lose_plugin
        else:
            return True, plugin_version_dic

    def _get_build_discard(self, old_config):
        """获取触发构建相关配置"""
        # if old_config.get("com.cloudbees.hudson.plugins.folder.Folder"):
        #     pass
        if not old_config.get(constant.FLOW_KEY, {}):
            build_discard_dict = dict()
        elif not old_config.get(constant.FLOW_KEY, {}).get("properties"):
            build_discard_dict = dict()
        elif not old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.BUILD_DISCARD):
            build_discard_dict = dict()
        else:
            build_discard_dict = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
                constant.BUILD_DISCARD, {}).get("strategy", {})

        return build_discard_dict

    def _reconfig_build_discard(self, old_config_xml, build_discard):
        old_config_dict = xml_dict(xml_config=old_config_xml)
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}):
            old_config_dict[constant.FLOW_KEY]["properties"] = {
                constant.BUILD_DISCARD: {
                    "strategy": {
                        "@class": "hudson.tasks.LogRotator",
                        "daysToKeep": "-1",
                        "numToKeep": "-1",
                        "artifactDaysToKeep": "-1",
                        "artifactNumToKeep": "-1"
                    }
                }
            }

        # 首次配置定时触发， 新建TimerTrigger对象
        # Log Rotation
        strategy = {
            "@class": "hudson.tasks.LogRotator",
            "daysToKeep": build_discard.get("daysToKeep", -1),
            "numToKeep": build_discard.get("numToKeep", -1),
            "artifactDaysToKeep": "-1",
            "artifactNumToKeep": "-1"
        }
        if build_discard.get("daysToKeep"):
            strategy["daysToKeep"] = build_discard.get("daysToKeep", -1)
        else:
            strategy["daysToKeep"] = -1
        if build_discard.get("numToKeep"):
            strategy["numToKeep"] = build_discard.get("numToKeep", -1)
        else:
            strategy["numToKeep"] = -1
        if build_discard.get("strategy"):
            old_config_dict[constant.FLOW_KEY]["properties"] = {
                constant.BUILD_DISCARD: {
                    "strategy": strategy
                }
            }
        else:
            old_config_dict[constant.FLOW_KEY]["properties"].pop(constant.BUILD_DISCARD, None)
        new_config_xml = xml_dict(dict_config=old_config_dict)
        return new_config_xml

    def _tags_job(self, data, user_query):
        code = data.get("code")
        job_code = data.get("job_code")
        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        # select cancel
        tags = data.get("tags")
        if not user_query:
            return False, return_message.USER_NOT_EXISTED_MESSAGE
        job_query = ApplicationJenkinsJobsModel.fetch_one(code=job_code)
        if not job_query:
            return False, return_message.JOB_NOT_FOUNT_MESSAGE
        deploy_tags = JenkinsJobTagsModel.fetch_one(jenkins_job=job_query, user_info=user_query)
        if tags:
            if not deploy_tags:
                JenkinsJobTagsModel.create(jenkins_job=job_query, user_info=user_query)
            return True, ""
        else:
            if deploy_tags:
                deploy_tags.delete()
            return True, ""


class PipelineGroup(BaseObject):
    def get_pipeline_groups(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        kwargs = request.GET.dict()
        app_code = kwargs.get("app_code")

        app_query = ApplicationModel.fetch_one(code=app_code)
        if not app_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        if user_query.role != 1:
            status = user_query.is_app_auth(app_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        # 当前用户在指定应用下创建的所有流水线分组
        queryset = DevOpsPipelineGroupModel.fetch_all(create_user=user_query, application=app_query)
        pipeline_group_list = [i.to_base_dict() for i in queryset]
        return JsonResponse(
            success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline_group_list, language=self.ops_language()))


class PipelineOverallView(BaseObject):
    def get_pipeline_overall_views(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        # 当前用户创建的所有全局视图
        queryset = JenkinsJobOverAllViewModel.fetch_all(overall_view_username=user_query.username)
        jenkins_job_overall_view_list = [i.to_base_dict() for i in queryset]
        return JsonResponse(
            success(SuccessStatusCode.MESSAGE_GET_SUCCESS, jenkins_job_overall_view_list, language=self.ops_language()))


class JenkinsJobRebuilt(BaseObject):
    def get_jenkins_job_v2(self, request):
        # 检测Jenkins
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))
        data = request.GET.dict()
        search_type = data.get("search_type", None)
        search_data = data.get("search_data", None)
        page = int(data.get("current", 1))
        per_page = int(data.get("pageSize", 10))
        list_type = data.get("list_type", "all")

        code = data.get("code", None)
        business_code = data.get("business_code", None)
        all_data = data.get("all_data", False)

        dic = {}
        app_list = []
        if list_type == "tags":
            tags_queryset = JenkinsJobTagsModel.fetch_all(user_info=user_query)
            for tags_query in tags_queryset:
                try:
                    app_list.append(tags_query.jenkins_job.code)
                except Exception:
                    res = tags_query.delete()
            dic["code__in"] = app_list
        if search_type and search_data:
            dic[search_type + "__icontains"] = search_data
        if data.get("color"):
            dic["color"] = data.get("color")

        # 应用
        if code:
            application_query = ApplicationModel.fetch_one(code=code)
            if not application_query:
                return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

            application_name = application_query.get_model_code_name()

            view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
            if not view_query:
                view_query = ApplicationJenkinsModel.create(application=application_query,
                                                            jenkins_view_name=application_name)

            job_read_code_list = []
            if user_query.role not in [1]:
                status = user_query.is_app_auth(application_query)
                if not status:
                    return JsonResponse(error(ErrorStatusCode.USER_NOT_APPLICATION_POWER, language=self.ops_language()))

                job_read_code_list, _, _ = user_query.get_code_list(application_query, id_type="job")
                if list_type == "tags":
                    job_code_list = list(set(app_list) & set(job_read_code_list[0]))
                else:
                    job_code_list = job_read_code_list[0]
                dic["code__in"] = job_code_list

            dic["view"] = view_query
            jobs_queryset, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic,
                                                                          order_by="-last_run_datetime")

            jobs_list = [job_query.to_tags_dict_v3(user_query, job_read_code_list) for job_query in jobs_queryset]

            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        # 应用分组
        if business_code:
            business_query = BusinessModel.fetch_one(code=business_code)
            application_queryset = ApplicationModel.fetch_all(business=business_query)

            # 存放所有的应用-jenkins view（管理员）
            view_queryset = [
                ApplicationJenkinsModel.fetch_one(application=app) or ApplicationJenkinsModel.create(
                    jenkins_view_name=app.get_model_code_name(),
                    application=app
                )
                for app in application_queryset
            ]
            dic["view__in"] = view_queryset

            job_read_code_list = []
            if user_query.role not in [1]:
                job_read_code_list, _, _ = user_query.get_code_list(application_queryset, id_type="job")
                if list_type == "tags":
                    job_code_list = list(set(app_list) & set(job_read_code_list[0]))
                else:
                    job_code_list = job_read_code_list[0]
                dic["code__in"] = job_code_list

            current_page, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic,
                                                                         order_by="-last_run_datetime")
            jobs_list = [job_query.to_tags_dict_v3(user_query, job_read_code_list) for job_query in current_page]
            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        # 全部数据
        if all_data:
            application_queryset = ApplicationModel.fetch_all()

            # 存放所有的应用-jenkins view（管理员）
            view_queryset = [
                ApplicationJenkinsModel.fetch_one(application=app) or ApplicationJenkinsModel.create(
                    jenkins_view_name=app.get_model_code_name(),
                    application=app
                )
                for app in application_queryset
            ]
            dic["view__in"] = view_queryset

            job_read_code_list = []
            if user_query.role not in [1]:
                job_read_code_list, _, _ = user_query.get_code_list(application_queryset, id_type="job")
                if list_type == "tags":
                    job_code_list = list(set(app_list) & set(job_read_code_list[0]))
                else:
                    job_code_list = job_read_code_list[0]
                dic["code__in"] = job_code_list

            current_page, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic,
                                                                         order_by="-last_run_datetime")
            jobs_list = [job_query.to_tags_dict_v3(user_query, job_read_code_list) for job_query in current_page]
            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class JenkinsJobTriggers(BaseObject):
    def get_triggers_config(self, request):
        # 校验工具
        kwargs = request.GET.dict()
        job_name = kwargs.get("job_name")
        code = kwargs.get("code", None)

        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        view_name = application.get_model_code_name()
        res = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if res.get("status"):
            trigger_config = res.get("data", "")
            old_config = xml_dict(xml_config=trigger_config)
            jenkins_gitlab_triggers_config, jenkins_time_triggers_config, jenkins_reverse_triggers_config = \
                self._get_jenkins_triggers_config(old_config)
            git_hooks_config = self._get_git_hooks_config(job_name)
            git_jenkins_config = self._clean_data(jenkins_gitlab_triggers_config, jenkins_time_triggers_config,
                                                  jenkins_reverse_triggers_config, git_hooks_config)
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, git_jenkins_config,
                                        language=self.ops_language()))
        else:
            return JsonResponse(error(*res.get("message"), language=self.ops_language()))

    def update_triggers_config(self, request):
        """
               触发构建编辑
               :param request:
               {
                   "mergeRequestLabelFilterConfig": {"include": "", "exclude"： ""},
                   "includeBranchesSpec": "develop",
                   "push_events": "true",
                   "merge_requests_events": "false",
               }
               :return:
               """
        # 校验工具
        kwargs = json.loads(request.body)
        job_name = kwargs.get("job_name", "")
        code = kwargs.get("code", None)
        params = kwargs.get("params", {})
        project_id = kwargs.get("project_id")
        hook_id = kwargs.get("hook_id")

        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        # 校验jenkins工具
        jenkins_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not jenkins_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if jenkins_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(request, **jenkins_query.link_tool_dict())

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_update(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        # 修改触发规则前
        git_jenkins_config = {}
        view_name = application.get_model_code_name()
        res = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if res.get("status"):
            trigger_config = res.get("data", "")
            old_config = xml_dict(xml_config=trigger_config)
            jenkins_gitlab_triggers_config, jenkins_time_triggers_config, jenkins_reverse_triggers_config = \
                self._get_jenkins_triggers_config(old_config)
            git_hooks_config = self._get_git_hooks_config(job_name)
            git_jenkins_config = self._clean_data(jenkins_gitlab_triggers_config, jenkins_time_triggers_config,
                                                  jenkins_reverse_triggers_config, git_hooks_config)
        before_change_dict = git_jenkins_config

        # # 校验git工具
        # git_query = ToolsModel.fetch_one(tool_type="git")
        # if not git_query:
        #     return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        # if git_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        #     return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))
        # git_api = GitLabApi(**git_query.link_git_dict())

        # 查询流水线下关联的gitlab项目id和hooks
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = application.get_model_code_name()
        get_build_job_url = self._get_build_job_url(jenkins_query, job_name, view_name)
        token = self._get_secret_token(jenkins_api, job_name, view_name)
        view_name = application.get_model_code_name()
        res = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if res.get("status"):
            old_config = res.get("data")
        else:
            return JsonResponse(error(*res.get("message"), language=self.ops_language()))

        new_config_xml = self._update_reconfig_dict(old_config, params, token=token)
        res = jenkins_api.reconfig_job(job_name, new_config_xml, folder_name=view_name)
        if res.get("status"):
            git_dic = dict()
            project = dict()
            project_dic = dict()
            if project_id:
                # 校验git工具
                git_query = ToolsModel.fetch_one(tool_type="git")
                if not git_query:
                    return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
                if git_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
                    return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))
                git_api = GitLabApi(**git_query.link_git_dict())

                project_res = git_api.get_project(project_id=project_id)
                print("project_res", project_res)
                if not project_res.get("status"):
                    return JsonResponse(error(*project_res.get("message"), language=self.ops_language()))
                git_hooks_res = git_api.get_project_hooks_list(project_id)
                print("git_hooks_res", git_hooks_res)
                if not git_hooks_res.get("status"):
                    return JsonResponse(error(*git_hooks_res.get("message"), language=self.ops_language()))
                project = project_res.get("data")
                old_project_id = None
                if job_query.project:
                    if job_query.project.get("id"):
                        old_project_id = job_query.project.get("id")
                git_dic = self._update_git_config(old_project_id, project_id, get_build_job_url, token, hook_id,
                                                  git_api,
                                                  params)

            project_dic = {
                "id": project.get("id"),
                "name": project.get("name"),
                "description": project.get("description"),
                "ssh_url_to_repo": project.get("ssh_url_to_repo"),
                "http_url_to_repo": project.get("http_url_to_repo"),
            }
            job_query.update(hooks=git_dic, project=project_dic)

            # 修改触发规则后
            new_git_jenkins_config = {}
            new_view_name = application.get_model_code_name()
            res = jenkins_api.get_job_config(job_name, folder_name=new_view_name)
            if res.get("status"):
                new_trigger_config = res.get("data", "")
                new_config = xml_dict(xml_config=new_trigger_config)
                new_jenkins_gitlab_triggers_config, new_jenkins_time_triggers_config, \
                new_jenkins_reverse_triggers_config = self._get_jenkins_triggers_config(new_config)
                git_hooks_config = self._get_git_hooks_config(job_name)
                new_git_jenkins_config = self._clean_data(new_jenkins_gitlab_triggers_config,
                                                          new_jenkins_time_triggers_config,
                                                          new_jenkins_reverse_triggers_config, git_hooks_config)
            after_change_dict = new_git_jenkins_config

            # 修改触发规则操作审计
            operation_audit_create_build_operation_log(user_query, job_query, 3, 5, "编辑流水线触发规则",
                                                       before_change_dict, after_change_dict)

            return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, language=self.ops_language()))
        else:
            return JsonResponse(error(*res.get("message"), language=self.ops_language()))

    def _get_jenkins_triggers_config(self, old_config):
        """获取触发构建相关配置"""
        # if old_config.get("com.cloudbees.hudson.plugins.folder.Folder"):
        #     pass
        if not old_config.get(constant.FLOW_KEY, {}):
            jenkins_gitlab_triggers_config = jenkins_time_triggers_config = jenkins_reverse_triggers_config = dict()
        elif not old_config.get(constant.FLOW_KEY, {}).get("properties"):
            jenkins_gitlab_triggers_config = jenkins_time_triggers_config = jenkins_reverse_triggers_config = dict()
        elif not old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.TRIGGERS_JOB_KEY):
            jenkins_gitlab_triggers_config = jenkins_time_triggers_config = jenkins_reverse_triggers_config = dict()
        elif not old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.TRIGGERS_JOB_KEY).get(
            "triggers"):
            jenkins_gitlab_triggers_config = jenkins_time_triggers_config = jenkins_reverse_triggers_config = dict()
        else:
            jenkins_gitlab_triggers_config = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
                constant.TRIGGERS_JOB_KEY, {}).get("triggers", {}).get(constant.PUSH_TRIGGERS_KEY, {})
            jenkins_time_triggers_config = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
                constant.TRIGGERS_JOB_KEY, {}).get("triggers", {}).get(constant.TIME_TRIGGERS, {})
            jenkins_reverse_triggers_config = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
                constant.TRIGGERS_JOB_KEY, {}).get("triggers", {}).get(constant.REVERSE_BUILD_TRIGGERS, {})

        return jenkins_gitlab_triggers_config, jenkins_time_triggers_config, jenkins_reverse_triggers_config

    def _get_git_hooks_config(self, job_name):
        """从本地获取hooks信息"""
        print("get_git_hooks_config", job_name)
        jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        print("project_hooks_data", jenkins_job)
        # hooks_dic = dict()
        # if jenkins_job and jenkins_job.hooks:
        hooks_dic = jenkins_job.hooks
        print("11111111111", hooks_dic)
        # else:
        #     project_id = kwargs.get("project_id")
        #     # 校验工具
        #     tool_query = ToolsModel.fetch_one(tool_type="git")
        #     jenkins_query = ToolsModel.fetch_one(tool_type="jenkins")
        #     if not tool_query:
        #         return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        #     if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        #         return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        #
        #     # 创建jenkins连接
        #     jenkins_api = GitLabApi(**tool_query.link_git_dict())
        #     project_hooks_res = jenkins_api.get_project_hooks_list(project_id)
        #     if not project_hooks_res.get("status"):
        #         return JsonResponse(error(*project_hooks_res.get("message"), language=self.ops_language()))
        #     project_hooks_data = project_hooks_res.get("data")
        #
        #     for project_hooks in project_hooks_data:
        #         api_addr = jenkins_query.api_addr if jenkins_query.api_addr[-1] == "/" else jenkins_query.api_addr + "/"
        #         project_url = api_addr + "project/" + job_name
        #         print("hooks_dic1", project_url, project_hooks.get("url"))
        #         if project_hooks.get("url") == project_url:
        #             hooks_dic = project_hooks
        #             break
        #     print("2222222", hooks_dic)
        project_hooks = {
            "id": hooks_dic.get("id"),
            "project_id": hooks_dic.get("project_id"),
            "url": hooks_dic.get("url"),
            "push_events": hooks_dic.get("push_events"),
            "merge_requests_events": hooks_dic.get("merge_requests_events"),
            "tag_push_events": hooks_dic.get("tag_push_events")
        }
        return project_hooks

    def _clean_data(self, jenkins_gitlab_triggers_config, jenkins_time_triggers_config, jenkins_reverse_triggers_config,
                    git_hooks_config):
        """整理数据-前端需要的字段"""
        git_jenkins_config = {
            "branchFilterType": jenkins_gitlab_triggers_config.get("branchFilterType"),
            "includeBranchesSpec": jenkins_gitlab_triggers_config.get("includeBranchesSpec"),
            "sourceBranchRegex": jenkins_gitlab_triggers_config.get("sourceBranchRegex"),
            "spec": jenkins_time_triggers_config.get("spec"),
            "ReverseBuildTrigger": jenkins_reverse_triggers_config,
            "hook_id": git_hooks_config.get("id"),
            "project_id": git_hooks_config.get("project_id"),
            "url": git_hooks_config.get("url"),
            "push_events": git_hooks_config.get("push_events"),
            "tag_push_events": git_hooks_config.get("tag_push_events"),
            "merge_requests_events": git_hooks_config.get("merge_requests_events")
        }
        return git_jenkins_config

    def _get_build_job_url(self, jenkins_query, job_name, view_name):
        """获取jenkins流水线构建url, gitlab触发使用"""
        api_addr = jenkins_query.api_addr if jenkins_query.api_addr[-1] == "/" else jenkins_query.api_addr + "/"
        import urllib.parse
        get_build_job_url = api_addr + "project/" + view_name + "/" + urllib.parse.quote(job_name)
        return get_build_job_url

    def _get_secret_token(self, jenkins_api, job_name, view_name=None):
        """获取jenkins流水线构建token, gitlab触发使用"""
        res_token = jenkins_api.generate_secret_token(job_name, folder_name=view_name)
        if res_token.get("status"):
            token = res_token.get("data")
            print("token", token)
            return token
        else:
            return "b538c3c49bf8c3a55ddaab6f7c12d15b"

    def _update_git_config(self, old_project_id, project_id, get_build_job_url, token, hook_id, git_api, params):
        """修改gitlab项目webhooks"""
        if project_id and hook_id:
            # 参数有hooks 说明本地已经存储了hooks数据，查询gitlab是否有数据，走修改流程
            hooks_res = git_api.get_project_hooks(project_id, hook_id)
            if not hooks_res.get("status"):
                # gitlab没有查询到数据，可能被删除，或者本地数据错误， 走新建流程
                git_dic = self._create_hooks(old_project_id, project_id, get_build_job_url, token, params, git_api,
                                             hook_id=hook_id)
            else:
                # 本地有数据，gitlab也有数据，就直接修改数据
                hooks = hooks_res.get("data")
                git_dic = self._update_hooks(hooks, params, token)
        else:
            # 参数没有hooks 说明本地获取不到hooks数据，需要走新建流程
            git_dic = self._create_hooks(old_project_id, project_id, get_build_job_url, token, params, git_api,
                                         hook_id=hook_id)
        # 返回hooks数据
        return git_dic

    def _create_hooks(self, old_project_id, project_id, project_url, token, params, git_api, hook_id):
        """创建hooks配置项-当本地没有存储hooks信息或者本地hooks信息与gitlab不一致时调用"""
        git_dict = {
            "project_id": project_id,
            "url": project_url,
            "token": token
        }
        if params.get("push_events"): git_dict["push_events"] = params.get("push_events")
        if params.get("tag_push_events"): git_dict["tag_push_events"] = params.get("tag_push_events")
        if params.get("merge_requests_events"): git_dict["merge_requests_events"] = params.get(
            "merge_requests_events")
        print("git_dict_create", git_dict)
        res = git_api.create_project_hooks(**git_dict)
        res_delete = git_api.delete_project_hooks(old_project_id, hook_id)
        print("res_delete", res_delete)
        if not res.get("status"):
            return {}
        git_dic = res.get("data")
        return git_dic

    def _update_hooks(self, hooks, params, token):
        """创建hooks配置项-当本地存储hooks信息且本地hooks信息与gitlab一致时调用"""
        if params.get("push_events"): hooks.push_events = params.get("push_events", "false")
        if params.get("tag_push_events"): hooks.tag_push_events = params.get("tag_push_events", "false")
        hooks.token = token
        if params.get("merge_requests_events"): hooks.merge_requests_events = params.get("merge_requests_events",
                                                                                         "false")
        hooks.save()
        git_dic = hooks.attributes
        print("git_dict_create", git_dic)
        return git_dic

    def _update_reconfig_dict(self, old_config, params, token):
        """更新jenkins配置文件--定时构建，触发构建，其他工程触发"""
        old_config_dict = xml_dict(xml_config=old_config)
        # 空白配置，新建properties对象
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}):
            old_config_dict[constant.FLOW_KEY]["properties"] = {
                constant.TRIGGERS_JOB_KEY: {
                    "triggers": {
                        constant.PUSH_TRIGGERS_KEY: {
                        }
                    }
                }
            }
        # 首次配置触发规则，新建PipelineTriggersJobProperty对象
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.TRIGGERS_JOB_KEY, {}):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY] = {
                "triggers": {
                    constant.PUSH_TRIGGERS_KEY: {

                    }
                }
            }
        # 首次配置配置触发， 新建triggers对象
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.TRIGGERS_JOB_KEY, {}).get(
            "triggers"):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"] = {
                constant.PUSH_TRIGGERS_KEY: {
                },
                constant.TIME_TRIGGERS: {
                    "spec": None
                }
            }
        # 首次配置定时触发， 新建TimerTrigger对象
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.TRIGGERS_JOB_KEY, {}).get(
            "triggers").get(constant.TIME_TRIGGERS):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"][
                constant.TIME_TRIGGERS] = {
                "spec": None
            }
        # 首次配置定时触发， 新建GitLabPushTrigger对象

        plugin = old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}).get(
            "com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty", {}).get("@plugin",
                                                                                        "gitlab-plugin@1.5.13")

        print("plugin", plugin)
        default_triggers_key = {
            "@plugin": plugin,  # gitlab-plugin插件版本号
            "spec": None,  # spec
            "triggerOnPush": "true",  # Push Events
            "triggerOnMergeRequest": "true",  # Opened Merge Request Events
            "triggerOnPipelineEvent": "true",  # Build on successful pipeline events
            "triggerOnAcceptedMergeRequest": "true",  # Accepted Merge Request Events
            "triggerOnClosedMergeRequest": "true",  # Closed Merge Request Events
            "triggerOnApprovedMergeRequest": "true",  # Approved Merge Requests (EE-only)
            "triggerOpenMergeRequestOnPush": "never",  # Rebuild open Merge Requests
            "triggerOnNoteRequest": "true",  # Comments
            "noteRegex": None,  # Comment (regex) for triggering a build
            "ciSkip": "true",  # Enable [ci-skip]
            "skipWorkInProgressMergeRequest": "true",  # Ignore WIP Merge Requests
            "setBuildDescription": "true",  # Set build description to build cause (eg. Merge request or Git Push )
            "branchFilterType": "NameBasedFilter",  # Allowed branches
            "includeBranchesSpec": None,
            "excludeBranchesSpec": None,  # Source Branch Regex
            "sourceBranchRegex": None,  # Target Branch Regex
            "targetBranchRegex": None,  #
            "secretToken": token,
            "pendingBuildName": None,
            "cancelPendingBuildsOnUpdate": "true",  # Cancel pending merge request builds on update
        }

        # 触发构建-push,tag, marge
        """
        branchFilterType = "NameBasedFilter" or "RegexBasedFilter"
        includeBranchesSpec = "devlop,master,"
        sourceBranchRegex = "dev.*"
        """
        # 多选分支
        if params.get("branchFilterType"):
            default_triggers_key["branchFilterType"] = params.get("branchFilterType", "")
        # 多选分支
        if params.get("includeBranchesSpec"):
            default_triggers_key["includeBranchesSpec"] = params.get("includeBranchesSpec", "")
        # 正则分支
        if params.get("sourceBranchRegex"):
            default_triggers_key["sourceBranchRegex"] = params.get("sourceBranchRegex", "")
        old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"][
            constant.PUSH_TRIGGERS_KEY] = default_triggers_key
        if not params.get("branchFilterType") and not params.get("includeBranchesSpec") and not params.get(
            "sourceBranchRegex"):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"].pop(
                constant.PUSH_TRIGGERS_KEY, None)

        # 定时构建 spec = "H/15 * * * *"
        if params.get("spec", None):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"][
                constant.TIME_TRIGGERS] = {"spec": params.get("spec", None)}
        else:
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"].pop(
                constant.TIME_TRIGGERS, None)

        # 其他工程构建后触发
        """
        # 只有构建稳定时触发
        SUCCESS = {
            "spec": None,
            "upstreamProjects": "ceshi2-测试12,ceshi2-demo15,",
            "threshold": {
                "name": "SUCCESS",
                "ordinal": "0",
                "color": "BLUE",
                "completeBuild": "true"
            }
        }
        # 即使构建不稳定时也会触发
        UNSTABLE = {
            "spec": None,
            "upstreamProjects": "ceshi2-测试12,ceshi2-demo15,",
            "threshold": {
                "name": "UNSTABLE",
                "ordinal": "1",
                "color": "YELLOW",
                "completeBuild": "true"
            }
        }
        # 即使构建失败时也会触发
        FAILURE = {
            "spec": None,
            "upstreamProjects": "ceshi2-测试12,ceshi2-demo15,",
            "threshold": {
                "name": "FAILURE",
                "ordinal": "2",
                "color": "RED",
                "completeBuild": "true"
            }
        }
        """
        if params.get("ReverseBuildTrigger", None):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"][
                constant.REVERSE_BUILD_TRIGGERS] = params.get("ReverseBuildTrigger", None)
        else:
            old_config_dict[constant.FLOW_KEY]["properties"][constant.TRIGGERS_JOB_KEY]["triggers"].pop(
                constant.REVERSE_BUILD_TRIGGERS, None)

        new_config = xml_dict(dict_config=old_config_dict)
        return new_config


class JenkinsJobParameters(BaseObject):
    def get_parameters(self, request):
        # 校验工具
        kwargs = request.GET.dict()
        job_name = kwargs.get("job_name", "")
        code = kwargs.get("code", None)

        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        # 查询流水线下关联的gitlab项目
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        # 校验jenkins工具
        jenkins_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not jenkins_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if jenkins_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(**jenkins_query.link_tool_dict())
        view_name = application.get_model_code_name()
        res = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if res.get("status"):
            old_config = res.get("data")
        else:
            return JsonResponse(error(*res.get("message"), language=self.ops_language()))

        old_config_dict = xml_dict(xml_config=old_config)
        data = self._get_parameters(old_config_dict)

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

    def update_parameters(self, request):
        # 修改构建参数
        kwargs = json.loads(request.body)
        job_name = kwargs.get("job_name", "")
        code = kwargs.get("code", None)
        # string_parameter choice_parameter
        params = kwargs.get("params", {})
        # 校验工具
        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        # 查询流水线下关联的gitlab项目
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 校验jenkins工具
        jenkins_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not jenkins_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if jenkins_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_update(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **jenkins_query.link_tool_dict())
        view_name = application.get_model_code_name()
        res = jenkins_api.get_job_config(job_name, folder_name=view_name)
        if res.get("status"):
            old_config = res.get("data")
        else:
            return JsonResponse(error(*res.get("message"), language=self.ops_language()))
        if not self._check_parameter_variable(params):
            return JsonResponse(error(ErrorStatusCode.NAME_NOT_CHINESE, language=self.ops_language()))
        if not self._check_parameter_format(params):
            return JsonResponse(error(ErrorStatusCode.NAME_FORMAT_ERROR, language=self.ops_language()))
        if not self._check_name_unique(params):
            return JsonResponse(error(ErrorStatusCode.NAME_UNIQUE_ERROR, language=self.ops_language()))
        new_xml_config, string_parameter_list, choice_parameter_list = self._update_parameter(old_config, params)
        jenkins_api.reconfig_job(job_name, new_xml_config, folder_name=view_name)
        data = {"string_parameter": string_parameter_list, "choice_parameter": choice_parameter_list}

        # 编辑参数设置操作审计
        old_config_dict = xml_dict(xml_config=old_config)
        old_data = self._get_parameters(old_config_dict)

        before_change_dict = old_data

        after_change_dict = data

        operation_audit_create_build_operation_log(user_query, job_query, 3, 6, "编辑流水线参数设置", before_change_dict,
                                                   after_change_dict)

        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, data, language=self.ops_language()))

    def _get_parameters(self, old_config):
        # 空白配置，新建properties对象
        # 请求URL->[/t/devops/api/pipeline/v0_1/jenkins/job/reconfig/parameter/], 请求方法->[GET]
        # 请求参数->[{"code": "1", "job_name": "Deploy-Frontend-Commit"}]
        StringParameterDefinition = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
            constant.PARAMETERS, {}).get("parameterDefinitions", {}).get("hudson.model.StringParameterDefinition", [])
        if StringParameterDefinition:
            print("StringParameterDefinition", StringParameterDefinition)
            if isinstance(StringParameterDefinition, list):
                string_parameter = StringParameterDefinition
            else:
                string_parameter = [StringParameterDefinition]
        else:
            string_parameter = list()
        ChoiceParameterDefinition = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
            constant.PARAMETERS, {}).get("parameterDefinitions", {}).get("hudson.model.ChoiceParameterDefinition", {})
        if ChoiceParameterDefinition:
            if isinstance(ChoiceParameterDefinition, list):
                choice_parameter = ChoiceParameterDefinition
            else:
                choice_parameter = [ChoiceParameterDefinition]
        else:
            choice_parameter = list()
        string_parameter_list, choice_parameter_list = self._parse_data(string_parameter, choice_parameter)

        data = {"string_parameter": string_parameter_list, "choice_parameter": choice_parameter_list}
        return data

    def _parse_data(self, string_parameter, choice_parameter):
        """解析源数据"""
        if isinstance(string_parameter, dict):
            string_parameter = [string_parameter]
        if isinstance(choice_parameter, dict):
            choice_parameter = [choice_parameter]

        string_parameter_list = list()
        print("string_parameter_list", string_parameter, type(string_parameter))
        for parameter in string_parameter:
            print("parameter", parameter)
            string_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "default_string": parameter.get("defaultValue")
            })

        choice_parameter_list = list()
        for parameter in choice_parameter:
            choices_string_list = parameter.get("choices", {}).get("a", {}).get("string", [])
            if isinstance(choices_string_list, str):
                choices_string_list = [choices_string_list]
            choice_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "choices_string_list": choices_string_list
            })
        return string_parameter_list, choice_parameter_list

    def _unparse_data(self, string_parameter, choice_parameter):
        """转换成源数据"""
        string_parameter_list = list()
        for parameter in string_parameter:
            string_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "defaultValue": parameter.get("default_string"),
                "trim": "false"
            })

        choice_parameter_list = list()
        for parameter in choice_parameter:
            choices_string_list = parameter.get("choices_string_list")
            if isinstance(choices_string_list, list) and len(choices_string_list) == 1:
                choices_string_list = choices_string_list[0]
            choice_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "choices": {
                    "@class": "java.util.Arrays$ArrayList",
                    "a": {
                        "@class": "string-array",
                        "string": choices_string_list
                    }
                }
            })
        if len(string_parameter_list) == 1:
            string_parameter_list = string_parameter_list[0]
        if len(choice_parameter_list) == 1:
            choice_parameter_list = choice_parameter_list[0]
        return string_parameter_list, choice_parameter_list

    def _check_parameter_variable(self, params):
        """检查变量名是否合规"""
        parameter_list = params.get("string_parameter") + params.get("choice_parameter")
        for parameter in parameter_list:
            name = parameter.get("name")
            print("name_check", name)
            if not check_variable_name(name):
                return False
        return True

    def _check_parameter_format(self, params):
        """检查参数格式是否正确"""
        string_parameter_list = params.get("string_parameter")
        choice_parameter_list = params.get("choice_parameter")
        for string_parameter in string_parameter_list:
            string_parameter_keys = string_parameter.keys()
            if "name" not in string_parameter_keys:
                return False
            if "default_string" not in string_parameter_keys:
                return False
            if not isinstance(string_parameter.get("default_string"), str):
                return False
        for choice_parameter in choice_parameter_list:
            choice_parameter_keys = choice_parameter.keys()
            if "name" not in choice_parameter_keys:
                return False
            if "choices_string_list" not in choice_parameter_keys:
                return False
            if not isinstance(choice_parameter.get("choices_string_list"), list):
                return False
        return True

    def _check_name_unique(self, params):
        # 检查name是否唯一
        parameter_list = params.get("string_parameter") + params.get("choice_parameter")
        name_list = [parameter.get("name") for parameter in parameter_list]
        if len(name_list) == len(list(set(name_list))):
            return True
        else:
            return False

    def _update_parameter(self, old_config, params):
        """更新构建参数-全量数据"""
        print("old_config", old_config)
        old_config_dict = xml_dict(xml_config=old_config)
        # 空白配置，新建properties对象
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}):
            old_config_dict[constant.FLOW_KEY]["properties"] = {
                constant.PARAMETERS: {
                }
            }
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}):
            old_config_dict[constant.FLOW_KEY]["properties"] = {
                constant.PARAMETERS: {
                    "parameterDefinitions": {
                    }
                }
            }
        if not old_config_dict.get(constant.FLOW_KEY, {}).get("properties", {}).get(constant.PARAMETERS):
            old_config_dict[constant.FLOW_KEY]["properties"][constant.PARAMETERS] = {
                "parameterDefinitions": {
                }
            }
        string_parameter, choice_parameter = self._unparse_data(params.get("string_parameter"),
                                                                params.get("choice_parameter"))
        if not string_parameter and not choice_parameter:
            old_config_dict[constant.FLOW_KEY]["properties"].pop(constant.PARAMETERS, None)
        else:
            old_config_dict[constant.FLOW_KEY]["properties"][constant.PARAMETERS]["parameterDefinitions"] = {
                "hudson.model.StringParameterDefinition": string_parameter,
                "hudson.model.ChoiceParameterDefinition": choice_parameter
            }
        new_xml_config = xml_dict(dict_config=old_config_dict)
        string_parameter_list, choice_parameter_list = self._parse_data(string_parameter, choice_parameter)
        return new_xml_config, string_parameter_list, choice_parameter_list


class JenkinsJobReconfigScript(BaseObject):
    def get_pipeline_script(self, request):
        """获取流水线列表"""
        data = request.GET.dict()
        job_name = data.get("job_name", None)
        code = data.get("code", None)
        if not all([code, job_name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        print("job_name", job_name)

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        view_name = application.get_model_code_name()
        # 获取全部job(包含当前构建历史)
        result = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        job_config = result.get("data")
        script = self._get_jenkins_config(job_config)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, script, language=self.ops_language()))

    def update_pipeline_script(self, request):
        post_data = json.loads(request.body)
        job_name = post_data.get("job_name")
        code = post_data.get("code", None)
        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        jenkins_file = post_data.get("jenkins_file", "")

        if not all([jenkins_file, job_name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        view = ApplicationJenkinsModel.fetch_one(application=application)
        if not view:
            dic = {"application": application, "jenkins_view_name": application.get_model_code_name}
            view = ApplicationJenkinsModel.create(**dic)

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 判断权限-编辑-流程配置
        if user_query.role != 1:
            status = job_query.is_auth_update(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        # 检查语法
        result = jenkins_api.check_jenkinsfile_syntax(jenkins_file)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))

        # 获取配置文件--xml格式
        view_name = application.get_model_code_name()
        result = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        job_config = result.get("data")

        # 编辑之前的流程配置
        old_script = self._get_jenkins_config(job_config)
        before_change_dict = {"before_update_config": old_script}

        config_xml = self._update_jenkins_config(job_config, jenkins_file)
        result = jenkins_api.reconfig_job(job_name, config_xml, folder_name=view_name)

        if result.get("status"):
            new_result = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
            if not new_result.get("status"):
                return JsonResponse(error(*new_result.get("message"), language=self.ops_language()))
            new_job_config = new_result.get("data")

            # 编辑之后的流程配置
            new_script = self._get_jenkins_config(new_job_config)
            after_change_dict = {"after_update_config": new_script}
            # 编辑流程配置操作日志
            operation_audit_create_build_operation_log(user_query, job_query, 3, 4, "编辑流水线流程配置",
                                                       before_change_dict, after_change_dict)
            return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, result.get("data"),
                                        language=self.ops_language()))
        return JsonResponse(error(*result.get("message"), language=self.ops_language()))

    def check_pipeline_script_syntax(self, request):
        jenkins_file = request.POST.get("jenkins_file")
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

        result = jenkins_api.check_jenkinsfile_syntax(jenkins_file)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))

    def pipeline_script_jenkinsfile_to_json(self, request):
        jenkins_file = request.POST.get("jenkins_file")

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
        result = jenkins_api.to_json(jenkins_file)
        print("result", result)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, result.get("data"),
                                    language=self.ops_language()))

    def pipeline_script_json_to_jenkinsfile(self, request):
        json_file = request.POST.get("json_file")
        print("json_file", type(json_file))
        print("json_file", json_file)
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
        result = jenkins_api.to_jenkins_file(json_file)
        print("result", result)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, result.get("data"),
                                    language=self.ops_language()))

    def _get_jenkins_config(self, job_config):
        """获取jenkins配置文件中pipeline脚本"""
        config_dict = xml_dict(xml_config=job_config)
        script = config_dict.get(constant.FLOW_KEY, {}).get("definition", {}).get("script")
        return script

    def _update_jenkins_config(self, job_config, jenkins_file):
        # xml配置文件 转dict
        config_dict = xml_dict(xml_config=job_config)
        script = config_dict.get(constant.FLOW_KEY, {}).get("definition", {}).get("script", "")
        if script:
            config_dict[constant.FLOW_KEY]["definition"]["script"] = jenkins_file

        # 填充完最新数据后传xml格式
        config_xml = xml_dict(dict_config=config_dict)
        return config_xml


class JenkinsJobBuild(BaseObject):
    def get_build_params(self, request):
        trigger_build_params = constant.trigger_build_params
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, trigger_build_params,
                                    language=self.ops_language()))

    def get_build_info(self, request):
        data = request.GET.dict()
        job_name = data.get("job_name")
        number = data.get("number")
        if not all([job_name, number]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        try:
            number = int(number)
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, e, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 获取全部job
        build_info = dict()
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name

        build_info_query = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=number)
        if not build_info_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # if build_info_query and build_info_query.output and (not build_info_query.building):
        #     build_info["build_console_output"] = build_info_query.output
        # else:
        #     result_get_build_console_output = jenkins_api.get_build_console_output(name=job_name, number=number,
        #                                                                            folder_name=view_name)
        #     if not result_get_build_console_output.get("status"):
        #         if (not build_info_query.output) and (not build_info_query.building):
        #             build_info["build_console_output"] = "未获取到构建历史，请稍后重试!"
        #     else:
        #         build_console_output = result_get_build_console_output.get("data") or ""
        #         build_info["build_console_output"] = build_console_output
        #         build_info_query.update(output=build_console_output)

        view_as_plain_text = jenkins_api.get_build_full_log_info(view_name, job_name, number)
        if view_as_plain_text.get("data") or "":
            build_info["build_console_output"] = view_as_plain_text.get("data") or ""

        result_get_job_build_info = jenkins_api.get_build_info(name=job_name, number=number, folder_name=view_name)
        if result_get_job_build_info.get("status"):
            build_info["build_info"] = filter_build_info_data(result_get_job_build_info.get("data", {}))
        result_get_job_config = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
        if result_get_job_config.get("status"):
            config_json_data = xmltodict.parse(result_get_job_config.get("data"))
            build_info["job_config"] = config_json_data
            build_info["script"] = (config_json_data.get(constant.FLOW_KEY, {})).get("definition", {}).get("script")

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, build_info, language=self.ops_language()))

    def build_start(self, request):
        post_data = json.loads(request.body)
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        code = post_data.get("code")
        app_query = ApplicationModel.fetch_one(code=code)
        if not app_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        return self._build_start(post_data, user_query, app_query)

    def _build_start(self, post_data, user_query, app_query):
        start = time.time()
        name = post_data.get("name")
        req_source = post_data.get("req_source", "页面执行")
        parameters = post_data.get("parameters")
        view = ApplicationJenkinsModel.fetch_one(application=app_query)
        if not view:
            dic = {"application": app_query, "jenkins_view_name": app_query.get_model_code_name}
            view = ApplicationJenkinsModel.create(**dic)

        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name, view=view)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_run(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

        view_name = view.jenkins_view_name
        if parameters:
            res = jenkins_api.get_job_config(name, folder_name=view_name)
            if not res.get("status"):
                return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
            else:
                xml_config = res.get("data")
            if not self._check_parameters(xml_config, parameters):
                return JsonResponse(error(ErrorStatusCode.NAME_FORMAT_ERROR, language=self.ops_language()))

        # status, queue_num = self._build_job_queue_num(job_query, jenkins_api, name, parameters, view_name)
        # if not status:
        #     return queue_num
        #
        # if ApplicationJenkinsJobBuildModel.fetch_one(queue_num=queue_num, job=job_query):
        #     custom_message = "当前流水线已经点击过执行正在处理，请稍后再次执行！"
        #     return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message=custom_message))

        queue_num = None
        result_job_build = jenkins_api.build_job(name, parameters=parameters, folder_name=view_name)
        if result_job_build.get("status"):
            queue_num = result_job_build.get("data")
            if ApplicationJenkinsJobBuildModel.fetch_one(queue_num=queue_num, job=job_query):
                custom_message = "当前流水线已经点击过执行正在处理，请稍后再次执行！"
                return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message=custom_message))
        else:
            return JsonResponse(error(*result_job_build.get("message"), language=self.ops_language()))

        result = jenkins_api.get_job_config(name=name, folder_name=view_name)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        job_config = result.get("data")
        script = self._get_jenkins_config(job_config)

        result = jenkins_api.to_json(script)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        result_test = result.get("data")

        # 提取出脚本中的人工确认
        input_id_submitter_dic = {}
        try:
            # 提取脚本中有input步骤的arguments列表
            input_id_submitter_list = extract_input_arguments(result_test)
            input_id_submitter_dic = extract_input_arguments_2(input_id_submitter_list)
        except Exception as e:
            print("执行流水线处理脚本内容（人工确认）error")
            pass

        # 将脚本整理区分为并行阶段
        parallel_names = {}
        try:
            # 脚本中的阶段
            stages = result_test.get("pipeline", {}).get("stages")
            for stage in stages:
                stages_parallel = stage.get("parallel", [])
                stages_parallel_name = stage.get("name", None)
                if stages_parallel:
                    parallel_list = [i.get("name") for i in stages_parallel]
                    parallel_names[stages_parallel_name] = parallel_list
        except Exception as e:
            print("执行流水线处理脚本内容（并行阶段）error")
            pass

        dt = {
            "queue_num": queue_num,
            "is_celery": True,
            "job": job_query,
            "username": user_query.username,
            "ch_name": user_query.ch_name,
            "req_source": req_source,
            "app_from": "pipeline",
            "result": "WAITING",
            "job_script": parallel_names
        }
        log_query = ApplicationJenkinsJobBuildModel.create(**dt)

        job_dict = {
            "last_run_username": user_query.username,
            "last_run_ch_name": user_query.ch_name,
            "last_run_req_source": req_source,
            "last_run_app_from": "pipeline",
            "last_run_result": "WAITING",
            "color": "waiting",
            "result": "WAITING"
        }
        job_query.update(**job_dict)

        celery_build_num_and_run_username.delay(job_query, view_name, jenkins_api, user_query, log_query,
                                                parallel_names, input_id_submitter_dic, app_query.code)
        # celery_build_num_and_run_username(job_query, view_name, jenkins_api, user_query, log_query)

        end = time.time()
        print(f"执行流水线耗时：{end - start}，构建队列ID：{queue_num}")
        return JsonResponse(success(SuccessStatusCode.JOB_BUILD_SUCCESS, queue_num, language=self.ops_language()))

    def _get_jenkins_config(self, job_config):
        """获取jenkins配置文件中pipeline脚本"""
        config_dict = xml_dict(xml_config=job_config)
        script = config_dict.get(constant.FLOW_KEY, {}).get("definition", {}).get("script")
        return script

    def _build_job_queue_num(self, job_query, jenkins_api, name, parameters, folder_name):
        result_job_build = jenkins_api.build_job(name, parameters=parameters, folder_name=folder_name)
        if not result_job_build.get("status"):
            return False, JsonResponse(error(*result_job_build.get("message"), language=self.ops_language()))
        queue_num = result_job_build.get("data")
        while True:
            if ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, queue_num=queue_num):
                result_job_build = jenkins_api.build_job(name, parameters=parameters, folder_name=folder_name)
                if not result_job_build.get("status"):
                    return False, JsonResponse(error(*result_job_build.get("message"), language=self.ops_language()))
                queue_num = result_job_build.get("data")
            else:
                return True, queue_num
            time.sleep(5)

    def build_abort(self, request):
        post_data = json.loads(request.body)
        job_name = post_data.get("job_name")
        num = post_data.get("num")

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name
        build_abort = jenkins_api.build_abort(job_name=job_name, num=num, folder_name=view_name)
        if not build_abort.get("status"):
            return JsonResponse(error(*build_abort.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, build_abort.get("data"),
                                    language=self.ops_language()))

    def build_stop(self, request):
        post_data = json.loads(request.body)
        name = post_data.get("name")
        number = post_data.get("number")

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name)

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_stop(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name
        # 获取全部job
        result_job_stop_build_config = jenkins_api.stop_build(name, number=number, folder_name=view_name)
        print("result", result_job_stop_build_config)
        if not result_job_stop_build_config.get("status"):
            return JsonResponse(error(*result_job_stop_build_config.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_STOP_SUCCESS, result_job_stop_build_config.get("data"),
                                    language=self.ops_language()))

    def build_proceed(self, request):
        post_data = json.loads(request.body)
        job_name = post_data.get("job_name")
        num = post_data.get("num")

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        view_name = job_query.view.jenkins_view_name
        build_proceed_empty = jenkins_api.build_proceed_empty(job_name=job_name, num=num, folder_name=view_name)
        if not build_proceed_empty.get("status"):
            return JsonResponse(error(*build_proceed_empty.get("message"), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, build_proceed_empty.get("data"),
                                    language=self.ops_language()))

    def build_delete(self, request):
        post_data = json.loads(request.body)
        name = post_data.get("name")
        number = post_data.get("number")
        build_code = post_data.get("build_code")
        app_code = post_data.get("app_code")

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        application_query = ApplicationModel.fetch_one(code=app_code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        application_name = application_query.get_model_code_name()

        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query,
                                                        jenkins_view_name=application_name)
        view_name = view_query.jenkins_view_name

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_delete_log(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))
        result_job_delete_build_config = jenkins_api.delete_build(name, number=number, folder_name=view_name)
        if not result_job_delete_build_config.get("status"):
            return JsonResponse(error(*result_job_delete_build_config.get("message"), language=self.ops_language()))
        build_query = ApplicationJenkinsJobBuildModel.fetch_one(code=build_code)
        if build_query:
            build_query.delete()
            # 修改当前流水线最近一次构建历史信息
            job_result = jenkins_api.get_job_info(job_query.job_name, folder_name=view_name)
            if not job_result.get("status"):
                print(f"获取{job_query.job_name}信息Error：", job_result.get("message"))
            else:
                job_dic = {}
                job_info = job_result.get("data")
                job_info_builds_list = job_info.get("builds", [])

                # 获取构建历史
                if job_info_builds_list:
                    number = job_info_builds_list[0].get("number")
                    result = jenkins_api.get_build_info(name=job_query.job_name, number=number, folder_name=view_name)
                    if not result:
                        print(f"获取{job_query.job_name}最近构建历史Error：", result.get("message"))

                    job_build_info = result.get("data")
                    job_dic["timestamp"] = str(job_build_info.get("timestamp", "0"))
                    job_dic["result"] = job_build_info.get("result", "")

                    result_dic = {}
                    # 更新当前job的上次构建相关信息
                    if job_build_info:
                        result_dic = filter_build_info_data(job_build_info)

                        # 流水线最近构建历史
                        job_dic["last_run_number"] = number
                        job_dic["last_run_result"] = result_dic.get("result", "")
                        job_dic["last_run_timestamp"] = str(result_dic.get("timestamp", ""))
                        job_dic["last_run_datetime"] = result_dic.get("datetime", "")
                        job_dic["last_run_duration"] = str(result_dic.get("duration", "1"))
                        job_dic["last_run_duration_str"] = result_dic.get("duration_str", "")
                        job_dic["last_run_revision"] = result_dic.get("revision", "")


                        result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
                        result_dic["duration"] = str(result_dic.get("duration", "1"))

                        result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
                            "datetime") else ""
                        result_dic["username"] = "系统执行"
                        result_dic["ch_name"] = "系统执行"
                        result_dic["req_source"] = "外部执行"
                        result_dic["app_from"] = "jenkins"
                        result_dic["job"] = job_query

                    jenkins_build_query = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=number)
                    if jenkins_build_query:
                        job_dic = {
                            "last_run_number": jenkins_build_query.number,
                            "last_run_username": jenkins_build_query.username,
                            "last_run_ch_name": jenkins_build_query.ch_name,
                            "last_run_req_source": jenkins_build_query.req_source,
                            "last_run_app_from": jenkins_build_query.app_from,
                            "last_run_result": jenkins_build_query.result,
                            "last_run_timestamp": jenkins_build_query.timestamp,
                            "last_run_datetime": jenkins_build_query.datetime,
                            "last_run_duration": jenkins_build_query.duration,
                            "last_run_duration_str": jenkins_build_query.duration_str,
                            "last_run_revision": jenkins_build_query.revision
                        }
                        job_query.update(**job_dic)
                    else:
                        ApplicationJenkinsJobBuildModel.create(**result_dic)
                        job_dic["last_run_username"] = "系统执行"
                        job_dic["last_run_ch_name"] = "系统执行"
                        job_dic["last_run_req_source"] = "外部执行"
                        job_dic["last_run_app_from"] = "jenkins"
                        job_query.update(**job_dic)

        return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS,
                                    result_job_delete_build_config.get("data"), language=self.ops_language()))

    def _check_parameters(self, xml_config, parameters):
        config_dict = xml_dict(xml_config=xml_config)
        data = self._get_parameters(config_dict)
        string_parameter_list = data.get("string_parameter", [])
        choice_parameter_list = data.get("choice_parameter", [])
        all_parameter_list = [string.get("name") for string in (choice_parameter_list + string_parameter_list)]
        string_parameter_name_list = [string.get("name") for string in choice_parameter_list]
        # 校验进来的参数是否已经配置过，发现未知参数报错
        for key, value in parameters.items():
            if key not in all_parameter_list:
                return False
        # 校验参数是否为选项参数，是的话检验发来的参数数据是否在列表中，不是报错
        for key, value in parameters.items():
            if key in string_parameter_name_list:
                for choice in choice_parameter_list:
                    if key == choice.get("name") and value not in choice.get("choices_string_list"):
                        return False
        return True

    def _get_parameters(self, old_config):
        # 空白配置，新建properties对象
        StringParameterDefinition = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
            constant.PARAMETERS, {}).get("parameterDefinitions", {}).get("hudson.model.StringParameterDefinition", [])
        if StringParameterDefinition:
            print("StringParameterDefinition", StringParameterDefinition)
            if isinstance(StringParameterDefinition, list):
                string_parameter = StringParameterDefinition
            else:
                string_parameter = [StringParameterDefinition]
        else:
            string_parameter = list()
        ChoiceParameterDefinition = old_config.get(constant.FLOW_KEY, {}).get("properties", {}).get(
            constant.PARAMETERS, {}).get("parameterDefinitions", {}).get("hudson.model.ChoiceParameterDefinition", {})
        if ChoiceParameterDefinition:
            if isinstance(ChoiceParameterDefinition, list):
                choice_parameter = ChoiceParameterDefinition
            else:
                choice_parameter = [ChoiceParameterDefinition]
        else:
            choice_parameter = list()
        string_parameter_list, choice_parameter_list = self._parse_data(string_parameter, choice_parameter)

        data = {"string_parameter": string_parameter_list, "choice_parameter": choice_parameter_list}
        return data

    def _parse_data(self, string_parameter, choice_parameter):
        """解析源数据"""
        if isinstance(string_parameter, dict):
            string_parameter = [string_parameter]
        if isinstance(choice_parameter, dict):
            choice_parameter = [choice_parameter]

        string_parameter_list = list()
        print("string_parameter_list", string_parameter, type(string_parameter))
        for parameter in string_parameter:
            print("parameter", parameter)
            string_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "default_string": parameter.get("defaultValue")
            })

        choice_parameter_list = list()
        for parameter in choice_parameter:
            choices_string_list = parameter.get("choices", {}).get("a", {}).get("string", [])
            if isinstance(choices_string_list, str):
                choices_string_list = [choices_string_list]
            choice_parameter_list.append({
                "name": parameter.get("name"),
                "description": parameter.get("description"),
                "choices_string_list": choices_string_list
            })
        return string_parameter_list, choice_parameter_list

    def get_job_build(self, request):
        """
            同步指定流水线下的构建历史
        :param request:
        :return:
        """
        data = request.GET.dict()
        job_name = data.get("job_name")
        code = data.get("code", None)

        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        tool_query_dict = tool_query.link_tool_dict()

        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        application_name = application_query.get_model_code_name()

        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query,
                                                        jenkins_view_name=application_name)
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view_query)
        view_name = view_query.jenkins_view_name

        # 判断权限
        if user_query.role != 1:
            status = job_query.is_auth_log(user_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

        # 更新单条流水线数据
        if not ApplicationJenkinsJobBuildModel.fetch_one(building=True):
            ApplicationJenkinsJobBuildModel.objects.filter().update(is_celery=False)
        # jenkins_sync_job_v2(jenkins_api, application_name, job_query.job_name, job_query)
        # jenkins_sync_job_v1_celery.delay(tool_query_dict, view_name, job_query.job_name, job_query)
        # jenkins_sync_job_v1_celery(tool_query_dict, view_name, job_query.job_name, job_query)

        can_stop = True
        can_delete_log = True
        if user_query.role != 1:
            can_stop = job_query.is_auth_stop(user_query)
            can_delete_log = job_query.is_auth_delete_log(user_query)

        build_queryset1 = ApplicationJenkinsJobBuildModel.fetch_all(job=job_query, number__nin=[None]).order_by("-number")
        build_queryset2 = ApplicationJenkinsJobBuildModel.fetch_all(job=job_query, number=None).order_by("-created_at")
        build_list = [build_query.to_job_list_dict() for build_query in list(build_queryset2)+list(build_queryset1)[:10]]
        end_data = {
            "can_stop": can_stop,
            "can_delete_log": can_delete_log,
            "build_list": build_list
        }

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class JenkinsJobInput(BaseObject):
    def input_job(self, request):
        post_data = json.loads(request.body)
        # 操作类型-proceed：确认  abort：终止
        operation_type = post_data.get("operation_type", None)
        code = post_data.get("code")
        job_name = post_data.get("job_name")
        num = post_data.get("num")
        execution_log = post_data.get("execution_log")
        user_list = post_data.get("user_list")

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        try:
            tool_url = tool_query.api_addr
        except Exception as e:
            tool_url = None

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view_query)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.JOB_NOT_FOUNT, language=self.ops_language()))

        try:
            query_username = user_query.username
            if user_list:
                if query_username not in user_list:
                    return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message="没有权限执行此操作"))
            else:
                return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message="没有配置确认者"))

            # input_data = jenkins_api.get_build_pending_input_id(job_query.view.jenkins_view_name, job_name, num)
            # 获取阶段日志中的继续和终止地址
            proceed_abort_url_res = jenkins_api.get_build_stage_log_proceed_and_abort_info(execution_log)
            proceed_abort_url_list = proceed_abort_url_res.get("data")
            print("proceed_abort_url_list111111", execution_log, type(proceed_abort_url_list), proceed_abort_url_list)
            proceed_urls = [url for url in proceed_abort_url_list if url.endswith('proceedEmpty')]
            proceed_url = None
            if proceed_urls:
                proceed_url = proceed_urls[0]
            abort_urls = [url for url in proceed_abort_url_list if url.endswith('abort')]
            abort_url = None
            if abort_urls:
                abort_url = abort_urls[0]
            print("proceed_urls11111111", type(proceed_urls), proceed_urls, type(proceed_url), proceed_url)
            print("proceed_urls22222222", type(abort_urls), abort_urls, type(abort_url), abort_url)
            # 给人工确认发送消息通知表中增加一个状态来表示用户在页面上已经点击
            job_build_input_message_query = JobBuildInputMessageModel.fetch_one(job=job_query, number=num,
                                                                                links_log_href=execution_log)
            if operation_type == "proceed":
                res = jenkins_api.build_proceed_empty_v2(proceed_url, tool_url)
                proceed_status = res.get("status")
                if proceed_status:
                    # 操作审计：流程控制-继续执行构建
                    operation_audit_create_build_operation_log(user_query, job_query, 4, 7, "继续执行构建", {}, {},
                                                               str(num), execution_log)
                    if job_build_input_message_query:
                        job_build_input_message_query.update(stage_status="2")
                    return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))
                else:
                    return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message=res.get("message"),
                                              language=self.ops_language()))
            else:
                res = jenkins_api.build_abort_v2(abort_url, tool_url)
                abort_status = res.get("status")
                if abort_status:
                    # 操作审计：流程控制-终止执行构建
                    operation_audit_create_build_operation_log(user_query, job_query, 4, 8, "终止执行构建", {}, {},
                                                               str(num), execution_log)
                    if job_build_input_message_query:
                        job_build_input_message_query.update(stage_status="3")
                    return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))
                else:
                    return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message=res.get("message"),
                                              language=self.ops_language()))
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message=str(e), language=self.ops_language()))


class Users(BaseObject):
    def get_users_list(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))
        user_list = [i.to_base_dict() for i in UserInfo.fetch_all(is_activate__in=[True, None])]
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, user_list))


class JenkinsJobStages(BaseObject):
    def get_job_build_stages(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        kwargs = request.GET.dict()
        code = kwargs.get("code")
        job_name = kwargs.get("job_name")
        number = kwargs.get("number")

        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        application_name = application_query.get_model_code_name()
        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query, jenkins_view_name=application_name)
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view_query)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.JOB_NOT_FOUNT, language=self.ops_language()))
        build_query = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=number)
        if not build_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        end_data = {
                "opsany_data": build_query.to_job_list_dict(),
                "api_error_message": None
            }

        try:
            # 如果这个构建记录是在本平台执行的，获取这个脚本中的并行阶段
            job_build_number_query = JobBuildNumberScriptModel.fetch_one(job=job_query, number=number)
            parallel_names_dic = job_build_number_query.parallel_script
        except Exception as e:
            parallel_names_dic = {}

        try:
            res = jenkins_api.get_build_stage_info(job_name, number, application_name)
            if res.get("status"):
                build_stages = res.get("data")
            else:
                end_data["api_error_message"] = res.get("message")
                build_stages = {}

            try:
                if build_stages and parallel_names_dic:
                    for stage in build_stages["stages"]:
                        if "stageFlowNodes" not in stage or not stage["stageFlowNodes"]:
                            stage["parentid"] = None
                        else:
                            for parent_name, child_names in parallel_names_dic.items():
                                if stage["name"] in child_names:
                                    try:
                                        parent_stage = next(
                                            s for s in build_stages["stages"] if s["name"] == parent_name)
                                    except Exception as e:
                                        parent_stage = None
                                    stage["parentid"] = parent_stage["id"] if parent_stage else None
                                    break
            except Exception as e:
                end_data["api_error_message"] = str(e)
                pass

            end_data["build_stages"] = build_stages
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.MESSAGE_NOT_FIND, custom_message={}, language=self.ops_language()))


class JenkinsJobStageLogs(BaseObject):
    def get_job_stage_log(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        kwargs = request.GET.dict()
        execution_log_url = kwargs.get("execution_log_url")
        run_status = kwargs.get("PAUSED_PENDING_INPUT")
        job_code = kwargs.get("job_code")
        num = kwargs.get("number")
        if not execution_log_url or not job_code or not num:
            return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, "缺少必传参数", language=self.ops_language()))

        job_query = ApplicationJenkinsJobsModel.fetch_one(code=job_code)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.JOB_NOT_FOUNT, language=self.ops_language()))

        user_list = []
        try:
            input_submitters = []
            # 获取阶段日志中的input_id
            input_data = jenkins_api.get_build_stage_log_input_id_info(execution_log_url)
            input_id = input_data.get("data")
            input_id = input_id.upper()

            # 通过input_id获取等待人工确认步骤中的确认者
            input_submitter_query = JobBuildNumberScriptModel.fetch_one(job=job_query, number=num)
            if input_submitter_query and input_submitter_query.input_id_submitter_dic:
                input_id_submitter_dic = dict(input_submitter_query.input_id_submitter_dic)
                input_id_submitter_dic = {k.upper(): v for k, v in input_id_submitter_dic.items()}
                input_submitters = input_id_submitter_dic.get(input_id).split(",")

            if input_submitters:
                for i in input_submitters:
                    user_query_ = UserInfo.fetch_one(username=i)
                    user_list.append(user_query_.to_base_dict())
        except Exception as e:
            print("获取阶段日志报错Error：".format(str(e)))
            pass

        operation_log_query = OperationLogModel.fetch_one(execution_log=execution_log_url)

        end_data = {
            "operation_data": operation_log_query.to_dict() if operation_log_query else {},
            "submitter": user_list
        }

        try:
            res = jenkins_api.get_build_stage_log_info(execution_log_url)
            if res.get("status"):
                jenkins_data = res.get("data")
                if res.get("status") and run_status:
                    text = res.get("data").get("text")
                    result = text.split('\n')[0]
                    # import re
                    # text_before_newline = text.split('\n')[0]
                    # chinese_characters = re.findall(r'[\u4e00-\u9fff]', text_before_newline)
                    # result = ''.join(chinese_characters)
                    jenkins_data = result
            else:
                jenkins_data = {}
            end_data["jenkins_data"] = jenkins_data

            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, custom_message={}, language=self.ops_language()))


class JenkinsJobScript(BaseObject):
    def get_all_job_number_script(self, request):
        kwargs = request.GET.dict()
        search_type = kwargs.get("search_type")
        search_data = kwargs.get("search_data")

        dic = {}

        if search_type and search_data:
            dic[search_type + "__icontains"] = search_data
        try:
            queryset = JobBuildNumberScriptModel.fetch_all(**dic)
            if queryset:
                end_data = [i.to_dict() for i in queryset]
            else:
                end_data = []
        except Exception as e:
            end_data = []
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class JenkinsJobBuildingJob(BaseObject):
    def get_building_job(self, request):
        kwargs = request.GET.dict()
        search_type = kwargs.get("search_type")
        search_data = kwargs.get("search_data")
        delete_job = kwargs.get("delete_job", None)

        if delete_job:
            SyncBuildingJobModel.objects.filter(job_name=delete_job).delete()
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))
        dic = {}
        if search_type and search_data:
            dic[search_type + "__icontains"] = search_data
        try:
            queryset = SyncBuildingJobModel.fetch_all(**dic)
            if queryset:
                end_data = [i.to_dict() for i in queryset]
            else:
                end_data = []
        except Exception as e:
            end_data = []
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class JenkinsOverallJobs(BaseObject):
    def get_overall_jobs(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        dic = {}
        application_queryset = ApplicationModel.fetch_all()

        # 存放所有的应用-jenkins view（管理员）
        view_queryset = [
            ApplicationJenkinsModel.fetch_one(application=app) or ApplicationJenkinsModel.create(
                jenkins_view_name=app.get_model_code_name(),
                application=app
            )
            for app in application_queryset
        ]
        dic["view__in"] = view_queryset

        if user_query.role not in ["1", 1]:
            job_read_code_list, _, _ = user_query.get_code_list(application_queryset, id_type="job")
            dic["code__in"] = job_read_code_list[0]

        job_queryset = ApplicationJenkinsJobsModel.fetch_all(**dic)
        job_list = [job_query.to_dict() for job_query in job_queryset]

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, job_list, language=self.ops_language()))


class JenkinsOverallViews(BaseObject):
    def get_overall_views(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        kwargs = request.GET.dict()
        overall_view_code = kwargs.get("overall_view_code")
        search_type = kwargs.get("search_type")
        search_data = kwargs.get("search_data")
        page = int(kwargs.get("current", 1))
        per_page = int(kwargs.get("pageSize", 10))
        application_code = kwargs.get("application_code")
        dic = {}

        if search_type and search_data:
            dic[search_type + "__icontains"] = search_data
        if application_code:
            app_query = ApplicationModel.fetch_one(code=application_code)
            view_query = ApplicationJenkinsModel.fetch_one(application=app_query)
            dic["view"] = view_query

        if overall_view_code:
            overall_view_query = JenkinsJobOverAllViewModel.fetch_one(code=overall_view_code)
            if not overall_view_query:
                return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
            query_job_code_list = list(overall_view_query.job_code_list)
            dic["code__in"] = query_job_code_list

            application_queryset = ApplicationModel.fetch_all()
            job_read_code_list = []
            if user_query.role not in ["1", 1]:
                job_read_code_list, _, _ = user_query.get_code_list(application_queryset, id_type="job")
                job_code_list = list(set(query_job_code_list) & set(job_read_code_list[0]))
                dic["code__in"] = job_code_list

            jobs_queryset, total = ApplicationJenkinsJobsModel.pagination(page, per_page, **dic, order_by="-last_run_datetime")

            jobs_list = [job_query.to_tags_dict_v3(user_query, job_read_code_list) for job_query in jobs_queryset]

            end_data = {
                "current": page,
                "pageSize": per_page,
                "total": total,
                "data": jobs_list
            }
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        bind_queryset = JenkinsOverallViewUserModel.objects.filter(create_user=user_query).order_by("index")
        new_list = []
        have_list = []
        for i in bind_queryset:
            overall_view = i.overall_view
            if overall_view not in have_list:
                have_list.append(i.overall_view)
                new_list.append(i.overall_view.to_overall_view_dict(user_query))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, new_list, language=self.ops_language()))

    def create_overall_view(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        data = json.loads(request.body)
        overall_view_name = data.get("overall_view_name")
        data["overall_view_username"] = user_query.username

        if not data.get("overall_view_name") or not data.get("job_code_list"):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        job_overall_view_query = JenkinsJobOverAllViewModel.fetch_one(overall_view_name=overall_view_name)
        if job_overall_view_query:
            return JsonResponse(error(ErrorStatusCode.NAME_HAS_EXISTED_1, language=self.ops_language()))

        job_overall_view_query_ = JenkinsJobOverAllViewModel.create(**data)
        if job_overall_view_query_:
            JenkinsOverallViewUserModel.create(create_user=user_query, overall_view=job_overall_view_query_, index=100)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, language=self.ops_language()))

    def update_overall_view(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        data = json.loads(request.body)
        overall_view_type = data.get("overall_view_type")
        leading_add_code_list = data.get("add_code_list", [])
        leading_remove_code_list = data.get("remove_code_list", [])

        code = data.get("code")
        job_overall_view_query = JenkinsJobOverAllViewModel.fetch_one(code=code)
        if not job_overall_view_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        dic = {}
        application_queryset = ApplicationModel.fetch_all()

        # 存放所有的应用-jenkins view
        view_queryset = [
            ApplicationJenkinsModel.fetch_one(application=app) or ApplicationJenkinsModel.create(
                jenkins_view_name=app.get_model_code_name(),
                application=app
            )
            for app in application_queryset
        ]
        dic["view__in"] = view_queryset
        if user_query.role not in ["1", 1]:
            job_read_code_list, _, _ = user_query.get_code_list(application_queryset, id_type="job")
            dic["code__in"] = job_read_code_list[0]
        job_queryset = ApplicationJenkinsJobsModel.fetch_all(**dic)
        # 有权访问的流水线code
        job_strategy_code_list = [i.code for i in job_queryset]
        job_strategy_code_set = set(job_strategy_code_list)

        # 现有的流水线code
        now_code_mongo_base_list = job_overall_view_query.job_code_list
        now_code_list = list(now_code_mongo_base_list) if now_code_mongo_base_list else []

        # 视图新增的流水线
        add_code_list = [leading_add_code for leading_add_code in leading_add_code_list if
                         leading_add_code in job_strategy_code_set]
        # 视图去除的流水线
        remove_code_list = [leading_remove_code for leading_remove_code in leading_remove_code_list if
                         leading_remove_code in job_strategy_code_set]

        result_job_code_list = list(set(now_code_list + add_code_list) - set(remove_code_list))
        data["job_code_list"] = result_job_code_list

        # 当把别人创建的视图设置成私有时，提示没有权限
        if overall_view_type == "2" and user_query.username != job_overall_view_query.overall_view_username:
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, custom_message="没有权限将此视图设置为私有",
                                      language=self.ops_language()))
        job_overall_view_query.update(**data)

        if overall_view_type == "2" and job_overall_view_query.overall_view_type == "2":
            overall_view_user_queryset = JenkinsOverallViewUserModel.fetch_all(overall_view=job_overall_view_query,
                                                                               create_user__ne=user_query)
            if overall_view_user_queryset:
                overall_view_user_queryset.delete()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, language=self.ops_language()))

    def delete_overall_view(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        data = json.loads(request.body)

        code = data.get("code")

        job_overall_view_query = JenkinsJobOverAllViewModel.fetch_one(code=code)
        if not job_overall_view_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        job_overall_view_query.delete()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))


class JenkinsOverallView(BaseObject):
    def get_overall_view(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        kwargs = request.GET.dict()
        code = kwargs.get("code")
        query = JenkinsJobOverAllViewModel.fetch_one(code=code)
        if not query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, query.to_dict(), language=self.ops_language()))


class JenkinsOverallViewsV2(BaseObject):
    def get_overall_view_v2(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        public_queryset = JenkinsJobOverAllViewModel.fetch_all(overall_view_type="1")
        self_queryset = JenkinsJobOverAllViewModel.fetch_all(overall_view_username=user_query.username,
                                                             overall_view_type="2")
        query_list = list(public_queryset) + list(self_queryset)
        bind_queryset = JenkinsOverallViewUserModel.objects.filter(create_user=user_query).order_by("index")
        if not bind_queryset:
            # 当用户有面板时，默认要开启一个
            if query_list:
                overall_view_query = query_list[0]
                JenkinsOverallViewUserModel.create(create_user=user_query, overall_view=overall_view_query, index=2)

        bind_list = list(set([i.overall_view for i in JenkinsOverallViewUserModel.fetch_all(create_user=user_query)]))
        public_list = self._clean_panel_inst_list(public_queryset, user_query, bind_list)
        self_list = self._clean_panel_inst_list(self_queryset, user_query, bind_list)
        end_data = [
            {"group_name": "公开视图", "description": "用户创建的视图，所有人可见。", "children": public_list},
            {"group_name": "私有视图", "description": "用户创建的视图，仅创建人可见。", "children": self_list}
        ]
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

    def _clean_panel_inst_list(self, queryset, user_query, bind_list):
        new_bind_list = []
        null_bind_list = []
        for i in queryset:
            dic = i.to_config_dict(user_query)
            if i in bind_list:
                dic["bind"] = True
                new_bind_list.append(dic)
            else:
                null_bind_list.append(dic)
        return new_bind_list + null_bind_list

    def update_overall_view_v2(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        data = json.loads(request.body)
        data_type = data.get("data_type")
        code = data.get("code")
        overall_view_list = data.get("overall_view_list")
        overall_view_query = None
        if code:
            overall_view_query = JenkinsJobOverAllViewModel.fetch_one(code=code)
            if not overall_view_query:
                return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        # 启用禁用
        if data_type == "enable":
            query = JenkinsOverallViewUserModel.fetch_one(create_user=user_query, overall_view=overall_view_query)
            if not query:
                end_index = JenkinsOverallViewUserModel.objects.filter(
                    create_user=user_query).order_by("-index").first()
                if not end_index:
                    index = 1
                else:
                    index = end_index.index or 10
                query = JenkinsOverallViewUserModel.create(create_user=user_query, overall_view=overall_view_query,
                                                           index=index+1)
            else:
                query.delete()

        # 排序
        if data_type == "index":
            index = 1
            for i in overall_view_list:
                overall_view_query_ = JenkinsJobOverAllViewModel.fetch_one(code=i)
                if not overall_view_query_:
                    continue
                query = JenkinsOverallViewUserModel.fetch_one(create_user=user_query, overall_view=overall_view_query_)
                if query:
                    query.update(index=index)
                    index += 1

        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))


class RefreshPipelines(BaseObject):
    def refresh_application_pipelines(self, request):
        try:
            data = json.loads(request.body)
            # res = self.refresh_application_pipelines_(data)
            # print("refresh_application_pipelines", res)
        except Exception as e:
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, str(e), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, time.time(), language=self.ops_language()))

    def refresh_application_pipelines_(self, data):
        code = data.get("code", None)
        business_code = data.get("business_code", None)
        all_data = data.get("all_data", False)
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return "Jenkins服务器权限错误，请确认配置！"

        query = SyncBuildingJobModel.fetch_one()
        if not query:
            SyncBuildingJobModel.create(status="1")

        # 创建jenkins连接
        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

        # 全部流水线
        if code or business_code or all_data:
            print(f"同步正在执行的流水线(全部数据)")
            view_name_list = []  # 存放所有应用的code
            application_queryset = ApplicationModel.fetch_all()

            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(),
                          "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_name_list.append(view_query.jenkins_view_name)

            for view_name in view_name_list:
                view_query_ = ApplicationJenkinsModel.fetch_one(jenkins_view_name=view_name)
                result_all_jobs = jenkins_api.get_folder_info(name=view_name)
                if not result_all_jobs.get("status"):
                    continue
                all_job = result_all_jobs.get("data", {}).get("jobs")
                if not all_job:
                    continue

                # 当前应用下正在执行的流水线
                building_jobs = [job.get("name") for job in all_job if "anime" in job.get("color")]

                for job_name in building_jobs:
                    sync_building_job_query = SyncBuildingJobModel.fetch_one(view=view_query_, job_name=job_name)
                    if sync_building_job_query and sync_building_job_query.status == "2":
                        continue
                    if not sync_building_job_query:
                        sync_building_job_query = SyncBuildingJobModel.create(view=view_query_, job_name=job_name, status="1")
                    res = sync_application_pipelines.delay(jenkins_api, view_query_, view_name, job_name, sync_building_job_query)


class RefreshJenkinsJob(BaseObject):
    def refresh_jenkins_jobs(self, request):
        try:
            data = json.loads(request.body)
            # 同步流水线（全部、应用分组下、应用下）
            # res = self.refresh_jenkins_jobs_(data)
            # print("refresh_jenkins_jobs", res)
        except Exception as e:
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, str(e), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, time.time(), language=self.ops_language()))

    def refresh_jenkins_jobs_(self, data):
        code = data.get("code", None)
        business_code = data.get("business_code", None)
        all_data = data.get("all_data", False)
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return "Jenkins服务器权限错误，请确认配置！"

        # 初始化一个记录
        query = RefreshJobModel.fetch_one()
        if not query:
            RefreshJobModel.create(status="1")

        # 创建jenkins连接
        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

        # 判断是否有正在执行的流水线
        # building_status = judge_building_job(jenkins_api)
        # if building_status:
        #     return True

        # 应用
        if code:
            application_query = ApplicationModel.fetch_one(code=code)
            if not application_query:
                return "应用不存在"
            view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
            if not view_query:
                application_name = application_query.get_model_code_name()
                dt = {"application": application_query, "jenkins_view_name": application_name}
                view_query = ApplicationJenkinsModel.create(**dt)
            view_name = view_query.jenkins_view_name
            result_all_jobs = jenkins_api.get_folder_info(name=view_name)
            if not result_all_jobs.get("status"):
                return "获取视图信息错误"
            all_job = result_all_jobs.get("data", {}).get("jobs")
            if not all_job:
                return "流水线不存在"

            building_jobs = [job.get("name") for job in all_job]

            for job_name in building_jobs:
                job_query = ApplicationJenkinsJobsModel.fetch_one(view=view_query, job_name=job_name)
                if job_query:
                    refresh_job_query = RefreshJobModel.fetch_one(view=view_query, job=job_query)
                    if refresh_job_query:
                        continue
                    else:
                        refresh_job_query = RefreshJobModel.create(view=view_query, job=job_query, status="1")
                    res = refresh_pipeline_jobs.delay(jenkins_api, view_query, view_name, job_name, all_job,
                                                      refresh_job_query)

        # 应用分组
        if business_code:
            business_query = BusinessModel.fetch_one(code=business_code)
            view_name_list = []  # 存放当前应用分组下所有应用的code
            application_queryset = ApplicationModel.fetch_all(business=business_query)

            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(),
                          "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_name_list.append(view_query.jenkins_view_name)

            for view_name in view_name_list:
                view_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=view_name)
                result_all_jobs = jenkins_api.get_folder_info(name=view_name)
                if not result_all_jobs.get("status"):
                    continue
                all_job = result_all_jobs.get("data", {}).get("jobs")
                if not all_job:
                    continue

                building_jobs = [job.get("name") for job in all_job]

                for job_name in building_jobs:
                    job_query = ApplicationJenkinsJobsModel.fetch_one(view=view_query, job_name=job_name)
                    if job_query:
                        refresh_job_query = RefreshJobModel.fetch_one(view=view_query, job=job_query)
                        if refresh_job_query:
                            continue
                        else:
                            refresh_job_query = RefreshJobModel.create(view=view_query, job=job_query, status="1")
                        res = refresh_pipeline_jobs.delay(jenkins_api, view_query, view_name, job_name, all_job,
                                                          refresh_job_query)

        # 全部流水线
        if all_data:
            view_name_list = []  # 存放所有应用的code
            application_queryset = ApplicationModel.fetch_all()

            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(),
                          "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_name_list.append(view_query.jenkins_view_name)

            for view_name in view_name_list:
                view_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=view_name)
                result_all_jobs = jenkins_api.get_folder_info(name=view_name)
                if not result_all_jobs.get("status"):
                    continue
                all_job = result_all_jobs.get("data", {}).get("jobs")
                if not all_job:
                    continue

                building_jobs = [job.get("name") for job in all_job]

                for job_name in building_jobs:
                    job_query = ApplicationJenkinsJobsModel.fetch_one(view=view_query, job_name=job_name)
                    if job_query:
                        refresh_job_query = RefreshJobModel.fetch_one(view=view_query, job=job_query)
                        if refresh_job_query:
                            continue
                        else:
                            refresh_job_query = RefreshJobModel.create(view=view_query, job=job_query, status="1")
                        res = refresh_pipeline_jobs.delay(jenkins_api, view_query, view_name, job_name, all_job,
                                                          refresh_job_query)


class CheckQueue(BaseObject):
    def check_pipeline_queue(self, request):
        """获取流水线状态"""
        data = request.GET.dict()
        code = data.get("code", None)
        application = ApplicationModel.fetch_one(code=code)
        if not code or not application:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        is_building = False
        app_view = ApplicationJenkinsModel.fetch_one(application=application)
        if app_view:
            view_name = app_view.jenkins_view_name
        else:
            return JsonResponse(
                success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        get_queue_info = jenkins_api.get_folder_info(view_name)
        if get_queue_info.get("status"):
            job_list = get_queue_info.get("data", {}).get("jobs")
            if job_list and isinstance(job_list, list):
                for job in job_list:
                    # red_anime  blue_anime
                    if "anime" in job.get("color"):
                        is_building = True
                        break
        else:
            is_building = False
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building, language=self.ops_language()))

    def check_pipeline_queue_rebuilt(self, request):
        """获取流水线状态"""
        data = request.GET.dict()
        code = data.get("code", None)
        business_code = data.get("business_code", None)
        all_data = data.get("all_data", None)

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 应用
        if code:
            application = ApplicationModel.fetch_one(code=code)
            if not code or not application:
                return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
            is_building = False
            app_view = ApplicationJenkinsModel.fetch_one(application=application)
            if app_view:
                view_name = app_view.jenkins_view_name
            else:
                return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building,
                                            language=self.ops_language()))

            get_queue_info = jenkins_api.get_folder_info(view_name)
            if get_queue_info.get("status"):
                job_list = get_queue_info.get("data", {}).get("jobs")
                if job_list and isinstance(job_list, list):
                    for job in job_list:
                        # red_anime  blue_anime
                        if "anime" in job.get("color"):
                            is_building = True
                            break
            else:
                is_building = False
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building,
                                        language=self.ops_language()))
        # 应用分组
        if business_code:
            is_building = False
            business_query = BusinessModel.fetch_one(code=business_code)
            view_name_list = []     # 存放当前应用分组下所有应用的code
            application_queryset = ApplicationModel.fetch_all(business=business_query)

            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(),
                          "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_name_list.append(view_query.jenkins_view_name)

            found_building_pipeline = False  # 控制外层循环

            for view_name in view_name_list:
                # 当发现有正在构建的任务，就退出循环
                if found_building_pipeline:
                    break
                get_queue_info = jenkins_api.get_folder_info(view_name)
                if get_queue_info.get("status"):
                    job_list = get_queue_info.get("data", {}).get("jobs")
                    if job_list and isinstance(job_list, list):
                        for job in job_list:
                            if "anime" in job.get("color"):
                                is_building = True
                                found_building_pipeline = True
                                break
                else:
                    is_building = False
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building,
                                        language=self.ops_language()))
        # 全部数据
        if all_data:
            is_building = False
            view_name_list = []     # 存放所有的应用name
            application_queryset = ApplicationModel.fetch_all()

            for application_query in application_queryset:
                view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
                if not view_query:
                    dt = {"jenkins_view_name": application_query.get_model_code_name(),
                          "application": application_query}
                    view_query = ApplicationJenkinsModel.create(**dt)
                view_name_list.append(view_query.jenkins_view_name)

            found_building_pipeline = False  # 控制外层循环

            for view_name in view_name_list:
                # 当发现有正在构建的任务，就退出循环
                if found_building_pipeline:
                    break
                get_queue_info = jenkins_api.get_folder_info(view_name)
                if get_queue_info.get("status"):
                    job_list = get_queue_info.get("data", {}).get("jobs")
                    if job_list and isinstance(job_list, list):
                        for job in job_list:
                            if "anime" in job.get("color"):
                                is_building = True
                                found_building_pipeline = True
                                break
                else:
                    is_building = False
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building,
                                        language=self.ops_language()))


class GitlabRepositoryUrl(BaseObject):
    def get_gitlab_repository_urls(self, request):
        try:
            start = time.time()
            tool_query = ToolsModel.fetch_one(tool_type="jenkins")
            if not tool_query:
                return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
            if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
                return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

            # 创建jenkins连接
            jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

            user_query = GetUserInfo().get_user_info(request)
            if not user_query:
                return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

            try:
                esb = EsbApi(request.COOKIES.get("bk_token"))
                res = esb.get_gitlab_repository_url()
            except Exception as e:
                res = {}

            if res.get("result"):
                access_token_value = res.get("data", {}).get("access_token")
                if not access_token_value:
                    pass

                # 创建一个私有凭据
                import uuid
                private_credential_params = {
                    "credentials_id": str(uuid.uuid4()) + "-gitlab-access-key",
                    "description": None,
                    "secret": access_token_value
                }
                name = f"{user_query.username}代码仓库私有凭据"
                credentials_id = private_credential_params.get("credentials_id")

                credentials_query = JenkinsCredentialsModel.fetch_one(name=name)
                if credentials_query:
                    update_params = {
                        "credentials_id": credentials_query.credentials_id,
                        "description": credentials_query.description,
                        "secret": access_token_value
                    }
                    data = jenkins_api.update_credentials(credentials_query.credentials_id, params=update_params, type=6)
                    if data.get("status"):
                        credentials_query.update(access_token_value=access_token_value, is_private="1")
                        # 判断当前用户是否有代码仓库私有凭据，没有就进行关联
                        user_credentials_query = UserJenkinsCredentialsModel.fetch_one(user=user_query)
                        if not user_credentials_query:
                            UserJenkinsCredentialsModel.create(user=user_query, jenkins_credentials=credentials_query)
                        else:
                            user_credentials_query.update(
                                **{"user": user_query, "jenkins_credentials": credentials_query})
                        # 同步凭据
                        jenkins_sync_credentials()
                    else:
                        print(f"修改凭据{credentials_query.credentials_id}失败：", data.get("message"))
                        # return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, language=self.ops_language()))
                else:
                    data = jenkins_api.create_credentials(params=private_credential_params, type=6)
                    if data.get("status"):
                        credentials_query_ = JenkinsCredentialsModel.create(name=name, is_private="1",
                                                                            credentials_id=credentials_id,
                                                                            access_token_value=access_token_value)
                        # 判断当前用户是否有代码仓库私有凭据，没有就进行关联
                        user_credentials_query = UserJenkinsCredentialsModel.fetch_one(user=user_query)
                        if not user_credentials_query:
                            UserJenkinsCredentialsModel.create(user=user_query,
                                                               jenkins_credentials=credentials_query_)
                        else:
                            user_credentials_query.update(
                                **{"user": user_query, "jenkins_credentials": credentials_query_})
                    # 同步凭据
                    jenkins_sync_credentials()

                end = time.time()
                print("获取自己参与的项目且成员角色大于开发者的项目地址列表耗时：", end - start)

                return JsonResponse(
                    success(SuccessStatusCode.MESSAGE_GET_SUCCESS, res.get("data", {}).get("project_list"),
                            language=self.ops_language()))
            else:
                return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, custom_message=res.get("message"),
                                          language=self.ops_language()))
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))


class NexusRepository(BaseObject):
    def get_nexus_repository(self, request):
        start = time.time()
        esb = EsbApi(request.COOKIES.get("bk_token"))
        kwargs = request.GET.dict()
        code = kwargs.get("code")
        format_type = kwargs.get("format_type")
        res = esb.get_nexus_repository_esb(code, format_type)
        if res.get("result"):
            end = time.time()
            print("获取应用或公共应用下的raw制品耗时：", end - start)
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, res.get("data"),
                                        language=self.ops_language()))
        else:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, custom_message=res.get("message"),
                                      language=self.ops_language()))


class NexusRepositoryVersion(BaseObject):
    def get_nexus_version(self, request):
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="repository")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.NEXUS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.NEXUS_SERVER_ERROR, language=self.ops_language()))

        tool_address = tool_query.api_addr
        tool_username = tool_query.username
        tool_password = tool_query.api_token

        nexus_version = self._get_nexus_version(tool_address, tool_username, tool_password)

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, nexus_version, language=self.ops_language()))

    def _get_nexus_version(self, nexus_url, username, password):
        try:
            nexus2_status_url = f"{nexus_url}/nexus/service/local/status"
            nexus3_status_url = f"{nexus_url}/service/rest/v1/status"

            response = requests.get(nexus3_status_url, auth=HTTPBasicAuth(username, password), timeout=5)

            if response.status_code == 200:
                return "Nexus 3"

            response = requests.get(nexus2_status_url, auth=HTTPBasicAuth(username, password), timeout=5)

            if response.status_code == 200:
                return "Nexus 2"

            return "Unknown Nexus version or invalid credentials"
        except Exception as e:
            return str(e)


class NexusCredential(BaseObject):
    def create_or_update_nexus_credential(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        tool_dict = tool_query.link_tool_dict()

        # 创建一个Nexus存储库凭据
        import uuid
        credentials_id = str(uuid.uuid4()) + "-nexus-credential"
        description = "这是Nexus制品库凭据。"
        username = tool_dict.get("username")
        password = tool_dict.get("password")
        nexus_dict = {
            "credentials_id": credentials_id,
            "description": description,
            "username": username,
            "password": password
        }
        name = "OpsAny制品仓库Nexus凭据"

        credentials_query = JenkinsCredentialsModel.fetch_one(credentials_type="1", name=name)

        if credentials_query:
            update_params = {
                "credentials_id": credentials_query.credentials_id,
                "description": credentials_query.description,
                "username": username,
                "password": password
            }
            data = jenkins_api.update_credentials(credentials_query.credentials_id, params=update_params, type=0)
            if data.get("status"):
                credentials_query.update(**update_params)
                # 同步凭据
                jenkins_sync_credentials()
            else:
                print(f"修改凭据{name}失败：", data.get("message"))
        else:
            data = jenkins_api.create_credentials(params=nexus_dict, type=0)
            if data.get("status"):
                create_nexus_dict = {
                    "name": name,
                    "credentials_id": credentials_id,
                    "username": username,
                    "credentials_type": "1"
                }
                credentials_query = JenkinsCredentialsModel.create(**create_nexus_dict)
            # 同步凭据
            jenkins_sync_credentials()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, language=self.ops_language()))


# 操作审计
class OperationAduit(BaseObject):
    def get_operation_aduit(self, request):
        data = request.GET.dict()
        page = int(data.get("current", 1))
        per_page = int(data.get("pageSize", 10))

        search_type = data.get("search_type", None)
        search_data = data.get("search_data", None)
        operation_type = data.get("operation_type", None)

        filter_dict = {"operation_type__nin": [4]}
        if search_type and search_data:
            filter_dict[search_type + "__icontains"] = search_data

        if operation_type:
            filter_dict["operation_type"] = operation_type

        current_page, total = OperationLogModel.pagination(page, per_page, **filter_dict)

        log_list = [log_query.to_dict() for log_query in current_page]

        end_data = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "data": log_list
        }

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class OperationLog(BaseObject):
    def get_operation_log(self, request):
        data = request.GET.dict()
        log_code = data.get("log_code")

        log_query = OperationLogModel.fetch_one(code=log_code)

        if not log_query:
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, log_query.to_detail_dict(),
                                    language=self.ops_language()))
