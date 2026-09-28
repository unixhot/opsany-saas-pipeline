import json

from django.http import JsonResponse
from component.base_views import BaseObject
from pipeline.utils import constant
from component.libs import GetUserInfo
from component.status_code import success, SuccessStatusCode, error, ErrorStatusCode
from pipeline.models import ApplicationJenkinsModel, ApplicationJenkinsJobsModel, ToolsModel, ApplicationModel, \
    ApplicationJenkinsJobBuildModel
from pipeline.utils.jenkins_api import JenkinsApi


default_pipeline = """pipeline {
  agent {
    label 'opsany'
  }
  stages {
    stage('Jenkins_Job_Runing') {
      steps {
        sh 'cd /data/script &amp;&amp; ./%s.build %s'
      }
    }
  }
}
"""


class BatchCreateScript(BaseObject):
    def batch_create_jobs_old(self, request):
        application_name_list = []
        uat_jobs = {}
        pro_jobs = {}
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
        import time

        error_app_list = []
        success_app_list = []
        # 创建文件夹
        for app_name in application_name_list:
            try:
                data = jenkins_api.create_folder(app_name)
                if data.get("status"):
                    success_app_list.append(app_name)
                else:
                    error_app_list.append(app_name)
            except Exception as e:
                error_app_list.append(app_name)
                print("创建文件夹{}失败，Error：{}".format(app_name, str(e)))

        success_job_uat_zuhou_list = []
        error_job_uat__zuhoulist = []
        # 创建流水线（Uat环境租后系统）
        a = time.time()
        print("开始创建流水线（Uat环境租后系统）")
        for uat_job in uat_jobs.get("租后业务系统"):
            try:
                application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name="zuhouyewuxitong")
                config = """<?xml version="1.0" encoding="utf-8"?>
<flow-definition plugin="workflow-job@1268.v6eb_e2ee1a_85a"><actions></actions><description></description><keepDependencies>false</keepDependencies><properties><com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.6.0"><gitLabConnection></gitLabConnection></com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty></properties><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3606.v0b_d8b_e512dcf"><script>pipeline {
  agent {
    label 'opsany'
  }
  stages {
    stage('Jenkins_Job_Runing') {
      steps {
        sh 'cd /data/script &amp;&amp; ./tianyi.build CIMC_APP_JAR_ALL'
      }
    }

  }
}</script><sandbox>true</sandbox></definition><triggers></triggers><disabled>false</disabled></flow-definition>"""
                config_xml_ = config.replace("CIMC_APP_JAR_ALL", uat_job)

                create_dic = {
                    "name": "Uat环境-" + uat_job,
                    "config_xml": config_xml_,
                    "folder_name": "zuhouyewuxitong"
                }
                data = jenkins_api.create_job(**create_dic)
                if data.get("status"):
                    job_query = ApplicationJenkinsJobsModel.create(view=application_jenkins_query,
                                                                   job_name="Uat环境-" + uat_job,
                                                                   color="notbuilt")
                    success_job_uat_zuhou_list.append(uat_job)
                # else:
                #     error_job_uat__zuhoulist.append(uat_job)
            except Exception as e:
                error_job_uat__zuhoulist.append(uat_job)
                print("创建流水线{}失败，Error：".format(uat_job, str(e)))
        b = time.time()
        print("创建流水线（Uat环境租后系统）耗时：", b - a)

        success_job_uat_zuqian_list = []
        error_job_uat__zuqianlist = []
        # 创建流水线（Uat环境租前系统）
        print("开始创建流水线（Uat环境租前系统）")
        a1 = time.time()
        for uat_job in uat_jobs.get("小微业务系统（生产）/租前系统"):
            try:
                application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name="zuqianxitong")
                config = """<?xml version="1.0" encoding="utf-8"?>
                <flow-definition plugin="workflow-job@1268.v6eb_e2ee1a_85a"><actions></actions><description></description><keepDependencies>false</keepDependencies><properties><com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.6.0"><gitLabConnection></gitLabConnection></com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty></properties><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3606.v0b_d8b_e512dcf"><script>pipeline {
                  agent {
                    label 'opsany'
                  }
                  stages {
                    stage('Jenkins_Job_Runing') {
                      steps {
                        sh 'cd /data/script &amp;&amp; ./tianyi.build CIMC_APP_JAR_ALL'
                      }
                    }

                  }
                }</script><sandbox>true</sandbox></definition><triggers></triggers><disabled>false</disabled></flow-definition>"""
                config_xml_ = config.replace("CIMC_APP_JAR_ALL", uat_job)

                create_dic = {
                    "name": "Uat环境-" + uat_job,
                    "config_xml": config_xml_,
                    "folder_name": "zuqianxitong"
                }

                data = jenkins_api.create_job(**create_dic)
                if data.get("status"):
                    job_query = ApplicationJenkinsJobsModel.create(view=application_jenkins_query,
                                                                   job_name="Uat环境-" + uat_job,
                                                                   color="notbuilt")
                    success_job_uat_zuqian_list.append(uat_job)
                # else:
                #     error_job_uat__zuqianlist.append(uat_job)
            except Exception as e:
                error_job_uat__zuqianlist.append(uat_job)
                print("创建流水线{}失败，Error：".format(uat_job, str(e)))
        b1 = time.time()
        print("创建流水线（Uat环境租前系统）耗时：", b1 - a1)


        success_job_pro_zuhou_list = []
        error_job_pro_zuhou_list = []
        # 创建流水线（生产环境租后系统）
        print("开始创建流水线（生产环境租后系统）")
        a2 = time.time()
        for pro_job in pro_jobs.get("租后业务系统"):
            try:
                application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name="zuhouyewuxitong")
                config = """<?xml version="1.0" encoding="utf-8"?>
                                <flow-definition plugin="workflow-job@1268.v6eb_e2ee1a_85a"><actions></actions><description></description><keepDependencies>false</keepDependencies><properties><com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.6.0"><gitLabConnection></gitLabConnection></com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty></properties><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3606.v0b_d8b_e512dcf"><script>pipeline {
                                  agent {
                                    label 'opsany'
                                  }
                                  stages {
                                    stage('Jenkins_Job_Runing') {
                                      steps {
                                        sh 'cd /data/script &amp;&amp; ./ali.build CIMC_APP_JAR_ALL'
                                      }
                                    }

                                  }
                                }</script><sandbox>true</sandbox></definition><triggers></triggers><disabled>false</disabled></flow-definition>"""
                config_xml_ = config.replace("CIMC_APP_JAR_ALL", pro_job)

                create_dic = {
                    "name": "生产环境-" + pro_job,
                    "config_xml": config_xml_,
                    "folder_name": "zuhouyewuxitong"
                }

                data = jenkins_api.create_job(**create_dic)
                if data.get("status"):
                    job_query = ApplicationJenkinsJobsModel.create(view=application_jenkins_query,
                                                                   job_name="生产环境-" + pro_job,
                                                                   color="notbuilt")
                    success_job_pro_zuhou_list.append(pro_job)
                # else:
                #     error_job_pro_zuhou_list.append(pro_job)
            except Exception as e:
                error_job_pro_zuhou_list.append(pro_job)
                print("创建流水线{}失败，Error：".format(pro_job, str(e)))
        b2 = time.time()
        print("创建流水线（生产环境租后系统）耗时：", b2 - a2)


        success_job_pro_zuqian_list = []
        error_job_pro_zuqian_list = []
        # 创建流水线（生产环境租前系统）
        print("开始创建流水线（生产环境租前系统）")
        a3 = time.time()
        for pro_job in pro_jobs.get("小微业务系统（生产）/租前系统"):
            try:
                application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name="zuqianxitong")
                config = """<?xml version="1.0" encoding="utf-8"?>
                <flow-definition plugin="workflow-job@1268.v6eb_e2ee1a_85a"><actions></actions><description></description><keepDependencies>false</keepDependencies><properties><com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.6.0"><gitLabConnection></gitLabConnection></com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty></properties><definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3606.v0b_d8b_e512dcf"><script>pipeline {
                  agent {
                    label 'opsany'
                  }
                  stages {
                    stage('Jenkins_Job_Runing') {
                      steps {
                        sh 'cd /data/script &amp;&amp; ./ali.build CIMC_APP_JAR_ALL'
                      }
                    }

                  }
                }</script><sandbox>true</sandbox></definition><triggers></triggers><disabled>false</disabled></flow-definition>"""
                config_xml_ = config.replace("CIMC_APP_JAR_ALL", pro_job)

                create_dic = {
                    "name": "生产环境-" + pro_job,
                    "config_xml": config_xml_,
                    "folder_name": "zuqianxitong"
                }

                data = jenkins_api.create_job(**create_dic)
                if data.get("status"):
                    job_query = ApplicationJenkinsJobsModel.create(view=application_jenkins_query,
                                                                   job_name="生产环境-" + pro_job,
                                                                   color="notbuilt")
                    success_job_pro_zuqian_list.append(pro_job)
                # else:
                #     error_job_pro_zuqian_list.append(pro_job)
            except Exception as e:
                error_job_pro_zuqian_list.append(pro_job)
                print("创建流水线{}失败，Error：".format(pro_job, str(e)))
        b3 = time.time()
        print("创建流水线（生产环境租前系统）耗时：", b3 - a3)
        data = {
            "Uat环境租前系统": {"成功数量": len(success_job_uat_zuqian_list), "成功": success_job_uat_zuqian_list, "失败": error_job_uat__zuqianlist},
            "Uat环境租后系统": {"成功数量": len(success_job_uat_zuhou_list), "成功": success_job_uat_zuhou_list, "失败": error_job_uat__zuhoulist},
            "生产环境租前系统": {"成功数量": len(success_job_pro_zuqian_list), "成功": success_job_pro_zuqian_list, "失败": error_job_pro_zuqian_list},
            "生产环境租后系统": {"成功数量": len(success_job_pro_zuhou_list), "成功": success_job_pro_zuhou_list, "失败": error_job_pro_zuhou_list},
        }
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, data, language=self.ops_language()))

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

    def batch_create_jobs(self, request):
        """
        # 参数案例
        jobs = {
            "zuhouyewuxitong": [
                {
                    "env": "uat",
                    "script_name": "tianyi",
                    "startswith": "Uat环境-",
                    "job_name_list": ["HUXINGQI-uat1", "HUXINGQI-uat2"],
                },
                {
                    "env": "pro",
                    "script_name": "ali",
                    "startswith": "Pro环境-",
                    "job_name_list": ["HUXINGQI-pro1", "HUXINGQI-pro2"],
                }
            ],
            "zuqianxitong": [
                {
                    "env": "uat",
                    "script_name": "tianyi",
                    "startswith": "Uat环境-",
                    "job_name_list": ["HU27-uat1", "HU27-uat2"],
                },
                {
                    "env": "pro",
                    "script_name": "ali",
                    "startswith": "Pro环境-",
                    "job_name_list": ["HU27-pro1", "HU27-pro2"],
                }
            ]
        }

        :param request:
        :return:
        """

        # 校验工具
        data = json.loads(request.body)
        jobs = data.get('jobs') or {}
        pipeline = data.get('pipeline') or ""
        if not pipeline:
            pipeline = default_pipeline
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
            return JsonResponse(error(ErrorStatusCode.DATA_NOT_EXISTED, custom_message=messages, language=self.ops_language()))
        else:
            plugin_version_dic = message
        empty_config = constant.CREATE_JOB_EMPTY_CONFIG

        error_message = []
        success_message = []
        for app_name, job_list in jobs.items():
            app_query = ApplicationModel.fetch_one(data__APPLICATION_name=app_name)
            if not app_query:
                error_message.append("获取应用失败：当前应用 {} 不存在！".format(app_name))
                continue
            jenkins_api.create_folder(app_name)
            application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=app_name)

            for job in job_list:
                script_name = job.get("script_name")
                startswith = job.get("startswith") or ""
                job_name_list = job.get("job_name_list") or []
                for job_name in job_name_list:
                    res_job_name = startswith + job_name
                    create_job_dict = {
                        "view": application_jenkins_query,
                        "job_name": res_job_name,
                    }
                    job_query = ApplicationJenkinsJobsModel.fetch_one(job_name=res_job_name)
                    if not job_query:
                        create_job_dict.update(color="notbuilt")
                        job_query = ApplicationJenkinsJobsModel.create(**create_job_dict)
                    else:
                        job_query.update(**create_job_dict)
                    create_dic = {
                        "name": res_job_name,
                        "config_xml": empty_config.format(
                            workflow_job=plugin_version_dic.get("workflow-job", ""),
                            description="批量导入",
                            gitlab_plugin=plugin_version_dic.get("gitlab-plugin", ""),
                            workflow_cps=plugin_version_dic.get("workflow-cps", ""),
                            config_xml=pipeline % (script_name, job_name)),
                        "folder_name": app_name
                    }
                    res = jenkins_api.create_job(**create_dic)
                    if not res.get("status"):
                        message = res.get("message")[0]
                        try:
                            message = message.value[2].get("chinese_simplified")
                        except:
                            pass
                        error_message.append("添加流水线失败：当前应用 {} 创建流水线 {} 失败，原因 {}！".format(app_name, res_job_name, message))
                    else:
                        success_message.append("添加成功，应用：{} 流水线 {}".format(app_name, res_job_name))
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, [success_message, error_message]))


class TestV2(BaseObject):
    def get_test(self, request):
        job_code_list = [1848, 1849, 1851]
        job_query_list = []
        for i in job_code_list:
            build_query = ApplicationJenkinsJobsModel.fetch_one(code=i)
            job_query_list.append(build_query)
        job_queryset = ApplicationJenkinsJobsModel.fetch_all(code__in=job_code_list)
        job_query_list.extend(job_queryset)
        return JsonResponse(success(SuccessStatusCode.MESSAGE_GET_SUCCESS, {}, language=self.ops_language()))