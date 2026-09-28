import datetime
import io
import json
import sys
import time

from mongoengine import Q

from pipeline.models import ApplicationModel, UserJenkinsCredentialsModel
from pipeline.models import ApplicationJenkinsModel, ToolsModel, ApplicationJenkinsJobsModel, \
    ApplicationJenkinsJobBuildModel, DataForScreenModel, JenkinsCredentialsModel
from pipeline.utils import constant
from pipeline.utils.constant import CREDENTIALS_TYPE
from pipeline.utils.filter_data import filter_build_info_data
from pipeline.utils.jenkins_api import JenkinsApi


# 同步jenkins凭据
def jenkins_sync_credentials():
    start = time.time()
    # 校验工具
    tool_query = ToolsModel.fetch_one(tool_type="jenkins")
    if not tool_query:
        return "jenkins tool error"
    if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        return "jenkins status error"

    # 修改没有用户关联的凭据is_private字段的值
    user_credentials_queryset = UserJenkinsCredentialsModel.fetch_all()
    user_credentials_code_list = [i.jenkins_credentials.code for i in user_credentials_queryset if i.jenkins_credentials]
    credentials_queryset = JenkinsCredentialsModel.fetch_all()
    for credentials_query in credentials_queryset:
        credentials_code = credentials_query.code
        if credentials_code not in user_credentials_code_list:
            credentials_query.update(is_private="0")

    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
    data = jenkins_api.get_credentials_list()
    if data.get("status"):
        credentials_dict = data.get("data")

        credentials_list = credentials_dict.get("credentials")
        if credentials_list:
            credentials_id_list = [credential.get("id") for credential in credentials_list]
        else:
            credentials_id_list = []

        for credential in credentials_list:
            dic = {
                # 标准字段
                "credentials_id": credential.get("id"),
                "typeName": credential.get("typeName"),
                "typeCode": CREDENTIALS_TYPE.get(credential.get("typeName")),
                "displayName": credential.get("displayName"),
                "description": credential.get("description"),
                "fullName": credential.get("fullName"),
                "fingerprint": credential.get("fingerprint", {}),
                # 外层字段
                "credentials_class": credentials_dict.get("_class"),
                "credentials_description": credentials_dict.get("description"),
                "credentials_displayName": credentials_dict.get("displayName"),
                "credentials_fullDisplayName": credentials_dict.get("fullDisplayName"),
                "credentials_global": credentials_dict.get("global"),
                "credentials_urlName": credentials_dict.get("urlName"),
            }
            displayName = credential.get("displayName")
            if displayName:
                if constant.CREDENTIALS_TYPE.get(credential.get("displayName")) == 0:
                    pass

            credentials_query = JenkinsCredentialsModel.fetch_one(credentials_id=dic.get("credentials_id"))
            if credentials_query:
                if not credentials_query.name:
                    dic["name"] = dic.get("credentials_id")
                credentials_query.update(**dic)
            else:
                if constant.CREDENTIALS_TYPE.get(dic.get("typeName")) not in [0, 2, 4, 6]:
                    pass
                else:
                    dic["name"] = dic.get("credentials_id")
                    JenkinsCredentialsModel.create(**dic)

        # 删除Jenkins上不存在的凭据
        credentials_queryset = JenkinsCredentialsModel.fetch_all()
        for credentials_query_ in credentials_queryset:
            credentials_id = credentials_query_.credentials_id
            if credentials_id not in credentials_id_list:
                credentials_query_.delete()
        end = time.time()
        print("同步jenkins凭据耗时：", end - start)


# 同步jenkins数据- 耗时2秒左右，有数据6秒左右
def jenkins_sync_data_two():
    """
        同步jenkins数据--同步的是所有应用的job数据
    """
    start = time.time()
    # 校验工具
    tool_query = ToolsModel.fetch_one(tool_type="jenkins")
    if not tool_query:
        return "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
    if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        return "jenkins服务器权限错误，请确认配置!"

    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

    application_jenkins_queryset = ApplicationJenkinsModel.fetch_all()

    for application_jenkins_query in application_jenkins_queryset:
        start1 = time.time()
        view_name = application_jenkins_query.jenkins_view_name

        # 获取全部job(包含当前构建历史)
        result_all_jobs = jenkins_api.get_folder_info(name=view_name)
        if not result_all_jobs.get("status"):
            continue
        all_job = result_all_jobs.get("data", {}).get("jobs")

        # 没有流水线报错
        if not all_job:
            continue

        jenkins_job_query_list = []

        # 获取全部流水线和相关构建日志
        for job in all_job:
            job_name = job.get("name")
            job_color = job.get("color")

            result_config = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
            job_config = result_config.get("data", "")

            job_dic = {"job_name": job_name, "config": job_config, "color": job_color, "view": application_jenkins_query}

            # 获取单条任务详情
            result = jenkins_api.get_job_info(job_name, folder_name=view_name)

            if not result.get("status"):
                continue
            job_info = result.get("data")
            job_info_builds_list = job_info.get("builds", [])
            job_dic["description"] = job_info.get("description", "")

            number = None
            # 获取构建历史
            if job_info_builds_list:
                number = job_info_builds_list[0].get("number")
                result = jenkins_api.get_build_info(name=job_name, number=number, folder_name=view_name)
                if not result:
                    continue
                job_build_info = result.get("data")
                job_dic["timestamp"] = str(job_build_info.get("timestamp", "0"))
                job_dic["result"] = job_build_info.get("result", "")

                # 更新当前job的上次构建相关信息
                if job_build_info:
                    result_build_info = filter_build_info_data(job_build_info)
                    job_dic["last_run_number"] = number
                    job_dic["last_run_result"] = result_build_info.get("result", "")
                    job_dic["last_run_timestamp"] = str(result_build_info.get("timestamp", ""))
                    job_dic["last_run_datetime"] = result_build_info.get("datetime", "")
                    job_dic["last_run_duration"] = str(result_build_info.get("duration", "1"))
                    job_dic["last_run_duration_str"] = result_build_info.get("duration_str", "")
                    job_dic["last_run_revision"] = result_build_info.get("revision", "")

            jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=application_jenkins_query)
            if jenkins_job:
                if not (jenkins_job.last_run_username or jenkins_job.last_run_req_source or
                        jenkins_job.last_run_app_from) and jenkins_job.color != "notbuilt":
                    job_dic["last_run_username"] = "系统执行"
                    job_dic["last_run_ch_name"] = "系统执行"
                    job_dic["last_run_req_source"] = "外部执行"
                    job_dic["last_run_app_from"] = "jenkins"
                if jenkins_job.last_run_number and number and jenkins_job.last_run_number < number:
                    job_dic["last_run_username"] = "系统执行"
                    job_dic["last_run_ch_name"] = "系统执行"
                    job_dic["last_run_req_source"] = "外部执行"
                    job_dic["last_run_app_from"] = "jenkins"
                jenkins_job.update(**job_dic)
            else:
                if job_dic.get("color") != "notbuilt":
                    job_dic["last_run_username"] = "系统执行"
                    job_dic["last_run_ch_name"] = "系统执行"
                    job_dic["last_run_req_source"] = "外部执行"
                    job_dic["last_run_app_from"] = "jenkins"
                jenkins_job = ApplicationJenkinsJobsModel.create(**job_dic)
            jenkins_job_query_list.append(jenkins_job)

            # 获取当条任务构建历史
            build_list = list()
            build_query_list = []
            try:
                # 如果这个任务有处于静默期的记录，就跳过同步这个任务下的构建记录
                queue_id_dic = jenkins_api.get_queue_info()
                data = queue_id_dic.get("data") if queue_id_dic.get("status") else None
                if data == None:
                    print(f"获取静默期记录接口Error：{queue_id_dic.get('message')}")
                    continue
                queue_data = [{
                    "queue_id": i.get("id"),
                    "name": i.get("task", {}).get("name"),
                    "why": i.get("why")
                } for i in data]
                first_match = next((item for item in queue_data if item['name'] == jenkins_job.job_name), None)
                if first_match:
                    print(f"任务【{jenkins_job.job_name}】有处于静默期、等待执行器、阻塞的记录："
                          f"queue_id：【{first_match.get('queue_id')}】，why：{first_match.get('why')}")
                    continue
            except Exception as e:
                print(f"判断任务是否有静默期Error：{str(e)}")
                continue

            for build in job_info_builds_list:
                num = build.get("number")
                result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=view_name)

                if not result.get("status"):
                    continue
                build_info = result.get("data")
                # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
                result_dic = filter_build_info_data(build_info)
                try:
                    queue_num = result_dic.get("queue_num")
                except Exception as e:
                    queue_num = None
                    print(f"同步{jenkins_job.job_name}构建历史获取queue_num失败：", str(e))
                    continue

                # 跳过中间状态的流水线构建记录(在平台或者工单调用执行的流水线)
                if result_dic.get("result") not in ["SUCCESS", "ABORTED", "FAILURE"]:
                    # 如果任务正在执行且本地已经有这条记录，说明是页面或者工单调用执行的
                    building_jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, number=num)
                    if building_jenkins_build_job:
                        build_query_list.append(building_jenkins_build_job)
                    # 如果任务正在执行且本地有is_celery=True的记录，说明这个任务刚被执行还未获取到number或celery任务出现异常
                    is_celery_true_build_job = ApplicationJenkinsJobBuildModel.fetch_all(job=jenkins_job, is_celery=True)
                    if is_celery_true_build_job:
                        build_query_list.extend([is_celery_build for is_celery_build in is_celery_true_build_job])
                    continue

                result_dic["queue_num"] = queue_num
                result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
                result_dic["duration"] = str(result_dic.get("duration", "1"))

                result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
                    "datetime") else ""
                # 添加筛选后的数据
                build_list.append(result_dic)
                result_dic["job"] = jenkins_job
                # 如果用户是在平台点击的执行任务，这个任务执行完成，但是is_celery还是True，说明celery任务可能有问题，需要更新相关信息
                jenkins_build_job_is_celery = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, queue_num=queue_num,
                                                                                        is_celery=True)
                if jenkins_build_job_is_celery:
                    if not (jenkins_build_job_is_celery.username or jenkins_build_job_is_celery.req_source or jenkins_build_job_is_celery.app_from):
                        result_dic["username"] = "系统执行"
                        result_dic["ch_name"] = "系统执行"
                        result_dic["req_source"] = "外部执行"
                        result_dic["app_from"] = "jenkins"
                    # 将is_celery设置为False
                    result_dic["is_celery"] = False
                    jenkins_build_job_is_celery.update(**result_dic)
                    build_query_list.append(jenkins_build_job_is_celery)
                jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, number=num)
                if jenkins_build_job:
                    if not (jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
                        result_dic["username"] = "系统执行"
                        result_dic["ch_name"] = "系统执行"
                        result_dic["req_source"] = "外部执行"
                        result_dic["app_from"] = "jenkins"
                    jenkins_build_job.update(**result_dic)
                else:
                    result_dic["username"] = "系统执行"
                    result_dic["ch_name"] = "系统执行"
                    result_dic["req_source"] = "外部执行"
                    result_dic["app_from"] = "jenkins"
                    jenkins_build_job = ApplicationJenkinsJobBuildModel.create(**result_dic)
                build_query_list.append(jenkins_build_job)

            # 删除Jenkins没有的构建历史
            for query in ApplicationJenkinsJobBuildModel.fetch_all(job=jenkins_job):
                if query not in build_query_list:
                    query.delete()
            # ApplicationJenkinsJobBuildModel.objects(job=jenkins_job, code__nin=build_query_list).delete()

        end1 = time.time()
        print(f"同步{application_jenkins_query.application.get_model_code_visible_name()}应用耗时：{end1 - start1}")

        job_queryset = ApplicationJenkinsJobsModel.fetch_all(view=application_jenkins_query)
        for i in job_queryset:
            if i not in jenkins_job_query_list:
                i.delete()

    # 删除没有view的流水线记录
    ApplicationJenkinsJobsModel.objects(Q(view=None) | Q(view=0)).delete()
    # 删除没有job的构建记录
    ApplicationJenkinsJobBuildModel.objects(Q(job=None)).delete()
    # ApplicationJenkinsJobsModel.objects.filter(view=None).delete()
    end = time.time()
    print("同步jenkins数据耗时：", end - start)
    return "success"


def jenkins_sync_build(request):
    post_data = json.loads(request.body)
    job_code = post_data.get("code", None)
    if not job_code:
        return "未传递参数"
    job_query = ApplicationJenkinsJobsModel.fetch_one(code=job_code)
    view_name = job_query.view.jenkins_view_name
    job_name = job_query.job_name

    # 校验工具
    tool_query = ToolsModel.fetch_one(tool_type="jenkins")
    if not tool_query:
        return "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
    if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        return "jenkins服务器权限错误，请确认配置!"

    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query.link_tool_dict())
    # 获取单条任务详情
    result = jenkins_api.get_job_info(job_name, folder_name=view_name)

    if not result.get("status"):
        return result.get("message")
    job_info = result.get("data")
    job_info_builds_list = job_info.get("builds", [])

    # 获取当条任务构建历史
    build_list = list()
    build_query_list = []

    # 在平台点击执行，但是还没有获取到构建历史的number
    is_celery_build_queryset = ApplicationJenkinsJobBuildModel.fetch_all(job=job_query, is_celery=True)
    if is_celery_build_queryset:
        build_query_list.extend(is_celery_build_queryset)

    for build in job_info_builds_list:
        num = build.get("number")
        result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=view_name)
        if not result.get("status"):
            continue
        build_info = result.get("data")
        result_dic = filter_build_info_data(build_info)

        # # 跳过中间状态的流水线
        # if result_dic.get("result") not in ["SUCCESS", "ABORTED", "FAILURE"]:
        #     building_jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=num)
        #     if building_jenkins_build_job:
        #         build_query_list.append(building_jenkins_build_job)
        #     continue

        result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
        result_dic["duration"] = str(result_dic.get("duration", "1"))

        result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
            "datetime") else ""
        # 添加筛选后的数据
        build_list.append(result_dic)
        result_dic["job"] = job_query
        jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=num)
        if jenkins_build_job:
            if not (jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
                result_dic["username"] = "系统执行"
                result_dic["ch_name"] = "系统执行"
                result_dic["req_source"] = "外部执行"
                result_dic["app_from"] = "jenkins"
            jenkins_build_job.update(**result_dic)
        else:
            result_dic["username"] = "系统执行"
            result_dic["ch_name"] = "系统执行"
            result_dic["req_source"] = "外部执行"
            result_dic["app_from"] = "jenkins"
            jenkins_build_job = ApplicationJenkinsJobBuildModel.create(**result_dic)
        build_query_list.append(jenkins_build_job)

    # 删除Jenkins没有的构建历史
    for query in ApplicationJenkinsJobBuildModel.fetch_all(job=job_query):
        if query not in build_query_list:
            query.delete()


# 查看某个应用下是否有正在执行的流水线
def is_building_job_application(jenkins_api, view_name):
    is_building = False
    get_queue_info = jenkins_api.get_folder_info(view_name)
    if get_queue_info.get("status"):
        job_list = get_queue_info.get("data", {}).get("jobs")
        if job_list and isinstance(job_list, list):
            for job in job_list:
                # red_anime  blue_anime
                if "anime" in job.get("color"):
                    is_building = True
                    break
    else:
        is_building = False
    return is_building


# 判斷是否有正在執行的流水綫
def judge_building_job(jenkins_api):
    is_building = False
    view_name_list = []  # 存放所有的应用name
    application_queryset = ApplicationModel.fetch_all()

    for application_query in application_queryset:
        view_query = ApplicationJenkinsModel.fetch_one(application=application_query)
        if not view_query:
            dt = {"jenkins_view_name": application_query.get_model_code_name(),
                  "application": application_query}
            view_query = ApplicationJenkinsModel.create(**dt)
        view_name_list.append(view_query.jenkins_view_name)

    found_building_pipeline = False  # 控制外层循环

    for view_name in view_name_list:
        # 当发现有正在构建的任务，就退出循环
        if found_building_pipeline:
            break
        get_queue_info = jenkins_api.get_folder_info(view_name)
        if get_queue_info.get("status"):
            job_list = get_queue_info.get("data", {}).get("jobs")
            if job_list and isinstance(job_list, list):
                for job in job_list:
                    if "anime" in job.get("color"):
                        is_building = True
                        found_building_pipeline = True
                        break
        else:
            is_building = False
    return is_building


def jenkins_sync_folder_jobs_v1(folder_name):
    """更新当前应用下数据"""
    tool_query = ToolsModel.fetch_one(tool_type="jenkins")
    if not tool_query:
        return False, "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
    if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        return False, "jenkins服务器权限错误，请确认配置!"

    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

    application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=folder_name)
    if not application_jenkins_query:
        return False, "文件夹不存在"
    result_all_jobs = jenkins_api.get_folder_info(name=folder_name)
    if not result_all_jobs.get("status"):
        return False, str(result_all_jobs)
    all_job = result_all_jobs.get("data", {}).get("jobs")

    # 没有流水线报错
    if not all_job:
        return False, "流水线不存在"

    for job in all_job:
        job_query = ApplicationJenkinsJobsModel.fetch_one(view=application_jenkins_query, job_name=job.get("name"))
        if job_query:
            job_query.update(color=job.get("color"))
    return True, ""


def jenkins_sync_job_v1(jenkins_api, folder_name, job_name, view_query=None):
    start = time.time()
    """更新单条流水线数据"""
    tool_query = ToolsModel.fetch_one(tool_type="jenkins")
    if not tool_query:
        return False, "未检测到Jenkins工具配置，请到系统设置，添加工具集成。"
    if tool_query.link_status != constant.TOOL_LINK_STATUS_SUCCESS:
        return False, "jenkins服务器权限错误，请确认配置!"

    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query.link_tool_dict())

    application_jenkins_query = ApplicationJenkinsModel.fetch_one(jenkins_view_name=folder_name)
    if not application_jenkins_query:
        return False, "文件夹不存在"

    result_job = jenkins_api.get_job_info(name=job_name, folder_name=folder_name)
    result_config = jenkins_api.get_job_config(name=job_name, folder_name=folder_name)
    job_config = result_config.get("data", "")

    if not result_job.get("status"):
        return False, str(result_job)
    job_info = result_job.get("data")

    job_dic = {"job_name": job_info.get("name"), "color": job_info.get("color"),  "config": job_config}
    job_info_builds_list = job_info.get("builds", [])
    job_dic["description"] = job_info.get("description", "")

    # # 获取构建历史
    if job_info_builds_list:
        number = job_info_builds_list[0].get("number")
        result = jenkins_api.get_build_info(name=job_name, number=number, folder_name=folder_name)
        if not result:
            return result.get("message")
        job_build_info = result.get("data", {})
        job_dic["timestamp"] = str(job_build_info.get("timestamp", "0"))
        job_dic["result"] = job_build_info.get("result", "")

        if job_build_info:
            result_build_info = filter_build_info_data(job_build_info)
            job_dic["last_run_number"] = number
            job_dic["last_run_result"] = result_build_info.get("result", "")
            job_dic["last_run_timestamp"] = str(result_build_info.get("timestamp", ""))
            job_dic["last_run_datetime"] = result_build_info.get("datetime", "")
            job_dic["last_run_duration"] = str(result_build_info.get("duration", "1"))
            job_dic["last_run_duration_str"] = result_build_info.get("duration_str", "")
            job_dic["last_run_revision"] = result_build_info.get("revision", "")

    jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name)
    if jenkins_job and ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, is_celery=True):
        return False
    if jenkins_job:
        if not (jenkins_job.last_run_username or jenkins_job.last_run_req_source or jenkins_job.last_run_app_from) \
                and jenkins_job.color != "notbuilt":
            job_dic["last_run_username"] = "系统执行"
            job_dic["last_run_ch_name"] = "系统执行"
            job_dic["last_run_req_source"] = "外部执行"
            job_dic["last_run_app_from"] = "jenkins"
        jenkins_job.update(**job_dic)
    else:
        if job_dic.get("color") != "notbuilt":
            job_dic["last_run_username"] = "系统执行"
            job_dic["last_run_ch_name"] = "系统执行"
            job_dic["last_run_req_source"] = "外部执行"
            job_dic["last_run_app_from"] = "jenkins"
        job_dic["view"] = application_jenkins_query
        jenkins_job = ApplicationJenkinsJobsModel.create(**job_dic)

    # 获取当条任务构建历史
    for build in job_info_builds_list:
        num = build.get("number")
        # build_info_number = ApplicationJenkinsJobBuildModel.fetch_one(number=num, job=jenkins_job)
        # if build_info_number:
        #     if build_info_number.result:
        #         continue
        result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=folder_name)

        if not result.get("status"):
            return result.get("message")
        build_info = result.get("data")
        # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
        result_dic = filter_build_info_data(build_info)
        result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
        result_dic["duration"] = str(result_dic.get("duration", "1"))

        result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
            "datetime") else ""
        result_dic["job"] = jenkins_job
        jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, number=num)

        # 如果构建历史在平台和Jenkins上都存在，将没有执行人、执行方式、执行来源的构建历史设置和Jenkins相关
        if jenkins_build_job:
            if not (jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
                result_dic["username"] = "系统执行"
                result_dic["ch_name"] = "系统执行"
                result_dic["req_source"] = "外部执行"
                result_dic["app_from"] = "jenkins"
            jenkins_build_job.update(**result_dic)
        # 本地没有的就创建，指定执行人、执行方式、执行来源设置和Jenkins相关
        else:
            result_dic["username"] = "系统执行"
            result_dic["ch_name"] = "系统执行"
            result_dic["req_source"] = "外部执行"
            result_dic["app_from"] = "jenkins"
            ApplicationJenkinsJobBuildModel.create(**result_dic)

    end = time.time()
    print("更新单条流水线数据耗时：", end - start)


# 获取构建历史-大屏使用
def analysis_application_builds(days):
    dic = dict()
    dic["application_count"] = ApplicationModel.counter()

    today = datetime.date.today()
    recent_seven_days = [today - datetime.timedelta(days=i) for i in range(days)]

    build_count_list = list()
    for day in recent_seven_days:
        day_str = str(day)
        count = ApplicationJenkinsJobBuildModel.counter(datetime_str=day_str)
        application_build_count = list()

        application_list = ApplicationModel.fetch_all()
        for application in application_list:
            view = ApplicationJenkinsModel.fetch_one(application=application)
            job_queryset = ApplicationJenkinsJobsModel.fetch_all(view=view)
            application_count = ApplicationJenkinsJobBuildModel.counter(job__in=job_queryset, datetime_str=day_str)
            application_build_count.append(
                {"application_name": application.get_application_name(), "application_count": application_count})

        build_count_list.append({"day": day_str, "count": count, "detail": application_build_count})

    dic["build_count_list"] = build_count_list
    for build in build_count_list:
        data = DataForScreenModel.fetch_one(day=build.get("day"))
        if data:
            data.update(application_count=dic.get("application_count"), service_count=dic.get("service_count"),
                        **build)
        else:
            DataForScreenModel.create(application_count=dic.get("application_count"),
                                      service_count=dic.get("service_count"), **build)

    return dic
