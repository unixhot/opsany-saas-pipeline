from django.http import JsonResponse

from component.base_views import BaseView
from pipeline.utils import constant
from component.status_code import error, ErrorStatusCode, success, SuccessStatusCode
from pipeline.utils.gitlab_api import GitLabApi
from pipeline.models import ToolsModel, ApplicationJenkinsJobsModel


class GitLabGroupView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        # 工具
        tool_query = ToolsModel.fetch_one(tool_type="git")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))

        # Gitlab
        gitlab_api = GitLabApi(**tool_query.link_git_dict())
        group_list_res = gitlab_api.get_group()
        if group_list_res.get("status"):
            group_list = group_list_res.get("data")
        else:
            group_list = []
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, group_list, language=self.ops_language()))


class GitLabAllProjectView(BaseView):
    def get(self, request):
        # 全部项目
        tool_query = ToolsModel.fetch_one(tool_type="git")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))

        # jenkins
        gitlab_api = GitLabApi(**tool_query.link_git_dict())
        project_all_list_res = gitlab_api.get_project_list()
        if project_all_list_res.get("status"):
            project_all_list = project_all_list_res.get("data")
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, project_all_list,
                                        language=self.ops_language()))
        else:
            return JsonResponse(error(*project_all_list_res.get("message"), language=self.ops_language()))


class GitLabProjectView(BaseView):
    def get(self, request):
        project_id = request.GET.get("project_id")
        tool_query = ToolsModel.fetch_one(tool_type="git")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))

        git_api = GitLabApi(**tool_query.link_git_dict())
        if project_id:
            project_res = git_api.get_project(project_id)
            if not project_res.get("status"):
                return JsonResponse(error(*project_res.get("message"), language=self.ops_language()))
            data = self.clean_data(project_res.get("data"))
            return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

        project_all_list_res = git_api.get_project_list()
        if not project_all_list_res.get("status"):
            return JsonResponse(error(*project_all_list_res.get("message"), language=self.ops_language()))
        project_all_list = project_all_list_res.get("data")
        project_list = list()
        for project in project_all_list:
            project_list.append(self.clean_data(project))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, project_list, language=self.ops_language()))

    def clean_data(self, project):
        dic = {
            "id": project.get("id"),
            "name": project.get("name"),
            "description": project.get("description"),
            "ssh_url_to_repo": project.get("ssh_url_to_repo"),
            "http_url_to_repo": project.get("http_url_to_repo"),
            # "branch": project.get("branch")
        }
        return dic


class GitLabProjectBranchView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        project_id = kwargs.get("project_id")
        if not project_id:
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        # У?鹤??
        tool_query = ToolsModel.fetch_one(tool_type="git")
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))

        # ????Gitlab????
        jenkins_api = GitLabApi(**tool_query.link_git_dict())
        project_branch_all_list_res = jenkins_api.get_project_branch(project_id)
        if not project_branch_all_list_res.get("status"):
            return JsonResponse(error(*project_branch_all_list_res.get("message"), language=self.ops_language()))
        project_branch_all_list = project_branch_all_list_res.get("data")
        project_branch_list = list()
        for project_branch in project_branch_all_list:
            project_branch_list.append({
                "project_id": project_branch.get("project_id"),
                "name": project_branch.get("name"),
                "can_push": project_branch.get("can_push"),
            })
        quoted_times_old = tool_query.quoted_times if tool_query.quoted_times else 0
        quoted_times = quoted_times_old + 1
        tool_query.update(quoted_times=quoted_times)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, project_branch_list,
                                    language=self.ops_language()))


class GitLabProjectHooksView(BaseView):
    def get(self, request):
        kwargs = request.GET.dict()
        project_id = kwargs.get("project_id")
        job_name = kwargs.get("job_name")
        if not all([project_id, job_name]):
            return JsonResponse(error(ErrorStatusCode.MUST_INPUT_MESSAGE, language=self.ops_language()))
        #
        tool_query = ToolsModel.fetch_one(tool_type="git")
        jenkins_query = ToolsModel.fetch_one(tool_type="jenkins")
        # 检测Gitlab工具
        if not tool_query:
            return JsonResponse(error(ErrorStatusCode.GIT_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.GITLAB_SERVER_ERROR, language=self.ops_language()))
        # 检测Jenkins工具
        if not jenkins_query:
            return JsonResponse(error(ErrorStatusCode.JENKINS_NOT_EXISTED, language=self.ops_language()))
        if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
            return JsonResponse(error(ErrorStatusCode.JENKINS_SERVER_ERROR, language=self.ops_language()))

        #
        gitlab_api = GitLabApi(**tool_query.link_git_dict())
        project_hooks_res = gitlab_api.get_project_hooks_list(project_id)
        if not project_hooks_res.get("status"):
            return JsonResponse(error(*project_hooks_res.get("message"), language=self.ops_language()))
        project_hooks_data = project_hooks_res.get("data")
        jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
        print("project_hooks_data", project_hooks_data)
        hooks_dic = dict()
        if jenkins_job and jenkins_job.hooks:
            hooks_dic = jenkins_job.hooks
        else:
            for project_hooks in project_hooks_data:
                api_addr = jenkins_query.api_addr if jenkins_query.api_addr[-1] == "/" else jenkins_query.api_addr + "/"
                project_url = api_addr + "project/" + job_name
                print("hooks_dic1", project_url, project_hooks.get("url"))
                if project_hooks.get("url") == project_url:
                    hooks_dic = project_hooks
                    break
        project_hooks = {
            "id": hooks_dic.get("id"),
            "project_id": hooks_dic.get("project_id"),
            "url": hooks_dic.get("url"),
            "push_events": hooks_dic.get("push_events"),
            "merge_requests_events": hooks_dic.get("merge_requests_events"),
            "tag_push_events": hooks_dic.get("tag_push_events")
        }
        quoted_times_old = tool_query.quoted_times if tool_query.quoted_times else 0
        quoted_times = quoted_times_old + 1
        tool_query.update(quoted_times=quoted_times)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, project_hooks,
                                    language=self.ops_language()))
