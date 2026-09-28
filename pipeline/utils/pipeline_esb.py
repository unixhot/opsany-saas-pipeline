from datetime import datetime as datetime1, timedelta
import json
import time

from django.http import JsonResponse

from component.base_views import BaseObject
from pipeline.utils import constant
from pipeline.celery_task import celery_build_num_and_run_username
from component.libs import GetUserInfo
from component.status_code import success, SuccessStatusCode, error, ErrorStatusCode
from pipeline.utils.jenkins_api import JenkinsApi
from pipeline.utils.libs import xml_dict, extract_input_arguments, extract_input_arguments_2
from pipeline.models import ApplicationJenkinsModel, ApplicationJenkinsJobsModel, ToolsModel, ApplicationModel, \
    ApplicationJenkinsJobBuildModel


class JenkinsJobBuild(BaseObject):
    def _build_start(self, post_data, user_query):
        run_type = post_data.get("run_type", "click")
        if run_type == "click":
            req_source = post_data.get("run_type", "页面执行")
            app_from = post_data.get("app_from", "devops")
            code = post_data.get("code")
            name = post_data.get("name")
            app_query = ApplicationModel.fetch_one(code=code)
        elif run_type == "api":
            req_source = post_data.get("req_source", "API调用")
            app_from = post_data.get("app_from", "workbench")
            application_name = post_data.get("application_name")
            name = post_data.get("job_name")
            app_query = ApplicationModel.fetch_one(data__APPLICATION_name=application_name)
        else:
            return JsonResponse(error(ErrorStatusCode.NO_PARAMS, language=self.ops_language()))
        
        parameters = post_data.get("parameters") or {}
        try:
            if isinstance(parameters, str):
                parameters = json.loads(parameters)
        except Exception as e:
            pass

        if not app_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))
        view = ApplicationJenkinsModel.fetch_one(application=app_query)
        if not view:
            dic = {"application": app_query, "jenkins_view_name": app_query.get_model_code_name}
            view = ApplicationJenkinsModel.create(**dic)
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
        job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=name, view=view)
        if not job_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
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

        queue_num = None
        result_job_build = jenkins_api.build_job(name, parameters=parameters, folder_name=view_name)
        if result_job_build.get("status"):
            queue_num = result_job_build.get("data")
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
            "app_from": app_from
        }
        log_query = ApplicationJenkinsJobBuildModel.create(**dt)

        job_dict = {
            "last_run_username": user_query.username,
            "last_run_ch_name": user_query.ch_name,
            "last_run_req_source": req_source,
            "last_run_app_from": app_from
        }
        job_query.update(**job_dict)
        celery_build_num_and_run_username.delay(job_query, view_name, jenkins_api, user_query, log_query=log_query,
                                                parallel_names=parallel_names,
                                                input_id_submitter_dic=input_id_submitter_dic, app_code=app_query.code)
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

    def build_start_esb_v1(self, request):
        """
        application_name: 应用平台唯一标识
        job_name： 流水线名称
        parameters： 执行参数（当流水线配置参数时，执行前需要传入参数）
        {
            "application_name": "",
            "job_name": "",
        }
        """
        data = json.loads(request.body)
        application_name = data.get("application_name")
        job_name = data.get("job_name")
        if not all([application_name, job_name]):
            message = "参数错误, 应用唯一标识(application_name)和流水线名称(job_name)为必传字段!"
            return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message=message))
        user_query = GetUserInfo().get_user_info_from_esb_username(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO))
        data["run_type"] = "api"
        data["username"] = user_query.username
        return self._build_start(data, user_query)

    def build_start_esb_v2(self, request):
        """
        [
            "app_name1==>job_name1",
            "app_name2==>job_name2",
        ]
        """
        data = json.loads(request.body)
        user_query = GetUserInfo().get_user_info_from_esb_username(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO))
        data_list = data.get("data_list", [])
        app_deploy_list = []
        for d in data_list:
            if "==>" not in d:
                continue
            app_deploy = d.split("==>")
            if len(app_deploy) != 2:
                continue
            app_deploy_list.append(
                {"application_name": app_deploy[0], "job_name": app_deploy[0], "run_type": "api",
                 "username": user_query.username}
            )
        for job_data in app_deploy_list:
            self._build_start(job_data, user_query)
        return JsonResponse(success(SuccessStatusCode.JOB_BUILD_SUCCESS))

    def build_start_esb_v3(self, request):
        """
        ESB，内部调用
        application_name: OpsAny
        job_name: job_name
        req_source: API
        parameters: {}
        """
        data = json.loads(request.body)
        print("11111111111111111111111111111", data)
        user_query = GetUserInfo().get_user_info_from_esb_username(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO))
        application_name = data.get("application_name")
        job_name = data.get("job_name")
        if not all([application_name, job_name]):
            message = "参数错误, 应用唯一标识(application_name)和流水线名称(job_name)为必传字段!"
            return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message=message))
        data["run_type"] = "api"
        data["username"] = user_query.username
        return self._build_start(data, user_query)
    
    def build_start_esb_rollback(self, request):
        data = request.GET.dict()
        queue_num = data.get("queue_num")
        if not queue_num:
            return JsonResponse(error(ErrorStatusCode.NO_PARAMS))
        query = ApplicationJenkinsJobBuildModel.fetch_one(queue_num=queue_num)
        if not query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, query.to_workbench_rollback_dict()))

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


class GetHomePage(BaseObject):
    def get_home_page(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))

        kwargs = request.GET.dict()
        code = kwargs.get("code")
        app_query = ApplicationModel.fetch_one(code=code)
        if not app_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        job_filter_dic = {}
        if user_query.role != 1:
            status = user_query.is_app_auth(app_query)
            if not status:
                return JsonResponse(error(ErrorStatusCode.USER_NOT_POWER, language=self.ops_language()))

            job_read_code_list, _, _ = user_query.get_code_list(app_query, id_type="job")
            job_filter_dic["code__in"] = job_read_code_list[0]

        view_query = ApplicationJenkinsModel.fetch_one(application=app_query)
        # 当前应用下所有的流水线
        jobs_queryset = ApplicationJenkinsJobsModel.fetch_all(view=view_query, **job_filter_dic)

        # 流水线数量
        pipeline_count = ApplicationJenkinsJobsModel.counter(view=view_query, **job_filter_dic)

        # 近七天执行成功的次数
        seven_days_task_success_count = 0
        # 近七天执行失败的次数
        seven_days_task_error_count = 0

        # 获取今天的日期
        now_date = datetime1.now().date()
        seven_days_ago = now_date - timedelta(days=6)

        # 所有流水线的构建历史
        job_log_queryset = ApplicationJenkinsJobBuildModel.fetch_all(job__in=jobs_queryset)

        for job_log_query in job_log_queryset:
            if job_log_query.created_at.date() >= seven_days_ago:
                if job_log_query.result == "SUCCESS":
                    seven_days_task_success_count += 1
                else:
                    seven_days_task_error_count += 1

        # 近七天执行次数
        seven_days_task_count = seven_days_task_success_count + seven_days_task_error_count

        # 近七天执行成功状态趋势
        daily_success_counts = []
        # 近七天执行失败状态趋势
        daily_error_counts = []

        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            daily_success_counts.append({"date": date, "success_count": 0})
            daily_error_counts.append({"date": date, "error_count": 0})

        # 最近七天流水线构建历史
        job_log_queryset_seven_days = ApplicationJenkinsJobBuildModel.fetch_all(job__in=jobs_queryset,
                                                                                created_at__gte=seven_days_ago)

        for job_log_queryset_seven_day in job_log_queryset_seven_days:
            job_log_date = job_log_queryset_seven_day.created_at.date()
            if seven_days_ago <= job_log_date <= now_date:
                index = (job_log_date - seven_days_ago).days
                if job_log_queryset_seven_day.result == "SUCCESS":
                    daily_success_counts[index]["success_count"] += 1
                else:
                    daily_error_counts[index]["error_count"] += 1

        end_data = {
            "pipeline_count": pipeline_count,
            "seven_days_task_count": seven_days_task_count,
            "seven_days_task_status": {
                "seven_days_task_success_count": seven_days_task_success_count,
                "seven_days_task_error_count": seven_days_task_error_count
            },
            "daily_success_counts": daily_success_counts,
            "daily_error_counts": daily_error_counts
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


# 获取当前应用下的流水线
class GetPipelineJenkinsJob(BaseObject):
    def get_pipeline_jenkins_job(self, request):
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))
        kwargs = request.GET.dict()
        search_type = kwargs.get("search_type", None)
        search_data = kwargs.get("search_data", None)

        try:
            page = int(kwargs.get("current"))
            per_page = int(kwargs.get("pageSize"))
        except:
            page = 1
            per_page = 10

        code = kwargs.get("code", None)
        application_query = ApplicationModel.fetch_one(code=code)
        if not application_query:
            return JsonResponse(error(ErrorStatusCode.APPLICATION_NOT_EXISTED, language=self.ops_language()))

        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED_V2, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        if user_query.role not in [1]:
            status = user_query.is_app_auth(application_query)
            if not status:
                return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, {}, language=self.ops_language()))
        application_name = application_query.get_model_code_name()

        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            view_query = ApplicationJenkinsModel.create(application=application_query,
                                                        jenkins_view_name=application_name)

        filter_dict = {"view": view_query}
        if search_type and search_data:
            filter_dict[search_type + "__icontains"] = search_data

        job_read_code_list = []
        if user_query.role != 1:
            job_read_code_list, _, _ = user_query.get_code_list(application_query, id_type="job")
            filter_dict["code__in"] = job_read_code_list[0]

        jobs_queryset, total = ApplicationJenkinsJobsModel.pagination(page, per_page, order_by="-last_run_datetime",
                                                                      **filter_dict)

        job_list = [job.to_devops_dict_v2(user_query, job_read_code_list) for job in jobs_queryset]

        end_data = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "data": job_list
        }

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))
