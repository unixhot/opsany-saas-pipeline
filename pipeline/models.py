import mongoengine as db

# Create your models here.

# 用户
from mongoengine import Q
from component.base_model import BasicDocument
from pipeline.utils import constant


class UserInfo(BasicDocument):
    code = db.SequenceField(primary_key=True)
    phone = db.StringField()
    username = db.StringField()
    email = db.StringField()
    ch_name = db.StringField()
    role = db.IntField()
    is_activate = db.BooleanField()
    icon_url = db.StringField()

    def to_base_dict(self):
        dt = {
            "id": self.id,
            "username": self.username,
            "ch_name": self.ch_name,
            "role": self.role,
        }
        return dt

    def to_dict(self):
        dt = {
            "phone": self.phone,
            "username": self.username,
            "email": self.email,
            "ch_name": self.ch_name,
            "role": self.role,
            "icon_url": self.icon_url
        }
        return dt

    def to_user_info_dict(self):
        dt = {
            "phone": self.phone,
            "username": self.username,
            "email": self.email,
            "ch_name": self.ch_name,
            "role": self.role,
        }
        return dt

    def to_code_dict(self):
        dt = {
            "code": self.code,
            "phone": self.phone,
            "username": self.username,
            "ch_name": self.ch_name,
        }
        return dt

    def to_role_dict(self):
        dt = {
            "code": self.code,
            "phone": self.phone,
            "username": self.username,
            "ch_name": self.ch_name,
        }
        return dt

    # 判断用户是否有某个应用的权限
    def is_app_auth(self, app_query):
        app_auth_queryset = self.get_get_strategy_list_by_user(app_query)
        if not app_auth_queryset:
            return False
        return True

    # 获取用户的权限策略
    def get_strategy_list_by_user(self):
        return StrategyModel.objects.filter(Q(user=self) | Q(group__in=list(GroupModel.fetch_all(user_list=self))))

    # 获取用户有权访问的所有应用code列表
    def get_auth_all_app_code_list(self):
        application_code_list = list()
        app_auth_queryset = self.get_get_strategy_list_by_user()
        for app_auth_query in app_auth_queryset:
            application_code_list.append(app_auth_query.application.code)
        application_code_set_list = list(set(application_code_list))
        return application_code_set_list

    # 获取用户有权限的应用
    def get_get_strategy_list_by_user(self, app=None):
        """
        :param app: 应用或应用查询集
        :return:
        """
        # 当前用户关联的所有策略
        strategy_queryset = StrategyModel.objects.filter(Q(user=self) | Q(group__in=list(GroupModel.fetch_all(user_list=self))))
        dic = {"strategy__in": list(strategy_queryset)}
        if app:
            if isinstance(app, ApplicationModel):
                dic["application"] = app
            else:
                dic["application__in"] = list(app)
        return ApplicationAuthModel.fetch_all(**dic)

    # 获取应用或应用分组或全部应用下的资源（流水线、持续部署、制品仓库）
    def get_code_list(self, app=None, id_type="job,deploy,repo"):
        app_auth_queryset = self.get_get_strategy_list_by_user(app)
        job_code_list, job_2_list, job_3_list, job_4_list, job_5_list, job_6_list, job_7_list = [], [], [], [], [], [], []
        deploy_code_list, deploy_2_list, deploy_3_list, deploy_4_list, deploy_5_list, deploy_6_list, deploy_7_list, deploy_8_list = [], [], [], [], [], [], [], []
        repo_code_list, repo_2_list, repo_3_list, repo_4_list, repo_5_list, repo_6_list, repo_7_list = [], [], [], [], [], [], []
        for app_auth_query in app_auth_queryset:
            if "job" in id_type:
                # if "job" in id_type and app_auth_query.all_select == 1:
                #     view_query = ApplicationJenkinsModel.fetch_one(application=app_auth_query.application)
                #     all_job_code_list = [job.code for job in ApplicationJenkinsJobsModel.fetch_all(view=view_query)]
                #     job_code_list.extend(all_job_code_list)
                #     job_2_list.extend(all_job_code_list)
                #     job_3_list.extend(all_job_code_list)
                #     job_4_list.extend(all_job_code_list)
                #     job_5_list.extend(all_job_code_list)
                #     job_6_list.extend(all_job_code_list)
                #     job_7_list.extend(all_job_code_list)
                if app_auth_query.all_select == 1 and app_auth_query.job_all_select:
                    view_query = ApplicationJenkinsModel.fetch_one(application=app_auth_query.application)
                    all_job_code_list = [job.code for job in ApplicationJenkinsJobsModel.fetch_all(view=view_query)]
                    if 1 in app_auth_query.job_all_select:
                        job_code_list.extend(all_job_code_list)
                    if 2 in app_auth_query.job_all_select:
                        job_2_list.extend(all_job_code_list)
                    if 3 in app_auth_query.job_all_select:
                        job_3_list.extend(all_job_code_list)
                    if 4 in app_auth_query.job_all_select:
                        job_4_list.extend(all_job_code_list)
                    if 5 in app_auth_query.job_all_select:
                        job_5_list.extend(all_job_code_list)
                    if 6 in app_auth_query.job_all_select:
                        job_6_list.extend(all_job_code_list)
                    if 7 in app_auth_query.job_all_select:
                        job_7_list.extend(all_job_code_list)
                else:
                    job_code_list.extend(app_auth_query.auth_job_1)
                    job_2_list.extend(app_auth_query.auth_job_2)
                    job_3_list.extend(app_auth_query.auth_job_3)
                    job_4_list.extend(app_auth_query.auth_job_4)
                    job_5_list.extend(app_auth_query.auth_job_5)
                    job_6_list.extend(app_auth_query.auth_job_6)
                    job_7_list.extend(app_auth_query.auth_job_7)
            if "deploy" in id_type:
                deploy_code_list.extend(app_auth_query.auth_deploy_1)
                deploy_2_list.extend(app_auth_query.auth_deploy_2)
                deploy_3_list.extend(app_auth_query.auth_deploy_3)
                deploy_4_list.extend(app_auth_query.auth_deploy_4)
                deploy_5_list.extend(app_auth_query.auth_deploy_5)
                deploy_6_list.extend(app_auth_query.auth_deploy_6)
                deploy_7_list.extend(app_auth_query.auth_deploy_7)
                deploy_8_list.extend(app_auth_query.auth_deploy_8)
            if "repo" in id_type:
                repo_code_list.extend(app_auth_query.auth_repo_1)
                repo_2_list.extend(app_auth_query.auth_repo_2)
                repo_3_list.extend(app_auth_query.auth_repo_3)
                repo_4_list.extend(app_auth_query.auth_repo_4)
                repo_5_list.extend(app_auth_query.auth_repo_5)
                repo_6_list.extend(app_auth_query.auth_repo_6)
                repo_7_list.extend(app_auth_query.auth_repo_7)
        return ([list(set(job_code_list)), list(set(job_2_list)), list(set(job_3_list)), list(set(job_4_list)),
                 list(set(job_5_list)), list(set(job_6_list)), list(set(job_7_list))],
                [list(set(deploy_code_list)), list(set(deploy_2_list)), list(set(deploy_3_list)),
                 list(set(deploy_4_list)), list(set(deploy_5_list)), list(set(deploy_6_list)),
                 list(set(deploy_7_list)), list(set(deploy_8_list))],
                [list(set(repo_code_list)), list(set(repo_2_list)), list(set(repo_3_list)),
                 list(set(repo_4_list)), list(set(repo_5_list)), list(set(repo_6_list)), list(set(repo_7_list))]
                )


# 保存最近一次更新rbac用户体系时间
class UserUpdateInfo(BasicDocument):
    id = db.SequenceField(primary_key=True)
    last_update_time = db.DateTimeField()

    class Meta:
        db_table = "update_user_data"


# 业务
class BusinessModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    data = db.DictField()
    pk_name = db.StringField()
    pk_value = db.StringField()
    model_code = db.StringField()
    import_type = db.StringField(default="逐条录入")
    link_inst = db.ListField()
    business_code = db.StringField(default="")  # 业务code
    position = db.StringField(null=False, default="yw")
    parent_inst = db.StringField()
    label_list = db.ListField()
    staff_manager_list = db.ListField()
    cmdb_code = db.IntField()

    # principal_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.DO_NOTHING)
    # create_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.DO_NOTHING)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["model_code"] = self.model_code
        dt["data"] = self.data
        if dt["data"]:
            dt["data"].pop("code", None)
        dt["pk_name"] = self.pk_name
        dt["pk_value"] = self.pk_value
        dt["position"] = self.position
        dt["import_type"] = self.import_type
        dt["link_inst"] = self.link_inst
        dt["parent_inst"] = self.parent_inst
        dt["business_code"] = self.business_code
        dt["created_at"] = str(self.created_at).split(".")[0]
        dt["cmdb_code"] = self.cmdb_code
        dt["application_count"] = ApplicationModel.counter(business=self)
        return dt

    def to_tree_dict(self, user_query=None):
        dt = dict()
        dt["code"] = self.code
        dt["unique_code"] = self.data.get("BUSINESS_name")
        dt["name"] = self.data.get("BUSINESS_VISIBLE_NAME")
        dt["type"] = self.model_code
        dic = {"business": self}
        if user_query:
            if user_query.role not in [1]:
                app_code_list = user_query.get_auth_all_app_code_list()
                dic["code__in"] = app_code_list
        application_queryset = ApplicationModel.fetch_all(**dic)
        application_list = [application_query.to_tree_dict(user_query) for application_query in application_queryset if
                            application_queryset]
        dt["children"] = application_list
        return dt

    def to_tree_create_dict(self, user_query=None):
        dt = dict()
        dt["code"] = self.code
        dt["unique_code"] = self.data.get("BUSINESS_name")
        dt["name"] = self.data.get("BUSINESS_VISIBLE_NAME")
        dt["type"] = self.model_code
        dic = {"business": self}
        if user_query:
            if user_query.role not in [1]:
                app_code_list = user_query.get_auth_all_app_code_list()
                dic["code__in"] = app_code_list
        application_queryset = ApplicationModel.fetch_all(**dic)
        application_list = [application_query.to_tree_create_dict() for application_query in application_queryset if
                            application_queryset]
        dt["children"] = application_list
        return dt

    def get_business_visible_name(self):
        return self.data.get("BUSINESS_VISIBLE_NAME")

    # 获取用户有权限访问的所有应用code列表
    def business_tree_to_strategy(self, user_query):
        application_code_list = list()
        app_auth_queryset = user_query.get_get_strategy_list_by_user()
        for app_auth_query in app_auth_queryset:
            application_code_list.append(app_auth_query.application.code)
        application_code_set_list = list(set(application_code_list))
        return application_code_set_list


# 应用
class ApplicationModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    data = db.DictField()
    pk_name = db.StringField()
    pk_value = db.StringField()
    model_code = db.StringField()
    import_type = db.StringField(default="逐条录入")
    link_inst = db.ListField()
    business_code = db.StringField(default="")  # 业务code
    position = db.StringField(null=False, default="yw")
    parent_inst = db.StringField()
    label_list = db.ListField()
    business = db.ReferenceField(BusinessModel, reverse_delete_rule=db.CASCADE)
    staff_manager_list = db.ListField()
    cmdb_code = db.IntField()
    creator_id = db.IntField()
    creator_username = db.StringField()

    # principal_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.DO_NOTHING)
    # create_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.DO_NOTHING)

    def to_base_dict(self):
        dt = {}
        dt["code"] = self.code
        dt["model_code"] = self.model_code
        dt["application_visible_name"] = self.data.get(self.model_code + "_VISIBLE_NAME")
        dt["application_name"] = self.data.get(self.model_code + "_name")
        return dt

    def to_deploy_dict(self):
        dt = {}
        dt["code"] = self.code
        dt["model_code"] = self.model_code
        dt["pk_name"] = self.pk_name
        dt["pk_value"] = self.pk_value
        return dt

    def to_dict(self):
        dt = {}
        dt["code"] = self.code
        dt["model_code"] = self.model_code
        dt["data"] = self.data
        if dt["data"]:
            dt["data"].pop("code", None)
        dt["pk_name"] = self.pk_name
        dt["pk_value"] = self.pk_value
        dt["position"] = self.position
        dt["import_type"] = self.import_type
        dt["link_inst"] = self.link_inst
        dt["parent_inst"] = self.parent_inst
        dt["business_code"] = self.business_code
        dt["position"] = self.position
        dt["created_at"] = str(self.created_at).split(".")[0]
        dt["cmdb_code"] = self.cmdb_code

        business = self.business
        if business:
            dt["business"] = business.to_dict()
        return dt

    def to_tree_dict(self, user_query=None):
        dt = {}
        dt["code"] = self.code
        dt["unique_code"] = self.data.get("APPLICATION_name")
        dt["name"] = self.data.get("APPLICATION_VISIBLE_NAME")
        dt["type"] = self.model_code
        dt["job_count"] = ApplicationJenkinsJobsModel.counter(view=ApplicationJenkinsModel.fetch_one(application=self))
        tags_queryset = JenkinsJobTagsModel.fetch_all(user_info=user_query)
        app_list = [tags_query.jenkins_job.code for tags_query in tags_queryset]
        dt["tags_job_count"] = ApplicationJenkinsJobsModel.counter(
            view=ApplicationJenkinsModel.fetch_one(application=self), code__in=app_list)
        if user_query.role != 1:
            job_read_code_list, _, _ = user_query.get_code_list(self, id_type="job")
            dt["job_count"] = ApplicationJenkinsJobsModel.counter(code__in=job_read_code_list[0])
            job_code_tags_list = list(set(job_read_code_list[0]) & set(app_list))
            dt["tags_job_count"] = ApplicationJenkinsJobsModel.counter(code__in=job_code_tags_list)
        return dt

    def to_tree_create_dict(self):
        dt = {}
        dt["code"] = self.code
        dt["unique_code"] = self.data.get("APPLICATION_name")
        dt["name"] = self.data.get("APPLICATION_VISIBLE_NAME")
        dt["type"] = self.model_code
        return dt

    def to_home_page(self):
        dt = {}
        dt["code"] = self.code
        dt["name"] = self.get_model_code_visible_name()
        return dt

    def get_model_code_name(self):
        return self.data.get(self.model_code + "_name")

    def get_model_visible_name_and_code(self):
        dt = {
            "code": self.code,
            "visible_name": self.data.get(self.model_code + "_VISIBLE_NAME")
        }
        return dt

    def get_model_code_visible_name(self):
        return self.data.get(self.model_code + "_VISIBLE_NAME")

    def get_rebuild_dict(self):
        dt = {
            "code": self.code,
            "visible_name": self.data.get(self.model_code + "_VISIBLE_NAME"),
            "name": self.data.get(self.model_code + "_name")
        }
        return dt


# ST2配置
class EventStackStormServiceModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    tool_name = db.StringField(max_length=128, null=True, unique=True)
    api_addr = db.StringField(max_length=255, null=False)
    username = db.StringField(max_length=128, null=True)
    password = db.StringField(max_length=255, null=True)
    api_token = db.StringField(max_length=255, null=True)
    description = db.StringField(max_length=255, null=True)

    def __unicode__(self):
        return self.tool_name

    def __str__(self):
        return self.tool_name

    def to_dict(self):
        dt = dict()
        dt["id"] = self.id
        dt["tool_name"] = self.tool_name
        dt["api_addr"] = self.api_addr
        dt["username"] = self.username
        dt["description"] = self.description
        return dt

    def connect_use_password_dict(self):
        dt = dict()
        dt["url"] = self.api_addr
        dt["username"] = self.username
        dt["password"] = self.password
        return dt

    def connect_use_api_token_dict(self):
        dt = dict()
        dt["url"] = self.api_addr
        dt["api_key"] = self.api_token
        return dt


# 应用权限
class ApplicationUserRoleModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE)
    user_info = db.ReferenceField(UserInfo, reverse_delete_rule=db.CASCADE)

    def to_dict(self):
        dt = {}
        dt["code"] = self.code
        dt["application"] = self.application.to_code_data_dict()
        dt["user_info"] = self.user_info.to_role_dict()
        return dt


# 工具
class ToolsModel(BasicDocument):
    type_choice = constant.TOOL_TYPE_LIST

    code = db.SequenceField(primary_key=True)
    # 工具名，最短4，最长32， 必传，唯一
    tool_name = db.StringField(min_length=2, max_length=128, required=True)
    # 工具类型，最长10， 必传
    tool_type = db.StringField(max_length=10, default="jenkins", required=True, unique=True, choices=type_choice)
    # 工具访问地址， 必传
    api_addr = db.StringField(max_length=255, required=True)
    # 用户名
    username = db.StringField(max_length=128)
    # 密码(token)
    api_token = db.StringField(max_length=255)
    # 描述
    description = db.StringField(max_length=512)
    # status
    link_status = db.StringField(default=constant.TOOL_LINK_STATUS_ERROR, max_length=32)
    # 引用次数
    quoted_times = db.IntField(default=0)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["tool_name"] = self.tool_name
        dt["tool_type"] = self.tool_type
        dt["api_addr"] = self.api_addr
        dt["username"] = self.username
        dt["api_token"] = self.api_token
        dt["description"] = self.description
        dt["link_status"] = self.link_status
        return dt

    def link_tool_dict(self):
        dt = dict()
        dt["url"] = self.api_addr
        dt["username"] = self.username
        dt["password"] = self.api_token
        return dt

    def link_git_dict(self):
        dt = dict()
        dt["url"] = self.api_addr
        dt["oauth_token"] = self.api_token
        return dt


# Jenkins凭据
class JenkinsCredentialsModel(BasicDocument):
    # 自定义
    code = db.SequenceField(primary_key=True)
    name = db.StringField(max_length=500, required=True)
    is_inner = db.BooleanField(default=False)
    typeCode = db.IntField()

    # 标准字段
    credentials_id = db.StringField(max_length=500, required=True, unique=True)
    typeName = db.StringField(max_length=500)
    # 显示名 username(描述)
    displayName = db.StringField(max_length=500)
    # 描述 描述信息
    description = db.StringField(max_length=500)
    # 全称   system/_/credentials_id
    fullName = db.StringField(max_length=500)
    fingerprint = db.DictField(default={})
    username = db.StringField()

    # 其他字段
    security = db.DictField(default={})

    # 外层字段
    credentials_class = db.StringField(max_length=500)
    credentials_description = db.StringField(max_length=500)
    credentials_displayName = db.StringField(max_length=500)
    credentials_fullDisplayName = db.StringField(max_length=500)
    credentials_global = db.BooleanField(default=True)
    credentials_urlName = db.StringField(max_length=500)

    access_token_value = db.StringField(max_length=100, null=True)
    is_private = db.StringField(max_length=10, default="0")     # 1：是  0：否（是否私有）
    credentials_type = db.StringField(max_length=10, default="0")       # 1：Nexus制品仓库凭据

    def to_parent_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.name
        dt["credentials_id"] = self.credentials_id
        return dt

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["storage_type"] = "Jenkins"
        dt["name"] = self.name
        dt["is_inner"] = self.is_inner
        dt["credentials_id"] = self.credentials_id
        dt["typeName"] = self.typeName
        dt["typeCode"] = self.typeCode
        dt["displayName"] = self.displayName
        dt["description"] = self.description
        dt["fullName"] = self.fullName
        dt["username"] = self.username
        dt["fingerprint"] = self.fingerprint
        dt["created_at"] = str(self.created_at).split(".")[0]
        dt["is_private"] = self.is_private

        application_query = ApplicationJenkinsCredentialsModel.fetch_one(jenkins_credentials=self)
        if application_query:
            dt["application"] = application_query.application.get_model_visible_name_and_code()
        else:
            dt["application"] = None
        return dt


# 应用凭据关联
class ApplicationJenkinsCredentialsModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE)
    jenkins_credentials = db.ReferenceField(JenkinsCredentialsModel, reverse_delete_rule=db.CASCADE)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["application"] = self.application.to_code_data_dict()
        dt["jenkins_credentials"] = self.jenkins_credentials.to_parent_dict()
        return dt


# 用户凭据关联
class UserJenkinsCredentialsModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    user = db.ReferenceField(UserInfo, reverse_delete_rule=db.CASCADE)
    jenkins_credentials = db.ReferenceField(JenkinsCredentialsModel, reverse_delete_rule=db.CASCADE)

    def to_dict(self):
        dt = {
            "code": self.code,
            "user": self.user.to_code_dict(),
            "jenkins_credentials": self.jenkins_credentials.to_parent_dict()
        }
        return dt


# 流水线模板分组
class PipelineTemplateGroupModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    # 语言类型
    name = db.StringField(max_length=20, required=True, unique=True)
    # 是否内置
    built_in = db.BooleanField(default=False)
    # 是否内置-opsany
    opsany_built_in = db.BooleanField(default=False)
    # 描述
    description = db.StringField()

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.name
        dt["built_in"] = self.built_in
        dt["description"] = self.description
        dt["created_at"] = str(self.created_at).split(".")[0]
        return dt


# pipeline脚本模板
class PipelineTemplateModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    # 语言类型
    group = db.ReferenceField(PipelineTemplateGroupModel, reverse_delete_rule=db.CASCADE)
    # 名称
    name = db.StringField(required=True, unique=True)
    # 类型
    type = db.StringField(default="自定义模板", required=True)
    # 是否内置
    built_in = db.BooleanField(default=False)
    # 是否内置-opsany
    opsany_built_in = db.BooleanField(default=False)
    # 脚本模板
    template = db.StringField(required=True)
    # 图片路径
    icon_url = db.StringField(required=False)
    # 描述
    description = db.StringField()

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["group"] = self.group.to_dict()
        dt["name"] = self.name
        dt["type"] = self.type
        dt["template"] = self.template
        dt["description"] = self.description
        dt["built_in"] = self.built_in
        dt["created_at"] = str(self.created_at).split(".")[0]
        if self.icon_url:
            dt["icon_url"] = self.icon_url
        return dt


# jenkins 配置文件模板命令
class PipelineToolModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    # 工具类型， 必传
    tool_type = db.StringField(max_length=20, required=True)
    # 工具名，最短4，最长32， 必传，唯一
    tool_name = db.StringField(min_length=2, max_length=128, required=True)
    name = db.StringField(max_length=100, required=True)
    arguments = db.ListField(default=[], required=True)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["tool_name"] = self.tool_name
        dt["tool_type"] = self.tool_type
        dt["name"] = self.name
        dt["arguments"] = self.arguments
        return dt


# jenkins 配置文件模板-post
class PipelineToolPostModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    # 中文名
    ch_name = db.StringField(required=True)
    # 条件选择
    condition = db.StringField(required=True)
    # name
    name = db.StringField(required=True)
    # 描述
    description = db.StringField(required=True)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["ch_name"] = self.ch_name
        dt["condition"] = self.condition
        dt["name"] = self.name
        dt["description"] = self.description
        return dt


# 应用-jenkins view
class ApplicationJenkinsModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE)
    jenkins_view_name = db.StringField(max_length=255, required=True)
    jenkins_jobs = db.ListField(default=[])

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["jenkins_view_name"] = self.jenkins_view_name
        return dt

    def get_jenkins_view_name(self):
        return self.jenkins_view_name

    def get_all_build_data(self):
        dt = dict()
        dt["code"] = self.code
        dt["application_name"] = self.application.get_application_name()
        dt["jenkins_view_name"] = self.jenkins_view_name
        app_job_list = list()
        application_jenkins_jobs_queryset = ApplicationJenkinsJobsModel.fetch_all(view=self)
        for application_jenkins_jobs in application_jenkins_jobs_queryset:
            build_list = list()
            for application_jenkins_jobs in ApplicationJenkinsJobBuildModel.fetch_all(job=application_jenkins_jobs):
                build_list.append(application_jenkins_jobs.to_dict())

            app_job_list.append({"app_job": application_jenkins_jobs.to_dict(), "build_list": build_list})
        dt["app_job_list"] = app_job_list
        return dt


# 应用-jenkins job
class ApplicationJenkinsJobsModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    view = db.ReferenceField(ApplicationJenkinsModel, reverse_delete_rule=db.CASCADE)
    job_name = db.StringField(max_length=255, required=True)
    description = db.StringField()
    config = db.StringField(required=False)
    color = db.StringField(max_length=30)
    timestamp = db.StringField(max_length=30)
    result = db.StringField(max_length=50)
    hooks = db.DictField(default={})
    project = db.DictField(default={})
    # 最近一次构建记录相关信息
    last_run_number = db.IntField(null=True)            # number
    last_run_username = db.StringField(null=True)       # 执行人英文名
    last_run_ch_name = db.StringField(null=True)        # 执行人中文名
    last_run_req_source = db.StringField(null=True)     # 执行方式：页面执行、API调用、外部执行
    last_run_app_from = db.StringField(null=True)       # 执行来源：jenkins、pipeline

    last_run_result = db.StringField(null=True)         # 执行结果
    last_run_timestamp = db.StringField(max_length=30, null=True)
    last_run_datetime = db.DateTimeField()              # 执行开始时间
    last_run_duration = db.StringField(null=True)       # 持续时间
    last_run_duration_str = db.StringField(null=True)   # 持续时间（中文）
    last_run_revision = db.StringField(null=True)       # 版本

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job_name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["view"] = self.view.to_dict()
        dt["view_name"] = self.view.jenkins_view_name
        dt["application"] = self.view.application.get_rebuild_dict()
        return dt

    def to_tags_dict(self, user_query=None):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["tags"] = False
        dt["view"] = self.view.to_dict()
        dt["view_name"] = self.view.jenkins_view_name

        if user_query:
            if JenkinsJobTagsModel.fetch_one(user_info=user_query, jenkins_job=self):
                dt["tags"] = True

        return dt

    def to_tags_dict_v2(self, user_query=None, job_code_list=None):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["tags"] = False

        dt["last_run_number"] = self.last_run_number
        dt["last_run_username"] = self.last_run_username
        dt["last_run_ch_name"] = self.last_run_ch_name
        dt["last_run_req_source"] = self.last_run_req_source
        dt["last_run_app_from"] = self.last_run_app_from

        dt["last_run_result"] = self.last_run_result
        dt["last_run_timestamp"] = self.last_run_timestamp
        dt["last_run_datetime"] = self.last_run_datetime
        dt["last_run_duration"] = self.last_run_duration
        dt["last_run_duration_str"] = self.last_run_duration_str
        dt["last_run_revision"] = self.last_run_revision
        dt["application"] = self.view.application.get_rebuild_dict()
        dt["view_name"] = self.view.jenkins_view_name
        if job_code_list:
            dt["can_update"] = self.code in job_code_list[1]
            dt["can_delete"] = self.code in job_code_list[2]
            dt["can_run"] = self.code in job_code_list[3]
            dt["can_stop"] = self.code in job_code_list[4]
            dt["can_log"] = self.code in job_code_list[5]
            dt["can_delete_log"] = self.code in job_code_list[6]
        if user_query.role == 1:
            dt["can_update"] = True
            dt["can_delete"] = True
            dt["can_run"] = True
            dt["can_stop"] = True
            dt["can_log"] = True
            dt["can_delete_log"] = True
        if user_query:
            if JenkinsJobTagsModel.fetch_one(user_info=user_query, jenkins_job=self):
                dt["tags"] = True

        return dt

    def to_tags_dict_v3(self, user_query=None, job_code_list=None):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["tags"] = False
        latest_build_query = ApplicationJenkinsJobBuildModel.objects(job=self).order_by('-datetime').first()
        dt["build"] = latest_build_query.to_job_list_dict() if latest_build_query else {}
        dt["application"] = self.view.application.get_rebuild_dict()
        dt["view_name"] = self.view.jenkins_view_name
        if job_code_list:
            dt["can_update"] = self.code in job_code_list[1]
            dt["can_delete"] = self.code in job_code_list[2]
            dt["can_run"] = self.code in job_code_list[3]
            dt["can_stop"] = self.code in job_code_list[4]
            dt["can_log"] = self.code in job_code_list[5]
            dt["can_delete_log"] = self.code in job_code_list[6]
        if user_query.role == 1:
            dt["can_update"] = True
            dt["can_delete"] = True
            dt["can_run"] = True
            dt["can_stop"] = True
            dt["can_log"] = True
            dt["can_delete_log"] = True
        if user_query:
            if JenkinsJobTagsModel.fetch_one(user_info=user_query, jenkins_job=self):
                dt["tags"] = True

        return dt

    def to_all_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["view"] = self.view.to_dict()
        dt["view_name"] = self.view.jenkins_view_name
        return dt

    def to_base_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job_name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["result"] = self.result
        dt["view_name"] = self.view.jenkins_view_name
        return dt

    def to_home_page(self):
        dt = dict()
        dt["job_name"] = self.job_name
        dt["color"] = self.color
        dt["application"] = self.view.application.to_base_dict() if self.view.application else {}
        dt["view_name"] = self.view.jenkins_view_name
        return dt

    def to_devops_dict(self, user_query=None, job_code_list=None):
        dt = dict()
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["view"] = self.view.to_dict()
        dt["view_name"] = self.view.jenkins_view_name
        dt["application"] = self.view.application.get_rebuild_dict()

        dt["last_run_number"] = self.last_run_number
        dt["last_run_username"] = self.last_run_username
        dt["last_run_ch_name"] = self.last_run_ch_name
        dt["last_run_req_source"] = self.last_run_req_source
        dt["last_run_app_from"] = self.last_run_app_from

        dt["last_run_result"] = self.last_run_result
        dt["last_run_timestamp"] = self.last_run_timestamp
        dt["last_run_datetime"] = self.last_run_datetime
        dt["last_run_duration"] = self.last_run_duration
        dt["last_run_duration_str"] = self.last_run_duration_str
        dt["last_run_revision"] = self.last_run_revision
        if job_code_list:
            dt["can_update"] = self.code in job_code_list[1]
            dt["can_delete"] = self.code in job_code_list[2]
            dt["can_run"] = self.code in job_code_list[3]
            dt["can_stop"] = self.code in job_code_list[4]
            dt["can_log"] = self.code in job_code_list[5]
            dt["can_delete_log"] = self.code in job_code_list[6]
        if user_query.role == 1:
            dt["can_update"] = True
            dt["can_delete"] = True
            dt["can_run"] = True
            dt["can_stop"] = True
            dt["can_log"] = True
            dt["can_delete_log"] = True
        return dt

    def to_devops_dict_v2(self, user_query=None, job_code_list=None):
        dt = {
            "last_run_number": "",
            "last_run_username": "",
            "last_run_ch_name": "",
            "last_run_req_source": "",
            "last_run_app_from": "",
            "last_run_result": "",
            "last_run_timestamp": "",
            "last_run_datetime": "",
            "last_run_duration": "",
            "last_run_duration_str": "",
            "last_run_revision": "",
        }
        dt["code"] = self.code
        dt["name"] = self.job_name
        dt["color"] = self.color
        # 前端使用的是这个字段，应该使用last_run_timestamp
        # dt["timestamp"] = self.timestamp
        dt["description"] = self.description
        dt["result"] = self.result
        dt["view"] = self.view.to_dict()
        dt["view_name"] = self.view.jenkins_view_name
        dt["application"] = self.view.application.get_rebuild_dict()
        if job_code_list:
            dt["can_update"] = self.code in job_code_list[1]
            dt["can_delete"] = self.code in job_code_list[2]
            dt["can_run"] = self.code in job_code_list[3]
            dt["can_stop"] = self.code in job_code_list[4]
            dt["can_log"] = self.code in job_code_list[5]
            dt["can_delete_log"] = self.code in job_code_list[6]
        if user_query.role == 1:
            dt["can_update"] = True
            dt["can_delete"] = True
            dt["can_run"] = True
            dt["can_stop"] = True
            dt["can_log"] = True
            dt["can_delete_log"] = True

        latest_build_query = ApplicationJenkinsJobBuildModel.objects(job=self).order_by('-datetime').first()
        last_build_dic = latest_build_query.to_job_list_dict() if latest_build_query else {}
        if last_build_dic:
            dt["last_run_number"] = last_build_dic.get("number", "")
            dt["last_run_username"] = last_build_dic.get("username", "")
            dt["last_run_req_source"] = last_build_dic.get("req_source", "")
            dt["last_run_app_from"] = last_build_dic.get("app_from", "")

            dt["last_run_result"] = last_build_dic.get("result", "")
            dt["timestamp"] = last_build_dic.get("timestamp", "")
            dt["last_run_datetime"] = last_build_dic.get("datetime", "")
            dt["last_run_duration"] = last_build_dic.get("duration", "")
            dt["last_run_duration_str"] = last_build_dic.get("duration_str", "")
            dt["last_run_revision"] = last_build_dic.get("revision", "")
        return dt
    
    def to_workbench_rollback_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job_name"] = self.job_name
        dt["description"] = self.description
        dt["view_name"] = self.view.jenkins_view_name if self.view else ""
        return dt

    # 编辑2
    def is_auth_update(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 2 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_2):
                return True
        return False

    # 删除3
    def is_auth_delete(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 3 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_3):
                return True
        return False

    # 执行4
    def is_auth_run(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 4 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_4):
                return True
        return False

    # 终止5
    def is_auth_stop(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 5 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_5):
                return True
        return False

    # 查看日志6
    def is_auth_log(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 6 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_6):
                return True
        return False

    # 删除日志7
    def is_auth_delete_log(self, user_query):
        app_auth_queryset = user_query.get_get_strategy_list_by_user(self.view.application)
        for app_auth_query in app_auth_queryset:
            if app_auth_query.all_select == 1 and 7 in app_auth_query.job_all_select:
                return True
            if (self.code in app_auth_query.auth_job_1) and (self.code in app_auth_query.auth_job_7):
                return True
        return False


# 应用-jenkins build
class ApplicationJenkinsJobBuildModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    job = db.ReferenceField(ApplicationJenkinsJobsModel, reverse_delete_rule=db.CASCADE)
    number = db.IntField(null=True)
    timestamp = db.StringField(max_length=30, null=True)
    datetime = db.DateTimeField()
    datetime_str = db.StringField(null=True)
    duration = db.StringField(null=True)
    duration_str = db.StringField(null=True)
    building = db.BooleanField(null=True)
    revision = db.StringField(max_length=100, null=True)
    result = db.StringField(null=True)
    output = db.StringField(null=True)
    username = db.StringField(null=True)
    ch_name = db.StringField(null=True)
    req_source = db.StringField(null=True)
    app_from = db.StringField(null=True)
    queue_num = db.IntField(null=True)
    is_celery = db.BooleanField(null=True)
    # 存储有并行阶段的脚本
    job_script = db.DictField(null=True)

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job"] = self.job.to_dict()
        dt["number"] = self.number
        dt["is_celery"] = self.is_celery
        dt["timestamp"] = self.timestamp
        dt["datetime"] = self.datetime
        dt["duration"] = self.duration
        dt["duration_str"] = self.duration_str
        dt["building"] = self.building
        dt["revision"] = self.revision
        dt["result"] = self.result
        dt["output"] = self.output
        dt["username"] = self.username
        dt["ch_name"] = self.ch_name
        dt["req_source"] = self.req_source
        dt["app_from"] = self.app_from
        dt["queue_num"] = self.queue_num
        return dt

    def to_job_list_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["number"] = self.number
        dt["timestamp"] = self.timestamp
        dt["datetime"] = self.datetime
        dt["duration"] = self.duration
        dt["duration_str"] = self.duration_str
        dt["building"] = self.building
        dt["revision"] = self.revision
        dt["result"] = self.result
        dt["username"] = self.username
        dt["req_source"] = self.req_source
        dt["app_from"] = self.app_from
        dt["queue_num"] = self.queue_num
        dt["is_celery"] = self.is_celery
        return dt

    def to_home_page(self):
        dt = dict()
        dt["code"] = self.code
        dt["job"] = self.job.to_home_page()
        dt["datetime"] = str(self.datetime).split(".")[0]
        dt["building"] = self.building
        dt["result"] = self.result
        dt["username"] = self.username
        dt["req_source"] = self.req_source
        dt["app_from"] = self.app_from
        dt["queue_num"] = self.queue_num
        return dt

    def get_datetime(self):
        return str(self.datetime).split(".")[0]

    def to_log_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job"] = self.job.to_dict()
        dt["number"] = self.number
        dt["timestamp"] = self.timestamp
        dt["datetime"] = str(self.datetime)
        dt["duration"] = self.duration
        dt["duration_str"] = self.duration_str
        dt["building"] = self.building
        dt["revision"] = self.revision
        dt["result"] = self.result
        dt["output"] = self.output
        dt["username"] = self.username
        dt["ch_name"] = self.ch_name
        dt["req_source"] = self.req_source
        dt["app_from"] = self.app_from
        dt["queue_num"] = self.queue_num
        return dt

    def to_workbench_rollback_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["job"] = self.job.to_workbench_rollback_dict() if self.job else {}
        dt["number"] = self.number
        dt["timestamp"] = self.timestamp
        dt["datetime"] = str(self.datetime)
        dt["duration"] = self.duration
        dt["duration_str"] = self.duration_str
        dt["building"] = self.building
        dt["revision"] = self.revision
        dt["result"] = self.result
        dt["output"] = self.output
        dt["username"] = self.username
        dt["ch_name"] = self.ch_name
        dt["req_source"] = self.req_source
        dt["app_from"] = self.app_from
        dt["api_type"] = "pipeline"
        dt["queue_num"] = self.queue_num
        dt["success"] = None
        if not self.building:
            if self.result == "SUCCESS":
                dt["success"] = True
            else:
                dt["success"] = False
        return dt


# 存放指定构建记录的并行阶段脚本，以及人工确认步骤中input_id对应的确认者
class JobBuildNumberScriptModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    job = db.ReferenceField(ApplicationJenkinsJobsModel, reverse_delete_rule=db.CASCADE, null=True)
    # 构建历史number
    number = db.IntField(null=True)
    # 并行阶段的脚本
    parallel_script = db.DictField(null=True)
    # 等待人工确认的input_id对应的确认者
    input_id_submitter_dic = db.DictField(null=True)

    def to_dict(self):
        dt = {
            "code": self.code,
            "job": self.job.to_dict() if self.job else {},
            "number": self.number,
            "parallel_script": self.parallel_script,
            "input_id_submitter_dic": self.input_id_submitter_dic
        }
        return dt


# 人工确认发送消息通知
class JobBuildInputMessageModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    job = db.ReferenceField(ApplicationJenkinsJobsModel, reverse_delete_rule=db.CASCADE, null=True)
    number = db.IntField(null=True)
    links_log_href = db.StringField(null=True)
    username_dict = db.DictField(null=True)
    # 阶段-等待人工确认状态  1：正在等待确认  2：继续  3：终止
    stage_status = db.StringField(null=True, default="1")


# 大屏数据
class DataForScreenModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    application_count = db.IntField(default=0)
    service_count = db.IntField(default=0)
    count = db.IntField(default=0)
    day = db.StringField()
    detail = db.ListField(default=[])

    def to_dict(self):
        dt = {
            "count": self.count,
            "day": self.day,
            "detail": self.detail
        }
        return dt


# 收藏任务
class JenkinsJobTagsModel(BasicDocument):
    jenkins_job = db.ReferenceField(ApplicationJenkinsJobsModel, required=True, reverse_delete_rule=db.CASCADE)
    user_info = db.ReferenceField(UserInfo, required=True, reverse_delete_rule=db.CASCADE)


# 流水线操作日志
class OperationLogModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    user_username = db.StringField()
    user_ch_name = db.StringField(null=True)
    operation_object_name = db.StringField(null=True)
    operation_object_code = db.IntField(null=True)
    # 1：新建  2：删除    3：编辑    4：流程控制
    operation_type = db.IntField()
    # 1：新建流水线  2：删除流水线    3：基础信息    4：流程配置  5：触发规则  6：参数设置  7：继续执行构建    8：终止执行构建
    operation_detail = db.IntField()
    describe = db.StringField()
    version = db.StringField(max_length=32)  # 修改版本
    before_change_dict = db.DictField(null=True)
    after_change_dict = db.DictField(null=True)
    builds_number = db.StringField(null=True)  # 构建历史number
    # 人工确认-stageFlowNodes.log地址
    execution_log = db.StringField(null=True)

    def to_dict(self):
        dt = {
            "code": self.code,
            "user_username": self.user_username,
            "user_ch_name": self.user_ch_name,
            "operation_object_name": self.operation_object_name,
            "operation_type": self.operation_type,
            "operation_detail": self.operation_detail,
            "describe": self.describe,
            "version": self.version,
            "create_time": str(self.created_at),
            "builds_number": self.builds_number,
            "execution_log": self.execution_log
        }

        return dt

    def to_detail_dict(self):
        dt = {
            "code": self.code,
            "user_username": self.user_username,
            "user_ch_name": self.user_ch_name,
            "operation_object_name": self.operation_object_name,
            "operation_object_code": self.operation_object_code,
            "operation_type": self.operation_type,
            "operation_detail": self.operation_detail,
            "describe": self.describe,
            "version": self.version,
            "create_time": str(self.created_at),
            "before_change_dict": self.before_change_dict,
            "after_change_dict": self.after_change_dict,
            "builds_number": self.builds_number,
            "execution_log": self.execution_log
        }

        return dt


# 持续部署操作日志
class DeployTaskOperationLogModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    user_username = db.StringField()
    user_ch_name = db.StringField(null=True)
    operation_object_name = db.StringField(null=True)
    operation_object_code = db.IntField(null=True)
    clone_operation_object_name = db.StringField(null=True)
    clone_operation_object_code = db.IntField(null=True)
    # 1：新建  2：删除  3：编辑  4：克隆
    operation_type = db.IntField()
    # 1：新建部署任务  2：删除部署任务  3：编辑部署任务（基本信息、部署步骤、参数设置）  4：克隆部署任务
    operation_detail = db.IntField()
    describe = db.StringField()
    version = db.StringField(max_length=32)
    before_change_dict = db.DictField(null=True)
    after_change_dict = db.DictField(null=True)

    def to_dict(self):
        dt = {
            "code": self.code,
            "user_username": self.user_username,
            "user_ch_name": self.user_ch_name,
            "operation_object_name": self.operation_object_name,
            "operation_type": self.operation_type,
            "operation_detail": self.operation_detail,
            "describe": self.describe,
            "version": self.version,
            "create_time": str(self.created_at)
        }

        return dt

    def to_detail_dict(self):
        dt = {
            "code": self.code,
            "user_username": self.user_username,
            "user_ch_name": self.user_ch_name,
            "operation_object_name": self.operation_object_name,
            "operation_object_code": self.operation_object_code,
            "clone_operation_object_name": self.clone_operation_object_name,
            "clone_operation_object_code": self.clone_operation_object_code,
            "operation_type": self.operation_type,
            "operation_detail": self.operation_detail,
            "describe": self.describe,
            "version": self.version,
            "create_time": str(self.created_at),
            "before_change_dict": self.before_change_dict,
            "after_change_dict": self.after_change_dict
        }
        return dt


class GroupModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    group_name = db.StringField(max_length=128, unique=True, null=False)
    description = db.StringField(max_length=255, null=True)
    user_list = db.ListField(db.ReferenceField(UserInfo, null=True))

    def to_base_dict(self):
        dt = {
            "code": self.code,
            "group_name": self.group_name,
            "description": self.description
        }
        return dt

    def to_dict(self):
        dt = dict()
        dt["code"] = self.code
        dt["group_name"] = self.group_name
        dt["description"] = self.description
        dt["user_list"] = [user_query.to_base_dict() for user_query in self.user_list if self.user_list]
        return dt


# 权限策略
class StrategyModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    strategy_name = db.StringField(unique=True, null=True)
    description = db.StringField(max_length=1024, unique=False, null=True)
    quoted_times = db.IntField()
    group_quoted_times = db.IntField()
    user = db.ListField(db.ReferenceField(UserInfo, null=True))
    group = db.ListField(db.ReferenceField(GroupModel, null=True))

    def to_dict(self):
        dt = {
            "code": self.code,
            "strategy_name": self.strategy_name,
            "description": self.description,
            "quoted_times": self.quoted_times,
            "group_quoted_times": self.group_quoted_times
        }
        return dt


class ApplicationAuthModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    strategy = db.ReferenceField(StrategyModel, reverse_delete_rule=db.CASCADE)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE)
    all_select = db.IntField(default=0)
    job_list = db.ListField()       # 存放流水线及对应操作权限
    deploy_list = db.ListField()    # 存放部署任务及对应操作权限
    repo_list = db.ListField()      # 存放制品仓库及对应操作权限
    apm_list = db.ListField()      # 存放APM服务组及对应操作权限
    # 是否为新数据 1：新数据
    new = db.IntField(default=0)

    # 流水线-全部      1：查看  2：编辑  3：删除  4：执行  5：终止  6：查看日志  7.删除日志
    job_all_select = db.ListField()

    # 持续部署-全部    1：查看  2：编辑  3：删除  4：执行  5：终止  6：克隆  7：查看日志  8.删除日志
    deploy_all_select = db.ListField()

    # 制品库-全部      1：查看  2：编辑  3：删除  4：查看文件详情  5：删除文件  6：上传制品  7：下载制品
    repo_all_select = db.ListField()

    # APM服务组-全部      1：查看  2：编辑  3：删除
    apm_all_select = db.ListField()

    """"
    job_list = [
        {
            "job_code": 11,
            "action_list": [1,2,3,4,5]
        },
        {
            "job_code": 12,
            "action_list": [1,2,3,4,5]
        }
    ]
    """

    # 流水线
    auth_job_1 = db.ListField()     # 查看
    auth_job_2 = db.ListField()     # 编辑
    auth_job_3 = db.ListField()     # 删除
    auth_job_4 = db.ListField()     # 执行
    auth_job_5 = db.ListField()     # 终止
    auth_job_6 = db.ListField()     # 查看日志
    auth_job_7 = db.ListField()     # 删除日志

    # 部署任务
    auth_deploy_1 = db.ListField()  # 查看
    auth_deploy_2 = db.ListField()  # 编辑
    auth_deploy_3 = db.ListField()  # 删除
    auth_deploy_4 = db.ListField()  # 执行
    auth_deploy_5 = db.ListField()  # 终止
    auth_deploy_6 = db.ListField()  # 克隆
    auth_deploy_7 = db.ListField()  # 查看日志
    auth_deploy_8 = db.ListField()  # 删除日志 弃用

    # 制品仓库
    auth_repo_1 = db.ListField()    # 查看
    auth_repo_2 = db.ListField()    # 编辑
    auth_repo_3 = db.ListField()    # 删除
    auth_repo_4 = db.ListField()    # 查看文件详情
    auth_repo_5 = db.ListField()    # 删除文件
    auth_repo_6 = db.ListField()    # 上传制品
    auth_repo_7 = db.ListField()    # 下载制品

    auth_apm_1 = db.ListField()    # 查看
    auth_apm_2 = db.ListField()    # 编辑
    auth_apm_3 = db.ListField()    # 删除

    def to_dict(self):
        dt = {
            "code": self.code,
            "strategy_code": self.strategy.code,
            "application_code": self.application.code,
            "all_select": self.all_select,
            "job_all_select": self.job_all_select,
            "deploy_all_select": self.deploy_all_select,
            "repo_all_select": self.repo_all_select,
            "apm_all_select": self.apm_all_select,
        }
        if self.job_list:
            dt["job_list"] = self.job_list
        if self.deploy_list:
            dt["deploy_list"] = self.deploy_list
        if self.repo_list:
            dt["repo_list"] = self.repo_list
        if self.apm_list:
            dt["apm_list"] = self.apm_list
        return dt


# 流水线视图
class JenkinsJobOverAllViewModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    overall_view_name = db.StringField(unique=True)
    overall_view_describe = db.StringField(null=True)
    # 视图权限  1：公开    2：私有
    overall_view_type = db.StringField(default="1")
    overall_view_username = db.StringField(null=True)
    job_code_list = db.ListField()

    def to_base_dict(self):
        dt = {
            "code": self.code,
            "overall_view_name": self.overall_view_name,
            "overall_view_describe": self.overall_view_describe,
            "overall_view_type": self.overall_view_type,
            "overall_view_username": self.overall_view_username,
        }
        return dt

    def to_dict(self):
        dt = {
            "code": self.code,
            "overall_view_name": self.overall_view_name,
            "overall_view_describe": self.overall_view_describe,
            "overall_view_type": self.overall_view_type,
            "overall_view_username": self.overall_view_username,
            "job_code_list": self.job_code_list,
        }
        try:
            if self.overall_view_username:
                dt["overall_view_ch_name"] = UserInfo.fetch_one(username=self.overall_view_username).ch_name
        except Exception as e:
            pass
        return dt

    def to_config_dict(self, user_query):
        dt = {
            "code": self.code,
            "overall_view_name": self.overall_view_name,
            "overall_view_describe": self.overall_view_describe,
            "overall_view_type": self.overall_view_type,
            "overall_view_username": self.overall_view_username,
            "bind": False,
            "can_update": self._check_can_update(user_query)
        }
        try:
            if self.overall_view_username:
                dt["overall_view_ch_name"] = UserInfo.fetch_one(username=self.overall_view_username).ch_name
        except Exception as e:
            pass
        return dt

    def to_overall_view_dict(self, user_query):
        dt = {
            "code": self.code,
            "overall_view_name": self.overall_view_name,
            "overall_view_describe": self.overall_view_describe,
            "overall_view_type": self.overall_view_type,
            "overall_view_username": self.overall_view_username,
            "can_update": self._check_can_update(user_query)
        }
        if user_query.username == self.overall_view_username:
            dt["can_update"] = True
        try:
            if self.overall_view_username:
                dt["overall_view_ch_name"] = UserInfo.fetch_one(username=self.overall_view_username).ch_name
        except Exception as e:
            pass
        return dt

    def _check_can_update(self, user_query):
        if user_query.username == self.overall_view_username:
            return True
        # if self.built_in and user_query.role in [1]:
        #     return True
        return False


# 用户概览页显示
class JenkinsOverallViewUserModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    create_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.CASCADE, null=True, default=None)
    overall_view = db.ReferenceField(JenkinsJobOverAllViewModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    index = db.IntField()


# 应用下-应用交付-流水线分组
class DevOpsPipelineGroupModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    name = db.StringField()
    describe = db.StringField(null=True)
    # 1:公开 2：私有
    type = db.StringField(default="1")
    # 创建人
    create_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.CASCADE, null=True, default=None)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    job_code_list = db.ListField()

    def to_base_dict(self):
        dt = {
            "code": self.code,
            "name": self.name,
            "describe": self.describe,
            "type": self.type,
            "application": self.application.to_base_dict()
        }
        if self.create_user:
            dt["create_user"] = self.create_user.to_base_dict()
        return dt

    def to_dict(self):
        dt = {
            "code": self.code,
            "name": self.name,
            "describe": self.describe,
            "type": self.type,
            "job_code_list": self.job_code_list
        }
        if self.create_user:
            dt["create_user"] = self.create_user.to_base_dict()
        return dt

    def to_config_dict(self, user_query):
        dt = {
            "code": self.code,
            "name": self.name,
            "describe": self.describe,
            "type": self.type,
            "application": self.application.to_base_dict(),
            "bind": False,
            "can_update": self._check_can_update(user_query)
        }
        if self.create_user:
            dt["create_user"] = self.create_user.to_base_dict()
        return dt

    def to_pipeline_group_dict(self, user_query):
        dt = {
            "code": self.code,
            "name": self.name,
            "describe": self.describe,
            "type": self.type,
            "application": self.application.to_base_dict(),
            "can_update": self._check_can_update(user_query)
        }
        if self.create_user:
            dt["create_user"] = self.create_user.to_base_dict()
        return dt

    def _check_can_update(self, user_query):
        if not self.create_user:
            return False
        if user_query == self.create_user:
            return True
        return False


class DevOpsPipelineGroupUserModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    application = db.ReferenceField(ApplicationModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    create_user = db.ReferenceField(UserInfo, reverse_delete_rule=db.CASCADE, null=True, default=None)
    pipeline_group = db.ReferenceField(DevOpsPipelineGroupModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    index = db.IntField()


# 刷新按钮
class RefreshJobModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    view = db.ReferenceField(ApplicationJenkinsModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    job = db.ReferenceField(ApplicationJenkinsJobsModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    # 1：还未执行同步  2：正在执行同步操作
    status = db.StringField(null=True, default="1")


# 同步正在执行的流水线
class SyncBuildingJobModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    view = db.ReferenceField(ApplicationJenkinsModel, reverse_delete_rule=db.CASCADE, null=True, default=None)
    job_name = db.StringField(null=True, default=None)
    # 1：还未执行同步  2：正在执行同步操作
    status = db.StringField(null=True, default="1")

    def to_dict(self):
        dt = {
            "code": self.code,
            "view": self.view.to_dict() if self.view else {},
            "job_name": self.job_name,
            "status": self.status
        }
        return dt


# 定时任务（同步Jenkins任务）
class AutoSyncJenkinsDataModel(BasicDocument):
    code = db.SequenceField(primary_key=True)
    name = db.StringField()
    minute = db.IntField(default=5)
    enable = db.BooleanField()

    def to_dict(self):
        dt = {
            "code": self.code,
            "name": self.name,
            "minute": self.minute,
            "enable": self.enable
        }
        return dt
