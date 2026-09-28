import gitlab
import requests

from component.status_code import ErrorStatusCode

GITLAB_API = "api/v4/"
PROJECT = "project/"
HOOKS = "/projects/:{}/hooks"


class GitLabApi(object):
    def __init__(self, url, oauth_token):
        self.url = url
        self.private_token = oauth_token
        self.server = self.git_server()

    def git_server(self):
        gitlab_oauth_token = gitlab.Gitlab(url=self.url, oauth_token=self.private_token, timeout=10)
        vision, revision = gitlab_oauth_token.version()
        if vision != "unknown":
            return gitlab_oauth_token
        return gitlab.Gitlab(url=self.url, private_token=self.private_token)

    def _get_url(self, url_path):
        url = self.url + GITLAB_API + url_path
        return url

    def test(self):
        return self.server.api_url

    def status(self):
        try:
            res = self.auth()
            if res == None:
                return True
        except gitlab.GitlabAuthenticationError as e:
            return ErrorStatusCode.USER_OR_PASSWORD_ERROR, str(e)
        except requests.exceptions.ConnectionError as e:
            return ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        except Exception as e:
            return ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return True

    def auth(self):
        return self.server.auth()

    def get_version(self):
        return self.server.version()

    def get_attributes(self, pro_list):
        pro_attributes_list = list()
        for pro in pro_list:
            pro_attributes_list.append(pro.attributes)
        return pro_attributes_list

    def get_group(self):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            group_list_pro = self.server.groups.list(as_list=True)
            print("group_list", group_list_pro)
            group_list = list()
            for group in group_list_pro:
                group_list.append(group.attributes)
            data["status"] = 1
            data["data"] = group_list
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def get_project_list(self):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            # all=True archived=1 visibility='public' owned=True starred=True search='keyword'
            project_pro_list = self.server.projects.list(all=True)
            project_list = list()
            for project in project_pro_list:
                project_attr = project.attributes
                # project_branch = project.branches.list()
                # project_attr["branch"] = [branch.name for branch in project_branch]
                # print("project_attr", project_attr)
                project_list.append(project_attr)
            data["status"] = 1
            data["data"] = project_list
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def get_project(self, project_id):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project_pro = self.server.projects.get(id=project_id, lazy=True)
            data["status"] = 1
            data["data"] = project_pro.attributes
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            if "Internal Server Error" in str(e):
                data["message"] = ErrorStatusCode.GITLAB_INTERNAL_SERVER_ERROR, str(e)
            else:
                data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def get_project_branch(self, id):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project_pro = self.server.projects.get(id=id, lazy=True)
            project_branch = project_pro.branches.list()
            project_branch_list = self.get_attributes(project_branch)
            data["status"] = 1
            data["data"] = project_branch_list
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def get_project_hooks_list(self, id):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project = self.server.projects.get(id=id, lazy=True)
            project_hooks = project.hooks.list()
            project_hooks_list = [project_hooks.attributes for project_hooks in project_hooks]
            data["status"] = 1
            data["data"] = project_hooks_list
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            if "Forbidden" in str(e):
                data["message"] = ErrorStatusCode.USER_GIT_NOT_POWER, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def get_project_hooks(self, project_id, hook_id):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project = self.server.projects.get(id=project_id, lazy=True)
            project_hooks = project.hooks.get(hook_id)
            data["status"] = 1
            # attributes
            data["data"] = project_hooks
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def create_project_hooks(self, project_id, url, token, push_events=0, tag_push_events=0, merge_requests_events=0):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project = self.server.projects.get(id=project_id, lazy=True)
            params = {
                "url": url,
                "token": token,
                "push_events": push_events,
                "tag_push_events": tag_push_events,
                "merge_requests_events": merge_requests_events,
                "repository_update_events": 0,
                "enable_ssl_verification": 0,
                "issues_events": 0,
                "confidential_issues_events": 0,
                "note_events": 0,
                "confidential_note_events": 0,
                "pipeline_events": 0,
                "wiki_page_events": 0,
                "job_events": 0,
                "push_events_branch_filter": ""
            }
            project_hooks = project.hooks.create(params)
            data["status"] = 1
            data["data"] = project_hooks.attributes
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabCreateError as e:
            if "Forbidden" in str(e):
                data["message"] = ErrorStatusCode.USER_GIT_NOT_POWER, str(e)
            else:
                data["message"] = ErrorStatusCode.OPERATION_ERROR, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def update_project_hooks(self, project_id, url, token, push_events=0, tag_push_events=0, merge_requests_events=0):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project = self.server.projects.get(id=project_id, lazy=True)
            params = {
                "url": url,
                "token": token,
                "push_events": push_events,
                "tag_push_events": tag_push_events,
                "merge_requests_events": merge_requests_events,
                "repository_update_events": 0,
                "enable_ssl_verification": 0,
                "issues_events": 0,
                "confidential_issues_events": 0,
                "note_events": 0,
                "confidential_note_events": 0,
                "pipeline_events": 0,
                "wiki_page_events": 0,
                "job_events": 0,
                "push_events_branch_filter": ""
            }
            project_hooks = project.hooks.update(params)
            data["status"] = 1
            data["data"] = project_hooks.attributes
        # except gitlab.GitlabAuthenticationError as e:
        #     data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        # except Exception as e:
        #     data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data

    def delete_project_hooks(self, project_id, hook_id):
        data = {"status": 0, "message": "success", "data": ""}
        try:
            project = self.server.projects.get(id=project_id, lazy=True)
            project_hooks = project.hooks.delete(hook_id)
            data["status"] = 1
            # attributes
            data["data"] = project_hooks
        except gitlab.GitlabAuthenticationError as e:
            data["message"] = ErrorStatusCode.TOOL_AUTH_ERROR, str(e)
        except gitlab.GitlabGetError as e:
            data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
        except requests.ConnectionError as e:
            data["message"] = ErrorStatusCode.GITLAB_SERVER_ERROR, str(e)
        except Exception as e:
            if "Not found" in str(e):
                data["message"] = ErrorStatusCode.DATA_NOT_EXISTED, str(e)
            else:
                data["message"] = ErrorStatusCode.TOOL_CONNECTION_ERROR, str(e)
        return data


if __name__ == '__main__':
    pass
