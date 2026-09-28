import os
import time

from celery.task import task

from component.esb_api import EsbApi
from config import BK_URL
from pipeline.utils.filter_data import filter_build_info_data
from pipeline.models import ApplicationJenkinsJobBuildModel, ApplicationJenkinsJobsModel, JobBuildNumberScriptModel, \
    JobBuildInputMessageModel, UserInfo
from pipeline.utils.jenkins_api import JenkinsApi


@task(time_limit=10800)
def celery_build_num_and_run_username(job_query, view_name, jenkins_api, user_query, log_query=None,
                                      parallel_names=None, input_id_submitter_dic=None, app_code=None):
    print(f"开始异步执行构建流水线【{job_query.job_name}】", job_query, log_query, parallel_names, input_id_submitter_dic, app_code)
    log_query1 = get_build_num_and_run_username(job_query, jenkins_api, log_query)
    status, message = get_run_build_info(job_query, log_query1, view_name, jenkins_api, parallel_names,
                                         input_id_submitter_dic, app_code)
    print("celery_build_num_and_run_username get_run_build_info:", status, message)
    return status, message


# 将get_run_build_info放进celery_build_num_and_run_username 异步任务
@task(time_limit=300)
def celery_get_run_build_info(log_query, view_name, jenkins_api):
    # get_run_build_info(log_query, view_name, jenkins_api)
    pass


def get_build_num_and_run_username(job_query, jenkins_api, log_query=None):
    while True:
        time.sleep(1)
        log_num_res = jenkins_api.get_queue_item(log_query.queue_num)
        status = log_num_res.get("status")
        if status:
            log_num = log_num_res.get("data", {}).get("executable", {}).get("number")
            print(f"正在获取任务【{job_query.job_name}】构建编号：【{log_num}】", log_query)
            if log_num:
                if log_query:
                    job_query.update(last_run_number=log_num)
                    log_query.update(number=log_num, is_celery=False)
                print(f"已经获取到任务【{job_query.job_name}】的构建编号：【{log_num}】-----{log_query.req_source}, {log_query.username}")
                break
        else:
            print(f"获取任务【{job_query.job_name}】构建编号失败：{log_num_res}")
            break
    return log_query


def get_run_build_info(job_query, log_query, view_name, jenkins_api, parallel_names=None, input_id_submitter_dic=None, app_code=None):
    try:
        if not log_query:
            return False, "log_query not found"
        num = log_query.number
        if not num:
            return False, "log_query not number"
        """
            当流程有并行阶段时，存储当前脚本的并行阶段名称
            {'Hello OpsAny': ['Hello OpsAny', '第一阶段'], '第二阶段': ['第二阶段step', '第二阶段step2']}
            当这次构建有待人工确认操作时，就创建一条记录
        """
        if parallel_names or input_id_submitter_dic:
            job_build_number_script_query = JobBuildNumberScriptModel.create(
                job=job_query, number=num, parallel_script=parallel_names, input_id_submitter_dic=input_id_submitter_dic)
        job_name = log_query.job.job_name
        while True:
            result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=view_name)
            if not result.get("status"):
                return False, "get_build_info api error, {}".format(result.get("data"))
            build_info = result.get("data")
            # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
            result_dic = filter_build_info_data(build_info)
            result_dic["result"] = result_dic.get("result", "")
            result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
            result_dic["duration"] = str(result_dic.get("duration", "1"))

            result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
                "datetime") else ""
            result_get_build_console_output = jenkins_api.get_build_console_output(name=job_name, number=num,
                                                                                   folder_name=view_name)
            if result_get_build_console_output.get("status"):
                result_dic["output"] = result_get_build_console_output.get("data")
            # 更新流水线job
            color = None
            job_info = jenkins_api.get_job_info(job_name, view_name)
            if job_info.get("status"):
                color = job_info.get("data", {}).get("color")
            job_query_dic = {
                "last_run_result": result_dic.get("result", ""),
                "last_run_timestamp": str(result_dic.get("timestamp", "")),
                "last_run_datetime": result_dic.get("datetime", ""),
                "last_run_duration": str(result_dic.get("duration", "1")),
                "last_run_duration_str": result_dic.get("duration_str", ""),
                "last_run_revision": result_dic.get("revision", ""),
                "color": color,
                "result": result_dic.get("result", "")
            }

            job_query.update(**job_query_dic)
            log_query.update(**result_dic)

            try:
                # 发送站内信通知
                query = JobBuildNumberScriptModel.fetch_one(job=job_query, number=num)
                if query and query.input_id_submitter_dic:
                    query_input_id_submitter_dic = dict(query.input_id_submitter_dic)
                    query_input_id_submitter_dic = {k.upper(): v for k, v in query_input_id_submitter_dic.items()}
                    build_stage_log = get_build_stage_info_(jenkins_api, job_query, num, view_name,
                                                            query_input_id_submitter_dic, app_code)
                else:
                    pass
                    # print("当前构建没有配置等待人工确认步骤")
            except Exception as e:
                print("发送站内信通知Error：", str(e))

            if result_dic.get("building") is False:
                job_query.update(**job_query_dic)
                log_query.update(**result_dic)
                break
            time.sleep(2)
        return True, "Success"
    except Exception as e:
        print("get_run_build_info_error", str(e))
        return False, str(e)


# 同步Jenkins任务
@task(time_limit=1800)
def jenkins_sync_data():
    from pipeline.utils.sync_data import jenkins_sync_data_two
    try:
        print("定时任务开始执行同步Jenkins任务")
        res = jenkins_sync_data_two()
    except Exception as e:
        print(f"定时任务执行同步Jenkins任务Error：{str(e)}")
    return True, "Success"


# 获取指定构建历史的构建日志
def get_build_stage_info_(jenkins_api, job_query, number, folder_name, input_id_submitter_dic, app_code):
    print(f"任务【{job_query.job_name}】开始指定发送消息通知", type(input_id_submitter_dic), input_id_submitter_dic)
    try:
        esb = EsbApi()
        # 阶段日志
        res = jenkins_api.get_build_stage_info(job_query.job_name, number, folder_name)
        res_data_stage = res.get("data", {}).get("stages")
        end_data = []
        # 存放阶段性构建历史(全量)
        end_data_stage_flow_nodes = []
        for i in res_data_stage:
            stageFlowNodes = i.get("stageFlowNodes")
            if stageFlowNodes:
                end_data.append(i)
        for i in end_data:
            end_data_stage_flow_nodes.extend(i.get("stageFlowNodes"))

        for i in end_data_stage_flow_nodes:
            links_log_href = i.get("_links", {}).get("log", {}).get("href")
            # 某个阶段的构建状态
            status = i.get("status")
            input_id = None
            if status == "PAUSED_PENDING_INPUT":
                input_id_res = jenkins_api.get_build_stage_log_input_id_info(links_log_href)
                if input_id_res.get("status"):
                    input_id = input_id_res.get("data")
                    input_id = input_id.upper()
                # 人工确认配置的确认者
                username_list = input_id_submitter_dic.get(input_id).split(",")
                job_build_input_message_query = JobBuildInputMessageModel.fetch_one(job=job_query, number=number,
                                                                                    links_log_href=links_log_href)

                # 如果日志中有正在等待人工确认的步骤，并且已经发送过站内信，就跳过
                if status == "PAUSED_PENDING_INPUT" and job_build_input_message_query:
                    continue
                if status == "PAUSED_PENDING_INPUT" and not job_build_input_message_query:
                    username_dict = {}
                    for username in username_list:
                        ENV_ = {"development": "", "production": "o", "testing": "t"}
                        ENV_URL = ENV_.get(os.getenv("BK_ENV"))
                        base_url = BK_URL + "/" + ENV_URL + "/pipeline/#/applicationDelivery/assemblyLine/executionLogDefault"
                        pc_url = base_url + "?appCode={}&view_name={}&number={}&job_name={}&job_code={}".format(
                            app_code, folder_name, number, job_query.job_name, job_query.code)
                        url = '<a href="{}" target="_blank">去处理</a>'.format(pc_url)
                        user_query = UserInfo.fetch_one(username=username)
                        parameter = "('{}','{}')".format(job_query.job_name, url)
                        alert_info = {"job_name": job_query.job_name, "url": url, "message_status": 5}
                        if user_query:
                            send_dict = esb.send_out_message(21, ["1"], parameter, user_query.username, alert_info)
                            username_dict[user_query.username] = send_dict.get("data") if send_dict else send_dict

                    JobBuildInputMessageModel.create(job=job_query, number=number, links_log_href=links_log_href,
                                                     username_dict=username_dict)
        return True
    except Exception as e:
        return False


@task(time_limit=300)
def sync_application_pipelines(jenkins_api, view_query, view_name, job_name, sync_building_job_query):
    print("开始执行sync_application_pipelines111111111", sync_building_job_query.status)
    start = time.time()
    sync_building_job_query.update(status="2")

    try:
        while True:
            result_job = jenkins_api.get_job_info(name=job_name, folder_name=view_name)
            if result_job.get("status"):
                job_info_data = result_job.get("data")
                job_name = job_info_data.get("name")
                job_color = job_info_data.get("color")
                result_config = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
                job_config = result_config.get("data", "")

                job_dic = {
                    "job_name": job_name,
                    "config": job_config,
                    "color": job_color,
                    "view": view_query,
                    "description": job_info_data.get("description", "")
                }

                # 构建历史
                job_info_builds_list = job_info_data.get("builds", [])

                number = None
                if job_info_builds_list:
                    number = job_info_builds_list[0].get("number")
                    result = jenkins_api.get_build_info(name=job_name, number=number, folder_name=view_name)
                    if not result.get("status"):
                        continue

                    job_build_info = result.get("data")
                    job_dic["timestamp"] = str(job_build_info.get("timestamp", "0"))

                    # 更新当前job的上次构建相关信息
                    if job_build_info:
                        result_build_info = filter_build_info_data(job_build_info)
                        job_dic["last_run_number"] = number
                        job_dic["result"] = result_build_info.get("result", "")
                        job_dic["last_run_result"] = result_build_info.get("result", "")
                        job_dic["last_run_timestamp"] = str(result_build_info.get("timestamp", ""))
                        job_dic["last_run_datetime"] = result_build_info.get("datetime", "")
                        job_dic["last_run_duration"] = str(result_build_info.get("duration", "1"))
                        job_dic["last_run_duration_str"] = result_build_info.get("duration_str", "")
                        job_dic["last_run_revision"] = result_build_info.get("revision", "")

                jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view_query)
                if jenkins_job:
                    if not(jenkins_job.last_run_username or jenkins_job.last_run_req_source or jenkins_job.last_run_app_from)\
                            and jenkins_job.color != "notbuilt":
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
                    ApplicationJenkinsJobsModel.create(**job_dic)

                # 获取当条任务构建历史
                build_list = list()
                build_query_list = []
                for build in job_info_builds_list:
                    num = build.get("number")
                    build_info_number = ApplicationJenkinsJobBuildModel.fetch_one(number=num, job=jenkins_job)
                    # if build_info_number:
                    #     if (build_info_number.result) and (not build_info_number.building):
                    #         continue
                    result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=view_name)

                    if not result.get("status"):
                        continue
                    build_info = result.get("data")
                    # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
                    result_dic = filter_build_info_data(build_info)
                    result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
                    result_dic["duration"] = str(result_dic.get("duration", "1"))

                    result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
                        "datetime") else ""
                    # 添加筛选后的数据
                    build_list.append(result_dic)
                    result_dic["job"] = jenkins_job
                    jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, number=num)
                    if jenkins_build_job:
                        if not (
                                jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
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

                if "anime" not in job_color:
                    sync_building_job_query.delete()
                    break
            else:
                sync_building_job_query.delete()
                return result_job.get("message")
    except Exception as e:
        sync_building_job_query.delete()
        print("同步流水线Error：", str(e))

    end = time.time()
    print(f"同步流水线{job_name}耗时：", end - start)
    return "success"


@task(time_limit=300)
def refresh_pipeline_jobs(jenkins_api, view_query, view_name, job_name, all_job, refresh_job_query):
    refresh_job_query.update(status="2")
    try:
        job = jenkins_api.get_job_info(job_name, view_name)
        if job.get("status"):
            job_info_data = job.get("data", {})
            job_name = job_info_data.get("name")
            job_color = job_info_data.get("color")
            result_config = jenkins_api.get_job_config(name=job_name, folder_name=view_name)
            job_config = result_config.get("data", "")

            job_dic = {"job_name": job_name, "config": job_config, "color": job_color,
                       "view": view_query}

            job_info_builds_list = job_info_data.get("builds", [])
            job_dic["description"] = job_info_data.get("description", "")

            number = None
            # 获取构建历史
            if job_info_builds_list:
                number = job_info_builds_list[0].get("number")
                result = jenkins_api.get_build_info(name=job_name, number=number, folder_name=view_name)
                if not result:
                    return result.get("message")

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

            jenkins_job = ApplicationJenkinsJobsModel.fetch_one(job_name=job_name, view=view_query)
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

            # 获取当条任务构建历史
            build_list = list()
            build_query_list = []
            for build in job_info_builds_list:
                num = build.get("number")
                build_info_number = ApplicationJenkinsJobBuildModel.fetch_one(number=num, job=jenkins_job)
                # if build_info_number:
                #     if (build_info_number.result) and (not build_info_number.building):
                #         continue
                result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=view_name)

                if not result.get("status"):
                    # return result.get("message")
                    continue
                build_info = result.get("data")
                # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
                result_dic = filter_build_info_data(build_info)
                result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
                result_dic["duration"] = str(result_dic.get("duration", "1"))

                result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
                    "datetime") else ""
                # 添加筛选后的数据
                build_list.append(result_dic)
                result_dic["job"] = jenkins_job
                jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=jenkins_job, number=num)
                if jenkins_build_job:
                    if not (
                            jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
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
            # for query in ApplicationJenkinsJobBuildModel.fetch_all(job=jenkins_job):
            #     if query not in build_query_list:
            #         query.delete()
            refresh_job_query.update("1")
            refresh_job_query.delete()
            return jenkins_job
        else:
            refresh_job_query.update("1")
            refresh_job_query.delete()
    except Exception as e:
        refresh_job_query.update("1")
        refresh_job_query.delete()
        print("刷新流水线Error：", str(e))

    # # 删除Jenkins上不存在的job
    # jenkins_job_list = [job.get("name") for job in all_job]
    # jenkins_job_queryset = ApplicationJenkinsJobsModel.fetch_all(view=view_query)
    # for jenkins_job_query in jenkins_job_queryset:
    #     if jenkins_job_query.job_name not in jenkins_job_list:
    #         jenkins_job_query.delete()


@task(time_limit=300)
def jenkins_sync_job_v1_celery(tool_query_dict, folder_name, job_name, job_query):
    """"更新指定流水线的构建历史"""
    # 创建jenkins连接
    jenkins_api = JenkinsApi(**tool_query_dict)
    if ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, is_celery=True):
        return False

    result_job = jenkins_api.get_job_info(name=job_name, folder_name=folder_name)
    result_config = jenkins_api.get_job_config(name=job_name, folder_name=folder_name)
    job_config = result_config.get("data", "")

    if not result_job.get("status"):
        return False, str(result_job)
    job_info = result_job.get("data")

    job_dic = {"job_name": job_info.get("name"), "color": job_info.get("color"),  "config": job_config}
    job_info_builds_list = job_info.get("builds", [])
    job_dic["description"] = job_info.get("description", "")

    build_list = list()
    build_query_list = []
    for build in job_info_builds_list:
        num = build.get("number")
        build_info_number = ApplicationJenkinsJobBuildModel.fetch_one(number=num, job=job_query)
        # if build_info_number:
        #     if (build_info_number.result) and (not build_info_number.building):
        #         continue
        result = jenkins_api.get_build_info(name=job_name, number=num, folder_name=job_name)

        if not result.get("status"):
            continue
        build_info = result.get("data")
        # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
        result_dic = filter_build_info_data(build_info)
        result_dic["timestamp"] = str(result_dic.get("timestamp", ""))
        result_dic["duration"] = str(result_dic.get("duration", "1"))

        result_dic["datetime_str"] = str(result_dic.get("datetime")).split(" ")[0] if result_dic.get(
            "datetime") else ""
        # 添加筛选后的数据
        build_list.append(result_dic)
        result_dic["job"] = job_query
        jenkins_build_job = ApplicationJenkinsJobBuildModel.fetch_one(job=job_query, number=num)
        if jenkins_build_job:
            if not (
                    jenkins_build_job.username or jenkins_build_job.req_source or jenkins_build_job.app_from):
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

    # 删除Jenkins上没有的构建历史
    jenkins_build_queryset = ApplicationJenkinsJobBuildModel.fetch_all(job=job_query)
    for jenkins_build in jenkins_build_queryset:
        if jenkins_build not in build_query_list:
            jenkins_build.delete()
