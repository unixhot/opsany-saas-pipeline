import json
from itertools import chain
import mongoengine
from django.http import JsonResponse
from django.views import View
from component.base_views import BaseView
from pipeline.decorator import admin_auth
from pipeline.utils.batch_create_script import BatchCreateScript, TestV2
from pipeline.utils.credentials import JenkinsCredentials, JenkinsCredentialsType
from pipeline.utils.gitlab_api import GitLabApi
from pipeline.utils.pipeline import JenkinsJob, JenkinsJobBuild, JenkinsJobReconfigScript, JenkinsJobTriggers, \
    JenkinsJobParameters, OperationAduit, OperationLog, GitlabRepositoryUrl, NexusRepository, NexusRepositoryVersion, \
    NexusCredential, RefreshPipelines, JenkinsJobRebuilt, CheckQueue, RefreshJenkinsJob, JenkinsOverallViews, \
    JenkinsOverallJobs, JenkinsOverallView, JenkinsOverallViewsV2, PipelineGroup, PipelineOverallView, JenkinsJobInput, \
    Users, JenkinsJobStages, JenkinsJobStageLogs, JenkinsJobScript, JenkinsJobBuildingJob
from component.status_code import success, SuccessStatusCode, ErrorStatusCode, error
from pipeline.models import *
from pipeline.utils import constant
from pipeline.utils.jenkins_api import JenkinsApi, flash_all_tool_status
from pipeline.utils.filter_data import filter_build_info_data
from pipeline.utils.libs import xml_dict, pipeline_tool_list
from pipeline.utils.pipeline_template import PipelineTemplateGroup, PipelineTemplate


class TestView(BaseView):
    def get(self, request):
        return BatchCreateScript(request).batch_create_jobs(request)


class TestV2View(BaseView):
    def get(self, request):
        return TestV2(request).get_test(request)


class BatchImportPipelineView(BaseView):
    def post(self, request):
        return BatchCreateScript(request).batch_create_jobs(request)


class JenkinsCredentialsTypeView(View):
    def get(self, request):
        return JenkinsCredentialsType(request).get_credentials_type(request)


class JenkinsCredentialsView(View):
    def get(self, request):
        return JenkinsCredentials(request).get_credentials(request)

    def post(self, request):
        # 新建凭据
        return JenkinsCredentials(request).create_credentials(request)

    def put(self, request):
        # 修改凭据
        return JenkinsCredentials(request).update_credentials(request)

    def delete(self, request):
        return JenkinsCredentials(request).delete_credentials(request)


class JenkinsJobListView(BaseView):
    def get_old(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 获取全部job(包含当前构建历史)
        result = jenkins_api.get_all_jobs()
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, result.get("data"),
                                    language=self.ops_language()))

    def get(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        view_queryset = ApplicationJenkinsModel.fetch_all()
        view_name_initial_list = [view_query.jenkins_view_name for view_query in view_queryset]
        view_name_lower_list = [name.lower() for name in view_name_initial_list]
        view_name_list = view_name_initial_list + view_name_lower_list

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 获取全部job(包含当前构建历史)
        result = jenkins_api.get_all_jobs()
        job_dic = result.get("data")
        jobs_list = []
        for i in job_dic:
            if i.get("_class") == "com.cloudbees.hudson.plugins.folder.Folder" and i.get("name") in view_name_list:
                jobs = i.get("jobs")
                if jobs:
                    jobs_list.extend(jobs)

        all_job = []
        for job in jobs_list:
            job_name = job.get("name")
            jenkins_job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
            try:
                application = jenkins_job_query.view.application.get_rebuild_dict()
            except Exception as e:
                application = {}
                print("获取应用信息Error：", str(e))
            if jenkins_job_query:
                dt = {
                    "name": job_name,
                    "fullname": job.get("fullname"),
                    "application": application
                }
                all_job.append(dt)

        # 本地存在，Jenkins上不存在的job
        opsany_jobs = [i.job_name for i in ApplicationJenkinsJobsModel.fetch_all()]
        jenkins_jobs = [i.get("name") for i in all_job]
        opsany_difference_jenkins_jobs = []
        for i in opsany_jobs:
            if i not in jenkins_jobs:
                opsany_difference_jenkins_jobs.append(i)

        end_data = {
            "views": {"total": len(view_name_initial_list), "view_list": view_name_initial_list},
            "jobs": {"total": len(all_job), "job_list": all_job},
            "opsany_difference_jenkins_jobs":
                {"total": len(opsany_difference_jenkins_jobs), "job_list": opsany_difference_jenkins_jobs}
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class JenkinsJobView(View):
    def get(self, request):
        """获取流水线列表"""
        # return JenkinsJob().get_job(request)
        return JenkinsJob(request).get_job_v2(request)

    def post(self, request):
        return JenkinsJob(request).create_job(request)

    def delete(self, request):
        return JenkinsJob(request).delete_job(request)


class PipelineGroupView(View):
    def get(self, request):
        return PipelineGroup(request).get_pipeline_groups(request)


class PipelineOverallViewView(View):
    def get(self, request):
        return PipelineOverallView(request).get_pipeline_overall_views(request)


class JenkinsJobRebuiltView(View):
    def get(self, request):
        return JenkinsJobRebuilt(request).get_jenkins_job_v2(request)


class JenkinsJobBuildView(View):
    def get(self, request):
        return JenkinsJobBuild(request).get_job_build(request)


class RefreshPipelinesView(View):
    def post(self, request):
        return RefreshPipelines(request).refresh_application_pipelines(request)


class RefreshJenkinsJobView(View):
    def post(self, request):
        return RefreshJenkinsJob(request).refresh_jenkins_jobs(request)


class CheckQueueView(View):
    def get(self, request):
        return CheckQueue(request).check_pipeline_queue_rebuilt(request)


class CheckQueueInternalView(BaseView):
    def get(self, request):
        data = request.GET.dict()
        code = data.get("code", None)
        job_name = data.get("job_name")
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
        get_queue_info = jenkins_api.get_job_info(job_name, view_name)
        if get_queue_info.get("status"):
            color = get_queue_info.get("data", {}).get("color")
            if "anime" in color:
                is_building = True
        else:
            is_building = False
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, is_building, language=self.ops_language()))


# # jenkins 流水线--修改配置--脚本修改
class JenkinsJobReconfigScriptView(View):
    def get(self, request):
        """获取流水线列表"""
        return JenkinsJobReconfigScript(request).get_pipeline_script(request)

    def put(self, request):
        """修改流水线"""
        return JenkinsJobReconfigScript(request).update_pipeline_script(request)


# jenkins 检查语法
class JenkinsCheckPipelineView(View):
    def post(self, request):
        return JenkinsJobReconfigScript(request).check_pipeline_script_syntax(request)


# jenkins pipeline script 转 json
class JenkinsFileToJsonView(View):
    def post(self, request):
        return JenkinsJobReconfigScript(request).pipeline_script_jenkinsfile_to_json(request)


# jenkins json转 pipeline script
class JenkinsToJenkinsFileView(BaseView):
    def post(self, request):
        return JenkinsJobReconfigScript().pipeline_script_json_to_jenkinsfile(request)


# jenkins 流水线 -- 修改配置--触发构建，定时触发，其他工程触发，gitlab触发
class JenkinsJobReconfigTriggersView(View):
    def get(self, request):
        return JenkinsJobTriggers(request).get_triggers_config(request)

    def put(self, request):
        return JenkinsJobTriggers(request).update_triggers_config(request)


class JenkinsJobTagsView(View):
    def put(self, request):
        return JenkinsJob(request).tags_job(request)


# jenkins 流水线 -- 修改配置--构建参数
class JenkinsJobParametersView(View):
    def get(self, request):
        return JenkinsJobParameters(request).get_parameters(request)

    def put(self, request):
        return JenkinsJobParameters(request).update_parameters(request)


# 获取构建记录状态
class JenkinsJobBuildStatusView(BaseView):
    def get(self, request):
        data = request.GET.dict()
        job_name = data.get("job_name", None)
        print("job_name", job_name)
        status_li = {"ABORTED": "计划终止", "SUCCESS": "计划成功", "FAILURE": "计划失败", None: "..."}
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, status_li, language=self.ops_language()))


# jenkins 获取配置相关模板
class JenkinsPipelineToolView(BaseView):
    def get(self, request):
        exclude_list = ["上传到制品库", "上传普通文件"]
        pipeline_tool_queryset = PipelineToolModel.fetch_all(tool_name__nin=exclude_list)
        pipeline_tool = [pipeline_tool_query.to_dict() for pipeline_tool_query in pipeline_tool_queryset]
        result = pipeline_tool_list(pipeline_tool)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, result, language=self.ops_language()))

    def post(self, request):
        try:
            print(request.body)
            post_data = json.loads(request.body)

            print("post_data", post_data)
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, str(e), language=self.ops_language()))
        tool_name = post_data.get("tool_name")
        tool_type = post_data.get("tool_type")
        name = post_data.get("name")
        arguments = post_data.get("arguments")
        if not isinstance(arguments, list):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, "arguments list error",
                                      language=self.ops_language()))
        for argument in arguments:
            argument_keys = argument.keys()
            print("argument_keys", argument_keys)
            if ("key" not in argument_keys) and ("value" in argument_keys) and ("is_literal" in argument_keys):
                return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, "arguments key error",
                                          language=self.ops_language()))

        if not all([tool_name, tool_type, name, arguments]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, "missing parameter",
                                      language=self.ops_language()))
        dt = {
            "tool_name": tool_name,
            "tool_type": tool_type,
            "name": name,
            "arguments": arguments
        }
        if PipelineToolModel.fetch_one(tool_name=tool_name):
            return JsonResponse(error(ErrorStatusCode.RECORD_HAS_EXISTED, language=self.ops_language()))
        print("dt", dt)
        pipeline = PipelineToolModel.create(**dt)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline.to_dict(),
                                    language=self.ops_language()))


class JenkinsPipelineToolPostView(BaseView):
    def get(self, request):
        pipeline_tool_post_queryset = PipelineToolPostModel.fetch_all()
        pipeline_tool_post = [pipeline_tool_query.to_dict() for pipeline_tool_query in pipeline_tool_post_queryset]
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline_tool_post,
                                    language=self.ops_language()))

    def post(self, request):
        try:
            print(request.body)
            post_data = json.loads(request.body)

            print("post_data", post_data)
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, str(e), language=self.ops_language()))
        ch_name = post_data.get("ch_name")
        condition = post_data.get("condition")
        name = post_data.get("name")
        description = post_data.get("description")
        if not all([ch_name, condition, name, description]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        dt = {
            "ch_name": ch_name,
            "condition": condition,
            "name": name,
            "description": description
        }
        if PipelineToolPostModel.fetch_one(ch_name=ch_name):
            return JsonResponse(error(ErrorStatusCode.RECORD_HAS_EXISTED, language=self.ops_language()))
        if PipelineToolPostModel.fetch_one(condition=condition):
            return JsonResponse(error(ErrorStatusCode.RECORD_HAS_EXISTED, language=self.ops_language()))
        print("dt", dt)
        pipeline = PipelineToolPostModel.create(**dt)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline.to_dict(),
                                    language=self.ops_language()))


# jenkins 流水线 -- 修改描述
class JenkinsJobDescriptionView(View):
    def get(self, request):
        return JenkinsJob(request).get_description(request)

    def put(self, request):
        return JenkinsJob(request).update_description(request)


# jenkins 流水线 -- 修改名称
class JenkinsJobRenameView(View):
    def get(self, request):
        return JenkinsJob(request).get_job_name_and_discard_strategy(request)

    def put(self, request):
        return JenkinsJob(request).update_job_name_and__discard_strategy(request)


# 触发构建--参数列表
class TriggerBuildParamsView(View):
    def get(self, request):
        return JenkinsJobBuild(request).get_build_params(request)


# jenkins 流水线 -- 构建历史信息-单条
class JenkinsJobBuildInfoView(View):
    def get(self, request):
        return JenkinsJobBuild(request).get_build_info(request)


class JenkinsJobInputView(View):
    def post(self, request):
        return JenkinsJobInput(request).input_job(request)


class UsersView(View):
    def get(self, request):
        return Users(request).get_users_list(request)


class JenkinsJobStagesView(View):
    def get(self, request):
        return JenkinsJobStages(request).get_job_build_stages(request)


class JenkinsJobStageLogsView(View):
    def get(self, request):
        return JenkinsJobStageLogs(request).get_job_stage_log(request)


class JenkinsJobScriptView(View):
    def get(self, request):
        return JenkinsJobScript(request).get_all_job_number_script(request)


class JenkinsJobBuildingJobView(View):
    def get(self, request):
        return JenkinsJobBuildingJob(request).get_building_job(request)


class JenkinsOverallJobsView(View):
    def get(self, request):
        return JenkinsOverallJobs(request).get_overall_jobs(request)


# 全局视图
class JenkinsOverallViewsView(View):
    def get(self, request):
        return JenkinsOverallViews(request).get_overall_views(request)

    def post(self, request):
        return JenkinsOverallViews(request).create_overall_view(request)

    def put(self, request):
        return JenkinsOverallViews(request).update_overall_view(request)

    def delete(self, request):
        return JenkinsOverallViews(request).delete_overall_view(request)


class JenkinsOverallViewView(View):
    def get(self, request):
        return JenkinsOverallView(request).get_overall_view(request)


class JenkinsOverallViewsV2View(View):
    def get(self, request):
        return JenkinsOverallViewsV2(request).get_overall_view_v2(request)

    def put(self, request):
        return JenkinsOverallViewsV2(request).update_overall_view_v2(request)


# 开始构建
class JenkinsJobBuildStartView(View):
    def post(self, request):
        return JenkinsJobBuild(request).build_start(request)


# 人工确认-终止
class JenkinsJobBuildAbortView(View):
    def post(self, request):
        return JenkinsJobBuild(request).build_abort(request)


# 人工确认-继续
class JenkinsJobBuildProceedEmptyView(View):
    def post(self, request):
        return JenkinsJobBuild(request).build_proceed(request)


# 停止构建
class JenkinsJobBuildStopView(View):
    def put(self, request):
        return JenkinsJobBuild(request).build_stop(request)


# 删除构建
class JenkinsJobBuildDeleteView(View):
    def delete(self, request):
        return JenkinsJobBuild(request).build_delete(request)


# 流水线配置模板分组
class PipelineTemplateGroupView(View):
    def get(self, request):
        return PipelineTemplateGroup(request).get_template_group(request)

    def post(self, request):
        return PipelineTemplateGroup(request).create_template_group(request)

    def put(self, request):
        return PipelineTemplateGroup(request).update_template_group(request)

    def delete(self, request):
        return PipelineTemplateGroup(request).delete_template_group(request)


# 流水线配置模板
class PipelineTemplateView(View):
    def get(self, request):
        return PipelineTemplate(request).get_template(request)

    def post(self, request):
        return PipelineTemplate(request).create_template(request)

    def put(self, request):
        return PipelineTemplate(request).update_template(request)

    def delete(self, request):
        return PipelineTemplate(request).delete_template(request)


# 复制流水线模板
class CopyPipelineTemplateView(View):
    def post(self, request):
        return PipelineTemplate(request).copy_template(request)


class JenkinsRefreshView(BaseView):
    def get(self, request):
        data = request.GET.dict()
        job_name = data.get("job_name", None)
        code = data.get("code", None)
        application_query = ApplicationModel.fetch_one(code=code)
        jenkins_view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not jenkins_view_query:
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, [], language=self.ops_language()))
        jenkins_view_name = jenkins_view_query.get_jenkins_view_name()
        # print("application_name", application_name)
        application_name = jenkins_view_name

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())

        # 获取全部job(包含当前构建历史)
        result = jenkins_api.get_jobs(view_name=application_name)
        if not result.get("status"):
            return JsonResponse(error(*result.get("message"), language=self.ops_language()))
        all_job = result.get("data")

        # 没有流水线报错
        if not all_job:
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, [], language=self.ops_language()))

        # 首次获取列表默认没有job_name默认使用第一条
        if all_job and (not job_name):
            job_name = all_job[0].get("name", "")
            print(job_name)

        # 获取全部流水线和相关构建日志
        for job in all_job:
            job.pop("_class", "")
            job.pop("url", "")

            # 获取单条任务详情
            job_name_from_all_job = job.get("name")
            result = jenkins_api.get_job_info(job_name_from_all_job, folder_name=application_name)
            if not result.get("status"):
                return JsonResponse(error(*result.get("message"), language=self.ops_language()))
            job_info = result.get("data")
            # print("job_info__job_info", job_info)

            job_info_builds_list = job_info.get("builds", [])

            if job_info_builds_list:
                number = job_info_builds_list[0].get("number")
                result = jenkins_api.get_build_info(name=job_name_from_all_job, number=number,
                                                    folder_name=jenkins_view_name)
                if not result:
                    return JsonResponse(error(*result.get("message"), language=self.ops_language()))
                job_build_info = result.get("data")
                job["timestamp"] = job_build_info.get("timestamp", 0)
                job["result"] = job_build_info.get("result", "")

            # 获取当条任务构建历史
            build_list = list()
            if job_name_from_all_job == job_name:
                for build in job_info_builds_list[:10]:
                    num = build.get("number")
                    # print("job_name_from_all_job_num", num, job_name_from_all_job, build)
                    result = jenkins_api.get_build_info(name=job_name_from_all_job, number=num,
                                                        folder_name=jenkins_view_name)
                    # print("result", result)
                    if not result.get("status"):
                        return JsonResponse(error(*result.get("message"), language=self.ops_language()))
                    build_info = result.get("data")
                    # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
                    result_dic = filter_build_info_data(build_info)
                    # 添加筛选后的数据
                    build_list.append(result_dic)
                job["build_list"] = build_list

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, all_job, language=self.ops_language()))


class JenkinsJobsView(BaseView):
    def get(self, request):
        data = request.GET.dict()
        view_name = data.get("view_name")
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
        get_jobs_result = jenkins_api.get_jobs(view_name=view_name)
        if not get_jobs_result.get("status"):
            return JsonResponse(error(*get_jobs_result.get("message"), language=self.ops_language()))
        print("get_jobs_result", get_jobs_result)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, get_jobs_result.get("data"),
                                    language=self.ops_language()))

    def post(self, request):
        data = json.loads(request.body)
        view_name = data.get("view_name")

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
        get_jobs_result = jenkins_api.create_folder(name=view_name)
        print("get_jobs_result", get_jobs_result)
        if not get_jobs_result.get("status"):
            return JsonResponse(error(*get_jobs_result.get("message"), language=self.ops_language()))
        print("get_jobs_result", get_jobs_result)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, get_jobs_result.get("data"),
                                    language=self.ops_language()))


class ToolView(BaseView):
    @admin_auth
    def get(self, request, **kwargs):
        tool_jenkins_queryset = ToolsModel.fetch_all(tool_type="jenkins")
        tool_git_queryset = ToolsModel.fetch_all(tool_type="git")
        tool_queryset = list(chain(tool_jenkins_queryset, tool_git_queryset))
        end_data = []
        if tool_queryset:
            for i in tool_queryset:
                end_data.append(i.to_dict())
        data = {
            "data": end_data
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

    @admin_auth
    def post(self, request, **kwargs):
        try:
            post_data = json.loads(request.body)
            tool_type = post_data.get("tool_type")
            tool_dict = {
                "tool_name": post_data.get("tool_name"),
                "tool_type": post_data.get("tool_type"),
                "api_addr": post_data.get("api_addr"),
                "username": post_data.get("username"),
                "api_token": post_data.get("api_token"),
                "description": post_data.get("description")
            }
            api_dict = {
                "url": post_data.get("api_addr"),
                "username": post_data.get("username"),
                "password": post_data.get("api_token"),
            }

            git_dict = {
                "url": post_data.get("api_addr"),
                "oauth_token": post_data.get("api_token")
            }
            if not all([tool_dict["tool_name"],tool_dict["api_token"], tool_dict["tool_type"], tool_dict["api_addr"]]):
                return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
            # 工具类唯一
            tool_obj_type = ToolsModel.fetch_one(tool_type=tool_dict.get("tool_type"))
            if tool_obj_type:
                return JsonResponse(error(ErrorStatusCode.TOOL_HAS_EXISTED, language=self.ops_language()))
            # 工具名称唯一
            tool_obj_name = ToolsModel.fetch_one(tool_type=tool_type, tool_name=tool_dict.get("tool_name"))
            if tool_obj_name:
                return JsonResponse(error(ErrorStatusCode.TOOL_NAME_HAS_EXISTED, language=self.ops_language()))
            # Jenkins
            if tool_dict["tool_type"] == "jenkins":
                jenkins_api = JenkinsApi(request, **api_dict)
                status = jenkins_api.jenkins_status()
                if status:
                    self.create_jenkins_folder(jenkins_api)
            # GItLab
            elif tool_dict["tool_type"] == "git":
                gitlab_api = GitLabApi(**git_dict)
                status = gitlab_api.status()
            # Nexus
            # elif tool_dict["tool_type"] == "repository":
            #     status = NexusApi(request, **api_dict).status()
            # SonarQube
            elif post_data.get("tool_type") == "SonarQube":
                status = ErrorStatusCode.TOOL_CONNECTION_ERROR, "error"
            else:
                raise Exception("tool type error")
            if status is True:
                tool_dict["link_status"] = constant.TOOL_LINK_STATUS_SUCCESS
                tool_obj = ToolsModel.create(**tool_dict)
                if tool_obj.tool_type == "jenkins":
                    message = "Jenkins服务配置成功，使用Jenkins需要依赖插件：{}，请到插件管理检查是否已安装。".format(
                        ", ".join(constant.JENKINS_REQUIRED_PLUGIN))
                    return JsonResponse(
                        {"code": 200, "successcode": 20001, "message": message, "data": tool_obj.to_dict()})
                return JsonResponse(
                    success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, tool_obj.to_dict(), language=self.ops_language()))
            else:
                print("状态连接失败", status)
                return JsonResponse(error(*status, language=self.ops_language()))
        except Exception as e:
            print(e)
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, str(e), language=self.ops_language()))

    @admin_auth
    def put(self, request, **kwargs):
        post_data = json.loads(request.body)
        code = post_data.get("code")
        try:
            if code:
                tool_dict = dict()
                tool_type = post_data.get("tool_type")
                if post_data.get("tool_name"):
                    tool_dict["tool_name"] = post_data.get("tool_name")
                if post_data.get("tool_type"):
                    tool_dict["tool_type"] = post_data.get("tool_type")
                if post_data.get("api_addr"):
                    tool_dict["api_addr"] = post_data.get("api_addr")
                if post_data.get("username"):
                    tool_dict["username"] = post_data.get("username")
                if post_data.get("api_token"):
                    tool_dict["api_token"] = post_data.get("api_token")
                tool_dict["description"] = post_data.get("description")

                # 参数是否完整
                if not all([tool_dict["tool_name"], tool_dict["tool_type"], tool_dict["api_addr"]]):
                    return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

                # 数据是否存在
                tool_obj_id = ToolsModel.fetch_one(code=code)
                if not tool_obj_id:
                    return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

                # 工具类唯一
                tool_name_unique = ToolsModel.check_field_unique(code, "tool_type", tool_dict.get("tool_type"))
                if not tool_name_unique:
                    return JsonResponse(error(ErrorStatusCode.TOOL_NAME_HAS_EXISTED, language=self.ops_language()))

                # 工具名称唯一
                tool_name_query = ToolsModel.fetch_one(tool_type=tool_type, tool_name=tool_dict.get("tool_name"))
                if tool_name_query:
                    if tool_name_query != tool_obj_id:
                        return JsonResponse(error(ErrorStatusCode.TOOL_NAME_HAS_EXISTED, language=self.ops_language()))
                # tool_name_unique = ToolsModel.check_field_unique(code, "tool_name", tool_dict.get("tool_name"))
                # if not tool_name_unique:
                #     return JsonResponse(error(ErrorStatusCode.TOOL_NAME_HAS_EXISTED, language=self.ops_language()))

                api_dict = {
                    "url": post_data.get("api_addr"),
                    "username": post_data.get("username"),
                    "password": post_data.get("api_token"),
                }

                git_dict = {
                    "url": post_data.get("api_addr"),
                    "oauth_token": post_data.get("api_token")
                }
                # jenkins
                if post_data.get("tool_type") == "jenkins":
                    jenkins_api = JenkinsApi(request, **api_dict)
                    status = jenkins_api.jenkins_status()
                    if status:
                        self.create_jenkins_folder(jenkins_api)
                # GItLab
                elif post_data["tool_type"] == "git":
                    gitlab_api = GitLabApi(**git_dict)
                    status = gitlab_api.status()
                # Nexus
                # elif tool_dict["tool_type"] == "repository":
                #     status = NexusApi(request, **api_dict).status()
                # SonarQube
                elif post_data.get("tool_type") == "SonarQube":
                    status = ErrorStatusCode.TOOL_CONNECTION_ERROR, "error"
                else:
                    raise Exception("tool type error")
                if status == True:
                    tool_dict["link_status"] = constant.TOOL_LINK_STATUS_SUCCESS
                    tool_obj = tool_obj_id.update(**tool_dict)
                    if tool_obj.tool_type == "jenkins":
                        message = "Jenkins服务配置成功，使用Jenkins需要依赖插件：{}，请到插件管理检查是否已安装。".format(
                            ", ".join(constant.JENKINS_REQUIRED_PLUGIN))
                        return JsonResponse(
                            {"code": 200, "successcode": 20004, "message": message, "data": tool_obj.to_dict()})

                    return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, tool_obj.to_dict(),
                                                language=self.ops_language()))
                else:
                    return JsonResponse(error(*status, language=self.ops_language()))
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        except mongoengine.errors.NotUniqueError as e:
            print("mongoengine.errors.NotUniqueError", e)
            return JsonResponse(error(ErrorStatusCode.TOOL_NAME_HAS_EXISTED, language=self.ops_language()))
        except Exception as e:
            print(e)
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, str(e), language=self.ops_language()))

    @admin_auth
    def delete(self, request, **kwargs):
        delete_data = json.loads(request.body)
        code = delete_data.get("code")
        print("delete_data", delete_data)
        try:
            if code:
                tool_obj = ToolsModel.fetch_one(code=code)
                if not tool_obj:
                    return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
                if tool_obj.tool_type == "jenkins":
                    app_jenkins_query = ApplicationJenkinsJobsModel.fetch_one()
                    if app_jenkins_query:
                        return JsonResponse(error(ErrorStatusCode.INST_HAS_JENKINS, language=self.ops_language()))
                if tool_obj.tool_type == "git":
                    quoted_times = tool_obj.quoted_times
                    if quoted_times and quoted_times != 0:
                        return JsonResponse(error(ErrorStatusCode.INST_HAS_GITLAB, language=self.ops_language()))
                # if tool_obj.tool_type == "repository":
                #     app_repo_queryset = ApplicationRepoModel.fetch_all()
                #     if app_repo_queryset:
                #         return JsonResponse(error(ErrorStatusCode.INST_HAS_NEXUS, language=self.ops_language()))
                tool_obj.delete()
                return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        except Exception as e:
            print(e)
            return JsonResponse(error(ErrorStatusCode.SERVER_ERROR, e, language=self.ops_language()))

    def create_jenkins_folder(self, jenkins_api):
        """当增加或修改Jenkins工具时，主动创建以应用唯一标识为名的Jenkins目录，且创建本地关联关系"""
        app_queryset = ApplicationModel.fetch_all()
        for app in app_queryset:
            dt = {"application": app}
            app_name = app.get_model_code_name()
            if not ApplicationJenkinsModel.fetch_one(**dt):
                ApplicationJenkinsModel.create(jenkins_view_name=app_name, **dt)
            jenkins_api.create_folder(app_name)


# 刷新全部工具状态
class ToolStatusView(BaseView):
    def get(self, request, **kwargs):
        tool_code = request.GET.get("tool_code")
        if tool_code:
            tool_queryset = ToolsModel.fetch_all(code=tool_code)
        else:
            tool_queryset = ToolsModel.fetch_all()
        status = flash_all_tool_status(request, tool_queryset)
        return JsonResponse(success(SuccessStatusCode.REFRESH_STATUS_SUCCESS, "成功：{}，失败：{}".format(*status),
                                    language=self.ops_language()))


class ToolTestJenkinsView(BaseView):
    def post(self, request, **kwargs):
        data = json.loads(request.body)
        tool_url = data.get("tool_url")
        tool_username = data.get("tool_username")
        tool_password = data.get("tool_password")

        if not all([tool_url, tool_username, tool_password]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        try:
            jenkins_api = JenkinsApi(url=tool_url, username=tool_username, password=tool_password)
            status = jenkins_api.jenkins_status()

            if status == True:
                end_data = {
                    "data": "连接测试成功",
                    "status": 1
                }
                return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, end_data,
                                            language=self.ops_language()))
            else:
                end_data = {
                    "data": "连接测试失败",
                    "status": 2
                }
                return JsonResponse(error(*status, language=self.ops_language()))
                # return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, end_data, language=self.ops_language()))
        except Exception as e:
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, errors=str(e), language=self.ops_language()))


class ToolTestGitView(BaseView):
    def post(self, request, **kwargs):
        data = json.loads(request.body)
        tool_url = data.get("tool_url")
        tool_username = data.get("tool_username")
        oauth_token = data.get("oauth_token")

        if not all([tool_url, oauth_token]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        try:
            git_api = GitLabApi(url=tool_url, oauth_token=oauth_token)
            status = git_api.status()
            if status == True:
                end_data = {
                    "data": "连接测试成功",
                    "status": 1
                }
                return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, end_data,
                                            language=self.ops_language()))
            else:
                end_data = {
                    "data": "连接测试失败",
                    "status": 2
                }
                return JsonResponse(error(*status, language=self.ops_language()))
        except Exception as e:
            end_data = {
                "data": str(e),
                "status": 2
            }
            return JsonResponse(error(ErrorStatusCode.TOOL_CONNECTION_ERROR, language=self.ops_language()))


class GitlabRepositoryUrlView(BaseView):
    def get(self, request):
        return GitlabRepositoryUrl().get_gitlab_repository_urls(request)


class NexusRepositoryView(BaseView):
    def get(self, request):
        return NexusRepository().get_nexus_repository(request)


class NexusRepositoryVersionView(BaseView):
    def get(self, request):
        return NexusRepositoryVersion().get_nexus_version(request)


class NexusCredentialView(BaseView):
    def get(self, request):
        return NexusCredential().create_or_update_nexus_credential(request)


# 操作审计
class OperationAduitView(View):
    def get(self, request):
        return OperationAduit().get_operation_aduit(request)


class OperationLogView(View):
    def get(self, request):
        return OperationLog().get_operation_log(request)
