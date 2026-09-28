import json

from django.http import JsonResponse

from component.base_views import BaseObject
from component.libs import GetUserInfo
from pipeline.utils import constant
from component.status_code import ErrorStatusCode, error, SuccessStatusCode, success
from pipeline.utils.jenkins_api import JenkinsApi
from pipeline.models import ApplicationModel, JenkinsCredentialsModel, ToolsModel, ApplicationJenkinsCredentialsModel, \
    UserJenkinsCredentialsModel
from pipeline.utils.sync_data import jenkins_sync_credentials


class JenkinsCredentialsType(BaseObject):
    def get_credentials_type(self, request):
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, constant.CREDENTIALS_TYPE_LIST,
                                    language=self.ops_language()))


class JenkinsCredentials(BaseObject):
    def get_credentials(self, request):
        # 同步凭据数据
        res = jenkins_sync_credentials()
        kwargs = request.GET.dict()
        app_code = kwargs.pop("app_code", None)
        all_data = kwargs.pop("all_data", None)
        search_type = kwargs.pop("search_type", None)
        search_data = kwargs.pop("search_data", None)
        dic = dict()
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        user_query = GetUserInfo().get_user_info(request)
        if not user_query:
            return JsonResponse(error(ErrorStatusCode.NOT_HAVE_USER_INFO, language=self.ops_language()))

        if search_type and search_data:
            dic[search_type + "__contains"] = search_data
        try:
            current = int(kwargs.pop("current", 1))
            pageSize = int(kwargs.pop("pageSize", 10))
        except Exception:
            current = 1
            pageSize = 10

        # user
        user_credentials_queryset = UserJenkinsCredentialsModel.fetch_all(user__nin=[user_query])

        user_credentials_code_list = [user_credentials.jenkins_credentials.code for user_credentials in
                                      user_credentials_queryset if user_credentials.jenkins_credentials]

        if app_code and all_data:
            app_query = ApplicationModel.fetch_one(code=app_code)

            app_credentials_queryset = ApplicationJenkinsCredentialsModel.fetch_all(application__nin=[app_query])

            jenkins_credentials_code_list = [app_credentials.jenkins_credentials.code for app_credentials in
                                             app_credentials_queryset if app_credentials.jenkins_credentials]
            jenkins_credentials_code_list.extend(user_credentials_code_list)

            credentials_queryset = JenkinsCredentialsModel.fetch_all(code__nin=jenkins_credentials_code_list,
                                                                     **dic).order_by("-is_inner")
            credentials_list = [credentials.to_dict() for credentials in credentials_queryset]
            return JsonResponse(
                success(SuccessStatusCode.MESSAGE_GET_SUCCESS, credentials_list, language=self.ops_language()))

        if all_data:
            credentials_queryset = JenkinsCredentialsModel.fetch_all(is_inner=False,
                                                                     code__nin=user_credentials_code_list)
            credentials_list = [credentials.to_dict() for credentials in credentials_queryset]
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, credentials_list,
                                        language=self.ops_language()))

        current_page, total = JenkinsCredentialsModel.pagination(current, pageSize,
                                                                 code__nin=user_credentials_code_list,
                                                                 order_by="-is_inner", **dic)
        end_data = []
        if current_page:
            for i in current_page:
                end_data.append(i.to_dict())
        data = {
            "current": current,
            "pageSize": pageSize,
            "total": total,
            "data": end_data
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

    def create_credentials(self, request):
        kwargs = json.loads(request.body)
        storage_type = kwargs.get("storage_type")
        app_code = kwargs.get("app_code")
        is_inner = kwargs.get("is_inner", False)
        credentials_type = kwargs.get("type")
        name = kwargs.get("name")
        params = kwargs.get("params")
        if not isinstance(params, dict) and not isinstance(is_inner, bool) and not all(
                [app_code, storage_type, type, name, params, params.get("credentials_id")]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))

        credentials_id = params.get("credentials_id")
        username = params.get("username", "")
        jenkins_credentials = JenkinsCredentialsModel.fetch_one(credentials_id=credentials_id)
        if jenkins_credentials:
            return JsonResponse(error(ErrorStatusCode.JENKINS_CREDENTIALS_HAS_EXISTED, language=self.ops_language()))
        jenkins_credentials = JenkinsCredentialsModel.fetch_one(name=name)
        if jenkins_credentials:
            return JsonResponse(
                error(ErrorStatusCode.JENKINS_CREDENTIALS_NAME_HAS_EXISTED, language=self.ops_language()))
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        data = jenkins_api.create_credentials(params=params, type=credentials_type)
        if data.get("status"):

            jenkins_credentials = JenkinsCredentialsModel.create(name=name, username=username,
                                                                 credentials_id=credentials_id, is_inner=is_inner)
            if is_inner and app_code:
                application = ApplicationModel.fetch_one(code=app_code)
                app_jenkins_credentials = ApplicationJenkinsCredentialsModel.fetch_one(
                    application=application, jenkins_credentials=jenkins_credentials)
                if not app_jenkins_credentials:
                    ApplicationJenkinsCredentialsModel.create(application=application,
                                                              jenkins_credentials=jenkins_credentials)
            # 同步凭据数据
            res = jenkins_sync_credentials()
            return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, language=self.ops_language()))
        return JsonResponse(error(*data.get("message"), language=self.ops_language()))

    def update_credentials(self, request):
        # 校验工具
        kwargs = json.loads(request.body)
        code = kwargs.get("code")
        app_code = kwargs.get("app_code")
        is_inner = kwargs.get("is_inner", False)
        name = kwargs.get("name")
        params = kwargs.get("params")
        username = params.get("username")

        application = None
        # 校验APP
        if app_code:
            application = ApplicationModel.fetch_one(code=app_code)

        # 校验凭据
        jenkins_credentials = JenkinsCredentialsModel.fetch_one(code=code)
        if not jenkins_credentials:
            return JsonResponse(error(ErrorStatusCode.JENKINS_CREDENTIALS_NOT_EXISTED, language=self.ops_language()))
        # 校验工具
        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))
        credentials_id = jenkins_credentials.credentials_id
        typeCode = jenkins_credentials.typeCode
        params["credentials_id"] = credentials_id

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        data = jenkins_api.update_credentials(credentials_id, params=params, type=typeCode)
        if data.get("status"):
            dic = dict()
            if name:
                dic["name"] = name
            if username:
                dic["username"] = username
            if is_inner is True:
                app_jenkins_credentials_ = ApplicationJenkinsCredentialsModel.fetch_one(
                    jenkins_credentials=jenkins_credentials)
                if app_jenkins_credentials_:
                    app_jenkins_credentials_.update(**{"application": application,
                                                       "jenkins_credentials": jenkins_credentials})
                else:
                    ApplicationJenkinsCredentialsModel.create(application=application,
                                                              jenkins_credentials=jenkins_credentials)
                dic["is_inner"] = True
            else:
                app_jenkins_credentials_ = ApplicationJenkinsCredentialsModel.fetch_one(
                    jenkins_credentials=jenkins_credentials)
                if app_jenkins_credentials_:
                    app_jenkins_credentials_.delete()
                dic["is_inner"] = False
            jenkins_credentials.update(**dic)
        else:
            return JsonResponse(error(ErrorStatusCode.OPERATION_ERROR, language=self.ops_language()))

        # 同步凭据数据
        jenkins_sync_credentials()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, language=self.ops_language()))

    def delete_credentials(self, request):
        kwargs = json.loads(request.body)
        code = kwargs.get("code")

        jenkins_credentials = JenkinsCredentialsModel.fetch_one(code=code)
        if not jenkins_credentials:
            return JsonResponse(error(ErrorStatusCode.JENKINS_CREDENTIALS_HAS_EXISTED, language=self.ops_language()))

        tool_query = ToolsModel.fetch_one(tool_type="jenkins")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

        # 创建jenkins连接
        jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
        data = jenkins_api.delete_credentials(credentialsId=jenkins_credentials.credentials_id)
        if data.get("status"):
            jenkins_credentials.delete()
            return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))
        return JsonResponse(error(*data.get("message"), language=self.ops_language()))

