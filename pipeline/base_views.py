import json
import datetime
import time

from django.http import JsonResponse
from djcelery.models import IntervalSchedule
from djcelery.schedulers import DatabaseScheduler

from component import return_message
from component.base_views import BaseView, BaseObject
from component.libs import GetUserInfo
from component.status_code import success, SuccessStatusCode, error, ErrorStatusCode
from pipeline.models import UserInfo, BusinessModel, ApplicationModel, ApplicationJenkinsJobsModel, \
    ApplicationJenkinsModel, PipelineTemplateModel, ApplicationJenkinsJobBuildModel, ToolsModel, \
    AutoSyncJenkinsDataModel
from component.esb_api import EsbApi
from pipeline.utils import constant
from pipeline.utils.sync_data import jenkins_sync_data_two, jenkins_sync_build


class DeployMenuStrategyCtrl(BaseView):
    def get(self, request):
        """ 获取当前平台使用者的菜单列表 """
        token = request.COOKIES.get("bk_token")
        esb_obj = EsbApi(token, language=self.ops_language())
        res_data = esb_obj.get_user_menu()  # 调用ESB接口获取到当前用户的在资源平台的菜单列表
        return JsonResponse(success(SuccessStatusCode.MENU_GET_SUCCESS, res_data[0] if res_data else {},
                                    language=self.ops_language()))


class GuideCtrl(BaseView):
    def get(self, request):
        """ 获取当前平台使用指南"""
        token = request.COOKIES.get("bk_token")
        platform_code = request.GET.get("platform_code", "")
        if not platform_code:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        esb_obj = EsbApi(token)
        res_data = esb_obj.guide(platform_code)
        return JsonResponse(res_data, safe=False)


# 获取当前用户信息
class GetUserInfoCtrl(BaseView):
    def get(self, request):
        """
        获取当前用户信息
        """
        token = request.COOKIES.get("bk_token")
        username = request.COOKIES.get("bk_token_username")

        user_query = UserInfo.objects.filter(username=username).first()
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        data = user_query.to_user_info_dict()
        language_theme_config = EsbApi(token, language=self.ops_language()).get_language_theme_config(username)
        data.update(language_theme_config)

        # token = request.COOKIES.get("bk_token")
        # bk_user = EsbApi(token).get_user_info_from_workbench_or_login()  # 获取当前用户
        # data = {
        #     "phone": bk_user.get("phone"),
        #     "username": bk_user.get("username"),
        #     "email": bk_user.get("email"),
        #     "ch_name": bk_user.get("ch_name"),
        #     "role": bk_user.get("role"),
        #     "icon_url": bk_user.get("icon_url"),
        # }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))


class GetNavCollectionView(BaseView):
    def get(self, request):
        token = request.COOKIES.get("bk_token")
        language = self.ops_language()
        end_data = EsbApi(token, language).get_nav_and_collection()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=language))


class CollectionNavView(BaseView):
    def post(self, request):
        token = request.COOKIES.get("bk_token")
        language = self.ops_language()
        data = json.loads(request.body)
        nav_id = data.get("nav_id")
        end_data = EsbApi(token, language).collection_nav(nav_id)
        if not isinstance(end_data, dict):
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, language=language))
        successcode = end_data.pop("api_code")
        res_dict = {
            "code": 200,
            "successcode": successcode,
            "message": end_data.get("message"),
            "data": end_data.get("data")
        }
        return JsonResponse(res_dict)


class GetUserMessageView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        page = int(kwargs.pop("current", 1))
        per_page = int(kwargs.pop("pageSize", 10))
        token = request.COOKIES.get("bk_token")
        language = self.ops_language()
        data = EsbApi(token, language).get_user_message_info(page, per_page)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=language))


class ReadAllMessageView(BaseView):
    def get(self, request):
        bk_token = request.COOKIES.get("bk_token")
        language = self.ops_language()
        EsbApi(bk_token, language).read_all_message()
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, language=language))


class CopyrightConfigView(BaseView):
    def get(self, request):
        """
        底部版权信息
        :param request:
        :return:
        {
            "code": 200,
            "successcode": 20005,
            "message": "相关信息信息获取成功",
            "data": {
                "content": "Copyright © 2019-2021 OpsAny. All Rights Reserved",
                "id": 1
            }
        }
        """
        token = request.COOKIES.get("bk_token")
        language = self.ops_language()
        end_data = EsbApi(token, language).get_copyright_config()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=language))


class UserView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        dic = dict()
        all_data = kwargs.pop("all_data", None)
        search_type = kwargs.pop("search_type", None)
        search_data = kwargs.pop("search_data", None)
        dic["role__in"] = [0, 2, 3]
        if search_type and search_data:
            search_type__contains = search_type + "__contains"
            dic[search_type__contains] = search_data

        if all_data:
            business_queryset = UserInfo.fetch_all(**dic)
            end_data = []
            if business_queryset:
                for i in business_queryset:
                    end_data.append(i.to_code_dict())
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

        try:
            current = int(kwargs.pop("current"))
            pageSize = int(kwargs.pop("pageSize"))
        except Exception:
            current = 1
            pageSize = 10

        current_page, total = UserInfo.pagination(current, pageSize, **dic)
        end_data = []
        if current_page:
            for i in current_page:
                end_data.append(i.to_code_dict())
        data = {
            "current": current,
            "pageSize": pageSize,
            "total": total,
            "data": end_data
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))


class BusinessTreeView(BaseView):
    def get(self, request):
        return BusinessTree(request).get_business_application_list(request)


class BusinessTreeV2View(BaseView):
    def get(self, request):
        return BusinessTreeV2(request).get_business_application_list_v2(request)


class GetHostInstView(BaseView):
    def get(self, request):
        return GetHostInst(request).get_host_inst()


class FlashDataView(BaseView):
    def post(self, request):
        try:
            res = jenkins_sync_data_two()
        except Exception as e:
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, str(e), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, time.time(), language=self.ops_language()))


class SyncCronTaskView(BaseView):
    def get(self, request):
        query = AutoSyncJenkinsDataModel.fetch_one()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, query.to_dict(), language=self.ops_language()))


class UpdateCronTaskView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        print("kwargs", type(kwargs), kwargs)
        minute = int(kwargs.get("minute", 5))
        enable = True if kwargs.get("enable", True) else False
        print("enable", type(enable), enable)
        query = AutoSyncJenkinsDataModel.fetch_one(name="定时任务")
        if not query:
            query = AutoSyncJenkinsDataModel.create(
                name="定时任务",
                minute=minute,
                enable=enable
            )
        query.update(minute=minute, enable=enable)

        interval_obj, created = IntervalSchedule.objects.get_or_create(
            every=query.minute * 60,
            period="seconds",
        )
        create_or_update_task = DatabaseScheduler.create_or_update_task
        schedule_dict = {
            "crontab": None,
            "schedule": interval_obj.schedule,
            "args": [],
            "kwargs": {},
            "task": "pipeline.celery_task.jenkins_sync_data",
            "enabled": query.enable,
            "description": ""
        }
        crontab_task_name = "{}".format("celery.jenkins_sync_data")
        create_or_update_task(crontab_task_name, **schedule_dict)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, query.to_dict(), language=self.ops_language()))


class FlashDataBuildView(BaseView):
    def post(self, request):
        try:
            res = jenkins_sync_build(request)
        except Exception as e:
            return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, str(e), language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.OPERATION_SUCCESS, time.time(), language=self.ops_language()))


class GetHostGroupView(BaseView):
    def get(self, request):
        return GetHostInst(request).get_host_group()


class BusinessTree(BaseObject):
    def get_business_application_list(self, request):
        user_query = GetUserInfo().get_user_info(request)
        business_tree_list = self._get_business_tree(user_query=user_query)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, business_tree_list,
                                    language=self.ops_language()))

    def _get_business_tree(self, user_query=None):
        if not user_query:
            return False, return_message.USER_NOT_EXISTED_MESSAGE
        business_queryset = BusinessModel.fetch_all()
        return [business_query.to_tree_dict(user_query=user_query) for business_query in business_queryset]

    def _business_application_list(self, bk_token):
        business_tree_list = self._business_tree(bk_token)
        for business_tree in business_tree_list:
            app_list = business_tree.get("children", [])
            if app_list:
                for app in app_list:
                    if "children" in app.keys():
                        del app["children"]
        return business_tree_list

    def _check_application_exist(self, bk_token, app_name):
        if app_name in self._application_list(bk_token=bk_token, data_type="app_name_list"):
            return True
        else:
            return False

    def _application_list(self, bk_token, data_type="app_list"):
        business_tree_list = self._business_tree(bk_token)
        app_list = []
        app_name_list = []
        for business_tree in business_tree_list:
            application_list = business_tree.get("children", [])
            if application_list:
                for app in application_list:
                    if "children" in app.keys():
                        del app["children"]
                    app_list.append(app)
                    app_name_list.append(app.get("unique_code"))
        if data_type == "app_name_list":
            return app_name_list
        else:
            return app_list

    def _business_tree(self, token):
        """
        [
            {
                'type': 'BUSINESS',
                'code': 1,
                'unique_code': 'OpsAny',
                'name': 'OpsAny产品线',
                'children': [
                    {
                        'type': 'APPLICATION',
                        'code': 1,
                        'unique_code': 'OpsAny',
                        'name': 'OpsAny智能运维平台',
                        'children': [
                            {
                                'type': 'SERVICE',
                                'code': 1,
                                'unique_code': 'fuwu', '
                                name': '服务'
                            }
                        ]
                    }
                ]
            }
        ]
        """
        esb_obj = EsbApi(token)
        business_tree_list = esb_obj.business_tree()
        return business_tree_list


class BusinessTreeV2(BaseObject):
    def get_business_application_list_v2(self, request):
        import time
        start = time.time()
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.USER_NOT_EXISTED, language=self.ops_language()))
        business_tree_list = self._get_business_application_list_v2(user_query=user_query)
        end = time.time()
        print("获取业务树耗时", end - start)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, business_tree_list, language=self.ops_language()))

    # def _get_business_application_list_v2(self, user_query=None):
    #     business_queryset = BusinessModel.fetch_all()
    #     end_data = [query.to_tree_create_dict(user_query) for query in business_queryset]
    #     return end_data

    def _get_business_application_list_v2(self, user_query=None):
        businesses = BusinessModel.fetch_all()
        business_codes = [b.code for b in businesses]

        # 权限判断：获取用户有权限的应用code列表
        app_code_list = []
        if user_query and user_query.role not in [1]:
            app_code_list = user_query.get_auth_all_app_code_list()

        app_filter = {"business__in": businesses}
        if app_code_list:
            app_filter["code__in"] = app_code_list

        applications = ApplicationModel.fetch_all(**app_filter)

        # 按业务code分组应用
        app_map = {}
        for app in applications:
            biz_code = app.business.code if app.business else None
            if biz_code:
                app_map.setdefault(biz_code, []).append(app.to_tree_create_dict())

        tree_data = []
        for biz in businesses:
            biz_dict = {
                "code": biz.code,
                "unique_code": biz.data.get("BUSINESS_name"),
                "name": biz.data.get("BUSINESS_VISIBLE_NAME"),
                "type": biz.model_code,
                "children": app_map.get(biz.code, [])
            }
            tree_data.append(biz_dict)
        return tree_data


class GetHostInst(BaseObject):
    def __init__(self, request):
        super(GetHostInst, self).__init__(request)
        self.esb = EsbApi(request.COOKIES.get('bk_token'))
        self.kwargs = request.GET.dict()

    def get_host_inst(self):
        data = self.kwargs
        search_type = data.get("search_type", "")
        search_data = data.get("search_data", "")
        # b = a.get_agent_by_business_code("all")
        b = self.esb.get_control_agent_info(system_type=data.get("system_type", None),
                                            group_type=data.get("group_type", None),
                                            search_type=search_type,
                                            search_data=search_data
                                            )
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, b, language=self.ops_language()))

    def get_host_group_list(self):
        end_data = self.esb.get_agent_group_list()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))

    def get_host_group(self):
        kwargs = self.kwargs
        group_type = kwargs.get("group_type", "")
        group_name = kwargs.get("group_name", "")
        filters = {}
        if group_type:
            filters["type"] = group_type
        if group_name:
            filters["name__contains"] = group_name
        all_group = self.esb.host_group_to_job("all", filters)
        # end_data = []
        # for i in all_group:
        #     flag = True
        #     if group_type:
        #         if i.get("type") != group_type:
        #             flag = False
        #     if group_name:
        #         if group_name.lower() not in i.get("name").lower():
        #             flag = False
        #     if flag:
        #         end_data.append(i)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, all_group.get("data", []),
                                    language=self.ops_language()))


class HomePageView(BaseView):
    def get(self, request):
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        dic = {}
        if user_query.role not in [1]:
            # app_role_list = [app_role.application.code for app_role in
            #                  ApplicationUserRoleModel.fetch_all(user_info=user_query)]
            app_role_list = user_query.get_auth_all_app_code_list()
            dic["code__in"] = app_role_list
        # 当前用户下的应用
        app_queryset = ApplicationModel.fetch_all(**dic)

        job_filter_dic = {}
        if user_query.role != 1:
            job_code_list, _, _ = user_query.get_code_list(app_queryset, id_type="job")
            job_read_code_list = job_code_list[0]
            job_filter_dic["code__in"] = job_read_code_list

        view_queryset = ApplicationJenkinsModel.fetch_all(application__in=app_queryset)
        # 当前用户下的流水线
        jobs_queryset = ApplicationJenkinsJobsModel.fetch_all(view__in=view_queryset, **job_filter_dic)

        # 应用覆盖（图一）
        use_job_count, unused_job_count = 0, 0
        for app_query in app_queryset:
            view_query = ApplicationJenkinsModel.fetch_one(application=app_query)

            job_filter_dic = {}
            if user_query.role != 1:
                job_code_list, _, _ = user_query.get_code_list(app_query, id_type="job")
                job_read_code_list = job_code_list[0]
                job_filter_dic["code__in"] = job_read_code_list

            # if ApplicationJenkinsJobsModel.fetch_one(view=view_query):
            if ApplicationJenkinsJobsModel.fetch_all(view=view_query, **job_filter_dic):
                use_job_count += 1
            else:
                unused_job_count += 1

        # 部署模板（图二）
        built_in_count, custom_count = 0, 0
        for job_query in PipelineTemplateModel.fetch_all():
            if job_query.built_in:
                built_in_count += 1
            else:
                custom_count += 1

        # 部署成功率（图三）, 今日数据（图四）
        now_date = datetime.datetime.date(datetime.datetime.now())
        job_success_count, job_unsuccessful_count = 0, 0
        today_task_success_count, today_task_error_count = 0, 0
        job_log_queryset = ApplicationJenkinsJobBuildModel.fetch_all(job__in=jobs_queryset)
        for job_log_query in job_log_queryset:
            if job_log_query.created_at.date() == now_date:
                if job_log_query.result == "SUCCESS":
                    today_task_success_count += 1
                else:
                    today_task_error_count += 1
            if job_log_query.result == "SUCCESS":
                job_success_count += 1
            else:
                job_unsuccessful_count += 1

        end_dic = {
            "job_cover": {"use_job": use_job_count, "unused_job": unused_job_count},
            "job_template": {"built_in_count": built_in_count, "custom_count": custom_count},
            "job_status": {"job_success_count": job_success_count, "job_unsuccessful_count": job_unsuccessful_count},
            "today_job": {"today_task_success_count": today_task_success_count,
                          "today_task_error_count": today_task_error_count},
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_dic, language=self.ops_language()))


class HomePageSevenJobView(BaseView):
    def get(self, request):
        # 检测Jenkins
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        user_query = GetUserInfo().get_user_info(request)
        kwargs = request.GET.dict()
        try:
            current, pageSize = int(kwargs.pop("current")), int(kwargs.pop("pageSize"))
        except Exception:
            current, pageSize = 1, 10
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        dic = {}
        if user_query.role not in [1]:
            # app_role_list = [app_role.application.code for app_role in
            #                  ApplicationUserRoleModel.fetch_all(user_info=user_query)]
            app_role_list = user_query.get_auth_all_app_code_list()
            dic["code__in"] = app_role_list
        # 当前用户下的应用
        app_queryset = ApplicationModel.fetch_all(**dic)
        view_queryset = ApplicationJenkinsModel.fetch_all(application__in=app_queryset)

        job_filter_dic = {}
        if user_query.role != 1:
            job_code_list, _, _ = user_query.get_code_list(app_queryset, id_type="job")
            job_read_code_list = job_code_list[0]
            job_filter_dic["code__in"] = job_read_code_list

        # 当前用户下的流水线
        jobs_queryset = ApplicationJenkinsJobsModel.fetch_all(view__in=view_queryset, **job_filter_dic)

        seven_ago_date = datetime.datetime.now().date() - datetime.timedelta(days=7)
        task_log_dic = {"job__in": jobs_queryset, "datetime__gte": seven_ago_date}
        job_log_queryset, total = ApplicationJenkinsJobBuildModel.pagination(current, pageSize, order_by="-datetime", **task_log_dic)
        job_log_list = [query.to_home_page() for query in job_log_queryset]
        end_data = {
            "current": current,
            "pageSize": pageSize,
            "total": total,
            "data": job_log_list
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, end_data, language=self.ops_language()))


class HomePageFrequentUsedAppView(BaseView):
    def get(self, request):
        # 检测Jenkins
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        try:
            length = int(request.GET.get("length", 8))
        except:
            length = 8
        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))
        dic = {}
        if user_query.role not in [1]:
            # app_role_list = [app_role.application.code for app_role in
            #                  ApplicationUserRoleModel.fetch_all(user_info=user_query)]
            app_role_list = user_query.get_auth_all_app_code_list()
            dic["code__in"] = app_role_list
        # 当前用户下的应用
        app_queryset = ApplicationModel.fetch_all(**dic)
        # 当前用户下的流水线
        app_list = []
        for app_query in app_queryset:
            dic = app_query.to_home_page()
            view_query = ApplicationJenkinsModel.fetch_one(application=app_query)

            job_filter_dic = {}
            if user_query.role != 1:
                job_code_list, _, _ = user_query.get_code_list(app_query, id_type="job")
                job_read_code_list = job_code_list[0]
                job_filter_dic["code__in"] = job_read_code_list

            # 当前用户下的流水线
            jobs_queryset = ApplicationJenkinsJobsModel.fetch_all(view=view_query, **job_filter_dic)
            task_log_queryset = ApplicationJenkinsJobBuildModel.fetch_all(job__in=jobs_queryset).order_by(
                "-created_at")
            if task_log_queryset:
                dic["datetime"] = task_log_queryset[0].get_datetime()
            dic["build_count"] = len(task_log_queryset)
            if len(task_log_queryset):
                app_list.append(dic)
        sort_app_list = self.bubble_sort(app_list)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, sort_app_list[: length],
                                    language=self.ops_language()))

    def bubble_sort(self, data_list):
        for i in range(1, len(data_list)):
            for j in range(0, len(data_list) - i):
                if data_list[j].get("build_count") < data_list[j + 1].get("build_count"):
                    data_list[j], data_list[j + 1] = data_list[j + 1], data_list[j]
        return data_list


class UpdateDirectorView(BaseView):
    def get(self, request):
        # all_user_list = esb.get_all_users()
        token = request.COOKIES.get("bk_token")
        esb = EsbApi(token=token)
        all_user_list = esb.get_user_group_sync()
        user_list = all_user_list.get("user_list", []) or []
        if not user_list:
            return JsonResponse(error(ErrorStatusCode.CUSTOM_ERROR, custom_message="没有拉取到用户信息"))
        temp_user_list = []
        for each_user in user_list:
            used_field = {}
            is_activate = each_user.get("is_activate")
            used_field["phone"] = each_user.get("phone")
            used_field["username"] = each_user.get("username")
            used_field["email"] = each_user.get("email")
            used_field["ch_name"] = each_user.get("chname")
            used_field["role"] = each_user.get("bk_role")
            used_field["is_activate"] = True if is_activate else False
            # if not UserInfo.objects.filter(username=each_user["bk_username"]).count():
            obj_user = UserInfo.fetch_one(username=each_user["username"])
            if not obj_user:
                obj_user = UserInfo.objects.create(**used_field)
            else:
                obj_user.update(**used_field)
                # obj_user = UserInfo.objects.select_for_update().filter(username=each_user["bk_username"])
                # with transaction.atomic():

            temp_user_list.append(used_field["username"])
        local_all_users = UserInfo.objects.all()
        deleted_user_list = []
        for each in local_all_users:
            if each.username not in temp_user_list:
                deleted_user_list.append(each.username)
        UserInfo.objects.filter(username__in=deleted_user_list).update(is_activate=False)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS))
