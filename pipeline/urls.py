# -*- coding: utf-8 -*-
"""
Copyright © 2012-2020 OpsAny. All Rights Reserved.
"""  # noqa
from django.urls import path
from pipeline import views, gitlab_views, views_esb
from pipeline import base_views

urlpatterns = [
    path("get-menu/", base_views.DeployMenuStrategyCtrl.as_view()),  # 获取导航拦
    path("guide/", base_views.GuideCtrl.as_view()),  # 获取导航拦
    path('user_info/', base_views.GetUserInfoCtrl.as_view()),  # 获取用户信息
    path("get-nav-and-collection/", base_views.GetNavCollectionView.as_view()),  # 获取导航收藏
    path("collection/", base_views.CollectionNavView.as_view()),  # 收藏操作
    path("get-user-message/", base_views.GetUserMessageView.as_view()),  # 获取站内信
    path("read-all-message/", base_views.ReadAllMessageView.as_view()),  # 全部已读操作
    path("copyright-config/", base_views.CopyrightConfigView.as_view()),  # 底部版权信息
    path("home-page/", base_views.HomePageView.as_view()),
    path("home-page-seven/", base_views.HomePageSevenJobView.as_view()),  # 概览页七天内
    path("home-page-used-app/", base_views.HomePageFrequentUsedAppView.as_view()),  # 概览页频繁使用
    path("update-director/", base_views.UpdateDirectorView.as_view()),  # 被动同步rbac用户到本地

    path("business-tree/", base_views.BusinessTreeView.as_view()),  # 业务树
    path("business-tree-v2/", base_views.BusinessTreeV2View.as_view()),  # 业务树(创建流水线使用)
    path("host-inst/", base_views.GetHostInstView.as_view()),  # 主机列表（管控）
    path("host-inst-group/", base_views.GetHostGroupView.as_view()),  # 主机分组（管控）

    path("pipeline/", base_views.FlashDataView.as_view()),  # 同步相关数据
    path("sync_cron_task/", base_views.SyncCronTaskView.as_view()),     # 同步Jenkins定时任务
    path("update-cron-task/", base_views.UpdateCronTaskView.as_view()),  # 更新Jenkinsi定时任务
    path("pipeline-build/", base_views.FlashDataBuildView.as_view()),   # 同步某条流水线下面的构建记录

    path("test/", views.TestView.as_view()),
    path("test-v2/", views.TestV2View.as_view()),
    path("batch-import-pipeline/", views.BatchImportPipelineView.as_view()),
    path("jenkins/refresh/", views.JenkinsRefreshView.as_view()),
    path("jenkins/credentials-type/", views.JenkinsCredentialsTypeView.as_view()),
    path("jenkins/credentials/", views.JenkinsCredentialsView.as_view()),
    path("jenkins/job/", views.JenkinsJobView.as_view()),  # 获取全部流水线以及当前构建历史

    # 新建流水线视图/分组相关接口
    path("get-app-pipeline-group/", views.PipelineGroupView.as_view()),         # 应用下流水线分组(应用视图)
    path("pipeline-overall-view/", views.PipelineOverallViewView.as_view()),    # 流水线视图(全局视图)

    path("jenkins-job/", views.JenkinsJobRebuiltView.as_view()),     # 流水线页面重构
    path("jenkins/job/build/", views.JenkinsJobBuildView.as_view()),    # 获取指定流水线构建历史             查看日志

    path("sync-pipelines/", views.RefreshPipelinesView.as_view()),  # 更新正在执行的流水线
    path("refresh-jenkins-jobs/", views.RefreshJenkinsJobView.as_view()),       # 刷新
    path("jenkins/job/building-queue-internal/", views.CheckQueueInternalView.as_view()),   # 获取指定流水线的构建状态

    path("jenkins/job/tags/", views.JenkinsJobTagsView.as_view()),  # 收藏流水线
    path("jenkins/job/building-queue/", views.CheckQueueView.as_view()),  # 获取构建队列
    path("jenkins/all-job/", views.JenkinsJobListView.as_view()),
    path("jenkins/job/rename/", views.JenkinsJobRenameView.as_view()),  # 修改流水线名称                   编辑-基础信息
    path("jenkins/job/redescription/", views.JenkinsJobDescriptionView.as_view()),  # 修改流水线描述
    path("jenkins/job/reconfig/script/", views.JenkinsJobReconfigScriptView.as_view()),  # 修改流水线配置-脚本       编辑-流程配置
    path("jenkins/job/reconfig/triggers/", views.JenkinsJobReconfigTriggersView.as_view()),  # 修改流水线配置-触发   编辑-触发规则
    path("jenkins/job/reconfig/parameter/", views.JenkinsJobParametersView.as_view()),  # 修改参数配置-参数          编辑-参数设置
    path("trigger-build-params/", views.TriggerBuildParamsView.as_view()),
    path("jenkins/job/check-syntax/", views.JenkinsCheckPipelineView.as_view()),  # 检查jenkinsfile语法
    path("jenkins/job/to-json/", views.JenkinsFileToJsonView.as_view()),  # jenkinsfile代码转json
    path("jenkins/job/to-jenkinsfile/", views.JenkinsToJenkinsFileView.as_view()),  # json转jenkinsfile
    path("jenkins/job/pipeline-template-group/", views.PipelineTemplateGroupView.as_view()),  # 流水线模板分组
    path("jenkins/job/pipeline-template/", views.PipelineTemplateView.as_view()),  # 流水线模板
    path("jenkins/job/pipeline-template/copy/", views.CopyPipelineTemplateView.as_view()),  # 复制模板
    path("jenkins/job/pipeline-tool/", views.JenkinsPipelineToolView.as_view()),  # 修改配置内置工具
    path("jenkins/job/pipeline-tool-post/", views.JenkinsPipelineToolPostView.as_view()),  # 修改配置内置工具

    path("jenkins/job/build/status/", views.JenkinsJobBuildStatusView.as_view()),  # 获取构建状态
    path("jenkins/job/build/start/", views.JenkinsJobBuildStartView.as_view()),  # 开始构建
    path("jenkins/job/build/proceed/", views.JenkinsJobBuildProceedEmptyView.as_view()),  # 人工确认-继续
    path("jenkins/job/build/abort/", views.JenkinsJobBuildAbortView.as_view()),  # 人工确认-终止
    path("jenkins/job/build/stop/", views.JenkinsJobBuildStopView.as_view()),  # 停止构建
    path("jenkins/job/build/delete/", views.JenkinsJobBuildDeleteView.as_view()),  # 删除构建历史
    path("jenkins/job/build-info/", views.JenkinsJobBuildInfoView.as_view()),  # 查看构建历史详情
    path("jenkins-job-input/", views.JenkinsJobInputView.as_view()),        # 任务卡点-人工确认
    path("users/", views.UsersView.as_view()),                              # 获取所有的用户
    path("jenkins/job/stages/", views.JenkinsJobStagesView.as_view()),      # 获取构建历史(按照阶段来区分)
    path("jenkins/job/stage-logs/", views.JenkinsJobStageLogsView.as_view()),       # 获取构建历史指定阶段日志
    path("jenkins/job/paraller-script/", views.JenkinsJobScriptView.as_view()),
    path("jenkins/job/building-job/", views.JenkinsJobBuildingJobView.as_view()),

    # 视图（用于流水线分组）
    path("jenkins/overall-jobs/", views.JenkinsOverallJobsView.as_view()),            # 所有的流水线（过权限策略）
    path("jenkins/job/overall-views/", views.JenkinsOverallViewsView.as_view()),      # 用户所关联的视图
    path("jenkins/job/overall-view/", views.JenkinsOverallViewView.as_view()),        # 视图详情（编辑视图用到）
    path("jenkins/job/overall-ivew-v2/", views.JenkinsOverallViewsV2View.as_view()),  # 视图管理界面

    path("gitlab/group/", gitlab_views.GitLabGroupView.as_view()),
    path("gitlab/all-projects/", gitlab_views.GitLabAllProjectView.as_view()),
    path("gitlab/projects/", gitlab_views.GitLabProjectView.as_view()),
    path("gitlab/project/branch/", gitlab_views.GitLabProjectBranchView.as_view()),
    path("gitlab/project/hooks/", gitlab_views.GitLabProjectHooksView.as_view()),

    path("jenkins/jobs/", views.JenkinsJobsView.as_view()),  # jenkins流水线

    path("tool/", views.ToolView.as_view()),                                    # Nexus工具CRUD
    path("tool/status/", views.ToolStatusView.as_view()),                       # 测试状态、工具列表刷新
    path("tool/jenkins/test/", views.ToolTestJenkinsView.as_view()),            # 添加工具连接测试jenkins
    path("tool/git/test/", views.ToolTestGitView.as_view()),                    # 添加工具连接测试git

    # 新增步骤--获取自己参与的项目且成员角色大于开发者的项目地址列表
    path("gitlab-repository-url/", views.GitlabRepositoryUrlView.as_view()),
    path("get-nexus-repository/", views.NexusRepositoryView.as_view()),         # 获取当前应用下或公共的raw类型仓库
    path("get-nexus-version/", views.NexusRepositoryVersionView.as_view()),     # 查询Nexus存储库管理器的版本
    path("create-or-update-nexus-credential/", views.NexusCredentialView.as_view()),    # 创建或更新Nexus凭据

    # 操作审计
    path("get-operation-audit/", views.OperationAduitView.as_view()),           # 操作审计
    path("get-operation-log/", views.OperationLogView.as_view()),               # 操作审计详情

    # esb接口：应用平台嵌入页面接口
    path("get-home-page/", views_esb.GetHomePageView.as_view()),                                    # 获取流水线资源统计数量
    path("get-pipeline-jenkins-job/", views_esb.GetPipelineJenkinsJobView.as_view()),               # 获取当前应用下的流水线
    
    # 工作台API管理
    path("api/run-pipeline-v1/", views_esb.RunPipelineV1View.as_view()),                            # 执行流水线
    path("api/run-pipeline-v2/", views_esb.RunPipelineV2View.as_view()),                            # 执行流水线(批量)
    path("api/run-pipeline-v3/", views_esb.RunPipelineV3View.as_view()),                            # 执行流水线-内部调用(工单)
    path("api/run-pipeline-task-rollback/", views_esb.RunPipelineTaskRollbackView.as_view()),       # 执行流水线-内部调用(工单)-执行状态回调
]
