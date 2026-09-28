# 工具连接状态正常
TOOL_LINK_STATUS_SUCCESS = "正常"
# 工具连接状态异常
TOOL_LINK_STATUS_ERROR = "异常"
# 工具类型 , ('SonarQube', '代码质量')
TOOL_TYPE_LIST = [('jenkins', '持续交付'), ('git', '代码仓库'), ('repository', '制品库')]

# ('gitlab-plugin', 'GitLab Plugin')  ('workflow-job', 'Pipeline: Job') ('workflow-cps', 'Pipeline: Groovy')
# ("favorite  ", "Favorite  ")  ('pipeline-stage-view', 'Pipeline: Stage View Plugin')
JENKINS_REQUIRED_PLUGIN = ["gitlab-plugin", "workflow-job", "workflow-cps", "pipeline-stage-view"]

# 制品库类型
REPOSITORY_TYPE_LIST = [("raw", "raw"), ("maven2", "maven2"), ("docker", "docker"), ("pypi", "pypi")]
REPOSITORY_FORMAT = ("raw", "pypi", "maven2", "docker")

FOLDER_CLASS = "com.cloudbees.hudson.plugins.folder.Folder"
JOB_CLASS = "org.jenkinsci.plugins.workflow.job.WorkflowJob"

# jenkins配置文件常用key
FLOW_KEY = "flow-definition"
# 丢弃策略
BUILD_DISCARD = "jenkins.model.BuildDiscarderProperty"
# 构建key
TRIGGERS_JOB_KEY = "org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty"
# 其他工程构建key
REVERSE_BUILD_TRIGGERS = "jenkins.triggers.ReverseBuildTrigger"
# 定时构建key
TIME_TRIGGERS = "hudson.triggers.TimerTrigger"
# gitlab触发构建key
PUSH_TRIGGERS_KEY = "com.dabsquared.gitlabjenkins.GitLabPushTrigger"
# 构建参数
PARAMETERS = "hudson.model.ParametersDefinitionProperty"
# 参数分类-字符，单选
PARAMETERS_DEFINITIONS = "parameterDefinitions"

# 凭据名称获取序号
CREDENTIALS_TYPE = {
    "Username with password": 0,
    "GitHub App": 1,
    "GitLab API token": 2,
    "OpenShift Username and Password": 3,
    "SSH Username with private key": 4,
    "Secret file": 5,
    "Secret text": 6,
    "X.509 Client Certificate": 7,
    "Certificate": 8
}

# 凭据类型列表
CREDENTIALS_TYPE_LIST = [
    {
        "name": "Jenkins",
        "type_list": [
            {
                "id": 0,
                "name": "Username with password",
                "ch_name": "密码验证",
                "fields": {"storage_type": "存储", "type": "类型", "name": "名称", "credentials_id": "唯一标识",
                           "username": "用户名", "password": "密码", "description": "描述"}
            },
            {
                "id": 2,
                "name": "GitLab API token",
                "ch_name": "GitLab令牌",
                "fields": {"storage_type": "存储", "type": "类型", "name": "名称", "credentials_id": "唯一标识",
                           "apiToken": "令牌", "description": "描述"}
            },
            {
                "id": 4,
                "name": "SSH Username with private key",
                "ch_name": "SSH密钥验证",
                "fields": {"storage_type": "存储", "type": "类型", "name": "名称", "credentials_id": "唯一标识",
                           "username": "用户名", "privateKey": "密钥", "passphrase": "密码", "description": "描述"}
            },
            {
                "id": 6,
                "name": "Secret text",
                "ch_name": "密钥文本",
                "fields": {"storage_type": "存储", "type": "类型", "name": "名称", "credentials_id": "唯一标识",
                           "secret": "密钥", "description": "描述"}
            }
        ]
    },
]

# 触发构建相关字段
trigger_build_params = [
    {
        "key": "triggerOnPush",
        "description": "Push Events 代码更新时自动执行",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOnMergeRequest",
        "description": "Opened Merge Request Events 合并请求时触发构建",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOnAcceptedMergeRequest",
        "description": "Accepted Merge Request Events",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOnClosedMergeRequest",
        "description": "Closed Merge Request Events",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOpenMergeRequestOnPush",
        "description": "Rebuild open Merge Requests",
        # Never On push to source branch On push to source or target branch
        "options": ["never", "source", "both"]
    },
    {
        "key": "triggerOnApprovedMergeRequest",
        "description": "Approved Merge Requests (EE-only)",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOnNoteRequest",
        "description": "Comment",
        # 输入框
        "options": ["true", "false"]
    },
    {
        "key": "noteRegex",
        "description": "Comment (regex) for triggering a build",
        # 输入框
        "options": "text"
    },
    {
        "key": "ciSkip",
        "description": "Enable [ci-skip]",
        "options": ["true", "false"]
    },
    {
        "key": "skipWorkInProgressMergeRequest",
        "description": "Ignore WIP Merge Requests",
        "options": ["true", "false"]
    },
    {
        "key": "setBuildDescription",
        "description": "Set build description to build cause (eg. Merge request or Git Push )",
        "options": ["true", "false"]
    },
    {
        "key": "triggerOnPipelineEvent",
        "description": "Build on successful pipeline events",
        "options": ["true", "false"]
    },
    {
        "key": "branchFilterType",
        "description": "Allowed branches",
        # Allow all branches to trigger this job,
        # Filter branches by name(includeBranchesSpec--Include, excludeBranchesSpec--Exclude),
        # Filter branches by regex(sourceBranchRegex--Source Branch Regex, targetBranchRegex--Target Branch Regex),
        "options": ["All", "NameBasedFilter", "RegexBasedFilter", ]
    },
    {
        "key": "includeBranchesSpec",
        "description": "Filter branches by name",
        "options": "input develop"
    },
    {
        "key": "excludeBranchesSpec",
        "description": "Filter branches by name",
        "options": "input develop"
    },
    {
        "key": "sourceBranchRegex",
        "description": "Filter branches by regex",
        "options": "input Regex"
    },
    {
        "key": "targetBranchRegex",
        "description": "Filter branches by regex",
        "options": "input Regex"
    },
    {
        "key": "mergeRequestLabelFilterConfig",
        "description": "Filter merge request by label",
        "options": {"include": "input text", "exclude": "input text"}
    },
    {
        "key": "secretToken",
        "description": "Secret token",
        "options": "input Secret token api",
    },
    {
        "key": "pendingBuildName",
        "description": "Pending build name for pipeline",
        "options": "input name"
    },
    {
        "key": "cancelPendingBuildsOnUpdate",
        "description": "Pending build name for pipeline",
        "options": ["true", "false"]
    },
]

# jenkins流水线配置模板
XML_DEMO = """<?xml version=\'1.1\' encoding=\'UTF-8\'?>\n<flow-definition plugin="workflow-job@2.40">\n  <actions/>\n  <description></description>\n  <keepDependencies>false</keepDependencies>\n  <properties>\n    <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.5.13">\n      <gitLabConnection></gitLabConnection>\n    </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>\n  </properties>\n  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.87">\n    <script>pipeline {\n    agent any\n\n    stages {\n        stage(&apos;Hello OpsAny&apos;) {\n            steps {\n                echo &apos;Hello OpsAny&apos;\n            }\n        }\n    }\n}\n</script>\n    <sandbox>true</sandbox>\n  </definition>\n  <triggers/>\n  <disabled>false</disabled>\n</flow-definition>"""

# 新建流水线空配置文件
CREATE_JOB_EMPTY_CONFIG = """<?xml version=\'1.1\' encoding=\'UTF-8\'?>\n<flow-definition plugin="workflow-job@{workflow_job}">\n  <actions/>\n  <description>{description}</description>\n  <keepDependencies>false</keepDependencies>\n  <properties>\n    <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@{gitlab_plugin}">\n      <gitLabConnection></gitLabConnection>\n    </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>\n  </properties>\n  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@{workflow_cps}">\n    <script>{config_xml}</script>\n    <sandbox>true</sandbox>\n  </definition>\n  <triggers/>\n  <disabled>false</disabled>\n</flow-definition>"""

# 新建视图空配置文件
EMPTY_VIEW_CONFIG_XML = """<?xml version="1.1" encoding="UTF-8"?>\n<hudson.model.ListView>\n  <name>EMPTY</name>\n  <filterExecutors>false</filterExecutors>\n  <filterQueue>false</filterQueue>\n  <properties class="hudson.model.View$PropertyList"/>\n  <jobNames>\n    <comparator class="hudson.util.CaseInsensitiveComparator"/>\n  </jobNames>\n  <jobFilters/>\n  <columns>\n    <hudson.views.StatusColumn/>\n    <hudson.views.WeatherColumn/>\n    <hudson.views.JobColumn/>\n    <hudson.views.LastSuccessColumn/>\n    <hudson.views.LastFailureColumn/>\n    <hudson.views.LastDurationColumn/>\n    <hudson.views.BuildButtonColumn/>\n  </columns>\n  <recurse>false</recurse>\n</hudson.model.ListView>"""
EMPTY_VIEW_CONFIG_XML_V2_3 = """<?xml version="1.1" encoding="UTF-8"?>\n<hudson.model.ListView>\n  <name>qsswe</name>\n  <filterExecutors>false</filterExecutors>\n  <filterQueue>false</filterQueue>\n  <properties class="hudson.model.View$PropertyList"/>\n  <jobNames>\n    <comparator class="java.lang.String$CaseInsensitiveComparator"/>\n  </jobNames>\n  <jobFilters/>\n  <columns>\n    <hudson.views.StatusColumn/>\n    <hudson.views.WeatherColumn/>\n    <hudson.views.JobColumn/>\n    <hudson.views.LastSuccessColumn/>\n    <hudson.views.LastFailureColumn/>\n    <hudson.views.LastDurationColumn/>\n    <hudson.views.BuildButtonColumn/>\n  </columns>\n  <recurse>false</recurse>\n</hudson.model.ListView>'"""
# 视图增加流水线
RECONFIG_VIEW_ADD_JOB = """<hudson.model.ListView><name>{}</name><filterExecutors>false</filterExecutors><filterQueue>false</filterQueue><properties class="hudson.model.View$PropertyList"></properties><jobNames><comparator class="hudson.util.CaseInsensitiveComparator"></comparator><string>{}</string></jobNames><jobFilters></jobFilters><columns><hudson.views.StatusColumn></hudson.views.StatusColumn><hudson.views.WeatherColumn></hudson.views.WeatherColumn><hudson.views.JobColumn></hudson.views.JobColumn><hudson.views.LastSuccessColumn></hudson.views.LastSuccessColumn><hudson.views.LastFailureColumn></hudson.views.LastFailureColumn><hudson.views.LastDurationColumn></hudson.views.LastDurationColumn><hudson.views.BuildButtonColumn></hudson.views.BuildButtonColumn><hudson.plugins.favorite.column.FavoriteColumn plugin="favorite@2.3.3"></hudson.plugins.favorite.column.FavoriteColumn></columns><recurse>false</recurse></hudson.model.ListView>"""
