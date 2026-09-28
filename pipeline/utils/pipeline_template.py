import json

from django.http import JsonResponse

from component.base_views import BaseObject
from pipeline.utils import constant
from component.status_code import error, ErrorStatusCode, success, SuccessStatusCode
from pipeline.utils.jenkins_api import JenkinsApi
from pipeline.models import PipelineTemplateGroupModel, PipelineTemplateModel, ToolsModel


class PipelineTemplateGroup(BaseObject):
    def get_template_group(self, request):
        group = request.GET.get("group")

        pipeline_template_group_queryset = PipelineTemplateGroupModel.fetch_all().order_by("-built_in", "created_at")
        pipeline_template_group_list = list()

        for pipeline_template_group in pipeline_template_group_queryset:
            dic = pipeline_template_group.to_dict()
            pipeline_template_queryset = PipelineTemplateModel.fetch_all(group=pipeline_template_group).order_by(
                "-built_in", "created_at")

            if not group:
                pipeline_template_list = list()
                # 校验工具
                tool_query = ToolsModel.fetch_one(tool_type="jenkins")
                if not tool_query:
                    return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
                if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
                    return JsonResponse(error(ErrorStatusCode.JENKINS_STATUS_ERROR, language=self.ops_language()))

                jenkins_api = JenkinsApi(request, **tool_query.link_tool_dict())
                for pipeline_template_query in pipeline_template_queryset:
                    template_dict = pipeline_template_query.to_dict()
                    template_str = pipeline_template_query.template
                    result = jenkins_api.to_json(template_str)
                    template_json = result.get("data") if isinstance(result.get("data"), dict) else {}

                    stage_list = [stage.get("name") for stage in template_json.get("pipeline", {}).get("stages", [])]
                    template_dict["stage_list"] = stage_list

                    pipeline_template_list.append(template_dict)
                dic["pipeline_template_list"] = pipeline_template_list
            # else:
            #     if pipeline_template_group.name in ["默认分组"]:
            #         continue
            pipeline_template_group_list.append(dic)

        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline_template_group_list,
                                    language=self.ops_language()))

    def create_template_group(self, request):
        kwargs = json.loads(request.body)
        name = kwargs.get("name")
        description = kwargs.get("description")
        built_in = kwargs.get("built_in", None)
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(name=name)
        if pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.GROUP_HAS_EXISTED, language=self.ops_language()))
        dic = {"name": name}
        if description:
            dic["description"] = description
        if built_in:
            dic["built_in"] = built_in
        pipeline_template_group_query = PipelineTemplateGroupModel.create(**dic)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, pipeline_template_group_query.to_dict(),
                                    language=self.ops_language()))

    def update_template_group(self, request):
        kwargs = json.loads(request.body)
        code = kwargs.get("code")
        name = kwargs.get("name", None)
        description = kwargs.get("description", None)
        if not all([code, name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(code=code)
        if not pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        is_unique = PipelineTemplateGroupModel.check_field_unique(code=code, field_name="name", field_value=name)
        if not is_unique:
            return JsonResponse(error(ErrorStatusCode.GROUP_HAS_EXISTED, language=self.ops_language()))
        dic = {"name": name}
        if description:
            dic["description"] = description
        pipeline_template_group_query.update(**dic)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, pipeline_template_group_query.to_dict(),
                                    language=self.ops_language()))

    def delete_template_group(self, request):
        kwargs = json.loads(request.body)
        code = kwargs.get("code")
        if not code:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(code=code)
        if not pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        pipeline_template_queryset = PipelineTemplateModel.fetch_all(group=pipeline_template_group_query)
        if pipeline_template_queryset:
            return JsonResponse(error(ErrorStatusCode.GROUP_DELETE_HAS_EXISTED, language=self.ops_language()))
        pipeline_template_group_query.delete()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))


class PipelineTemplate(BaseObject):
    def get_template(self, request):
        code = request.GET.get("code")
        if not code:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_query = PipelineTemplateModel.fetch_one(code=code)
        if not pipeline_template_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, pipeline_template_query.to_dict(),
                                    language=self.ops_language()))

    def create_template(self, request):
        kwargs = json.loads(request.body)
        group_id = kwargs.get("group_id")
        name = kwargs.get("name")
        template = kwargs.get("template")
        template_type = kwargs.get("type", "自定义模板")
        description = kwargs.get("description", None)
        icon_url = kwargs.get("icon_url", None)
        built_in = kwargs.get("built_in", None)
        if not all([group_id, name, template]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(code=group_id)
        if not pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.GROUP_NOT_EXISTED, language=self.ops_language()))
        pipeline_template_query = PipelineTemplateModel.fetch_one(name=name)
        if pipeline_template_query:
            return JsonResponse(error(ErrorStatusCode.TEMPLATE_HAS_EXISTED, language=self.ops_language()))
        dic = {"name": name, "group": pipeline_template_group_query, "template": template, "type": template_type}
        if description:
            dic["description"] = description
        if built_in:
            dic["built_in"] = built_in
        if icon_url:
            dic["icon_url"] = icon_url
        if pipeline_template_group_query.built_in:
            dic["built_in"] = True
        else:
            dic["built_in"] = False
        pipeline_template_query = PipelineTemplateModel.create(**dic)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, pipeline_template_query.to_dict(),
                                    language=self.ops_language()))

    def update_template(self, request):
        kwargs = json.loads(request.body)
        code = kwargs.get("code")
        group_id = kwargs.get("group_id")
        name = kwargs.get("name")
        template = kwargs.get("template")
        description = kwargs.get("description", None)
        icon_url = kwargs.get("icon_url", None)
        if not all([code, group_id, name, template, type]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(code=group_id)
        if not pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.GROUP_NOT_EXISTED, language=self.ops_language()))

        pipeline_template_query = PipelineTemplateModel.fetch_one(code=code)
        if not pipeline_template_query:
            return JsonResponse(error(ErrorStatusCode.TEMPLATE_NOT_EXISTED, language=self.ops_language()))

        is_unique = PipelineTemplateModel.check_field_unique(code=code, field_name="name", field_value=name)
        if not is_unique:
            return JsonResponse(error(ErrorStatusCode.TEMPLATE_HAS_EXISTED, language=self.ops_language()))
        dic = {"name": name, "group": pipeline_template_group_query, "template": template}
        if description:
            dic["description"] = description
        if icon_url:
            dic["icon_url"] = icon_url
        pipeline_template_query.update(**dic)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_UPDATE_SUCCESS, pipeline_template_query.to_dict(),
                                    language=self.ops_language()))

    def delete_template(self, request):
        kwargs = json.loads(request.body)
        code = kwargs.get("code")
        if not code:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        pipeline_template_query = PipelineTemplateModel.fetch_one(code=code)
        if not pipeline_template_query:
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, language=self.ops_language()))

        pipeline_template_query.delete()
        return JsonResponse(success(SuccessStatusCode.MESSAGE_DELETE_SUCCESS, language=self.ops_language()))

    def copy_template(self, request):
        kwargs = json.loads(request.body)
        template_id = kwargs.get("template_id")
        group_id = kwargs.get("group_id")
        name = kwargs.get("name")
        template_type = kwargs.get("type", "自定义模板")
        icon_url = kwargs.get("icon_url", None)
        # 校验参数
        if not all([template_id, group_id, name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        # 校验复制模板
        pipeline_template_query_to_code = PipelineTemplateModel.fetch_one(code=template_id)
        if not pipeline_template_query_to_code:
            return JsonResponse(error(ErrorStatusCode.TEMPLATE_NOT_EXISTED, language=self.ops_language()))
        # 校验分组
        pipeline_template_group_query = PipelineTemplateGroupModel.fetch_one(code=group_id)
        if not pipeline_template_group_query:
            return JsonResponse(error(ErrorStatusCode.GROUP_NOT_EXISTED, language=self.ops_language()))
        # if pipeline_template_group_query.name in ["默认分组"]:
        #     return JsonResponse(error(ErrorStatusCode.BUILT_IN_NOT_OPERATION, language=self.ops_language()))
        # 检验模板名是否存在
        pipeline_template_query = PipelineTemplateModel.fetch_one(name=name)
        if pipeline_template_query:
            return JsonResponse(error(ErrorStatusCode.TEMPLATE_HAS_EXISTED, language=self.ops_language()))

        template = pipeline_template_query_to_code.template
        description = kwargs.get("description", None) if kwargs.get("description",
                                                                    None) else pipeline_template_query_to_code.description
        dic = {"name": name, "group": pipeline_template_group_query, "template": template, "type": template_type}
        if description:
            dic["description"] = description
        if icon_url:
            dic["icon_url"] = icon_url
        if pipeline_template_group_query.built_in:
            dic["built_in"] = True
        else:
            dic["built_in"] = False
        pipeline_template_query = PipelineTemplateModel.create(**dic)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_CREATE_SUCCESS, pipeline_template_query.to_dict(),
                                    language=self.ops_language()))

