# -*- coding: utf-8 -*-
"""
Copyright © 2012-2020 OpsAny. All Rights Reserved.
"""
from django.urls import path

from pipeline import views_esb, base_views

urlpatterns = [
    # get:sync_user_info
    path("update-director/", base_views.UpdateDirectorView.as_view()),  # 被动同步rbac用户到本地
    # get:get_home_page
    path("get-home-page/", views_esb.GetHomePageView.as_view()),  # 获取流水线资源统计数量
    # get:get_pipeline_jenkins_job
    path("get-pipeline-jenkins-job/", views_esb.GetPipelineJenkinsJobView.as_view()),  # 获取当前应用下的流水线
    # get:run_pipeline_task_v3
    path("api/run-pipeline-v3/", views_esb.RunPipelineV3View.as_view()),  # 执行流水线-内部调用(工单)
    # get:run_pipeline_task_rollback
    path("api/run-pipeline-task-rollback/", views_esb.RunPipelineTaskRollbackView.as_view()),  # 执行流水线-内部调用(工单)-执行状态回调
]
