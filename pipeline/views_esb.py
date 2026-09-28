from django.views import View

from pipeline.utils.pipeline_esb import JenkinsJobBuild, GetHomePage, GetPipelineJenkinsJob


# 开始构建-esb-v1
class RunPipelineV1View(View):
    def post(self, request):
        return JenkinsJobBuild().build_start_esb_v1(request)


# 开始构建-esb-v2
class RunPipelineV2View(View):
    def post(self, request):
        return JenkinsJobBuild().build_start_esb_v2(request)


# 开始构建-esb-v3
class RunPipelineV3View(View):
    def post(self, request):
        return JenkinsJobBuild().build_start_esb_v3(request)


# 构建结果
class RunPipelineTaskRollbackView(View):
    def get(self, request):
        return JenkinsJobBuild().build_start_esb_rollback(request)


# 获取流水线资源统计数量
class GetHomePageView(View):
    def get(self, request):
        return GetHomePage(request).get_home_page(request)


# 获取当前应用下的流水线
class GetPipelineJenkinsJobView(View):
    def get(self, request):
        return GetPipelineJenkinsJob(request).get_pipeline_jenkins_job(request)
