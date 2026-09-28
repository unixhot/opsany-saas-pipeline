import datetime

from pipeline.models import ApplicationJenkinsJobsModel, ApplicationJenkinsJobBuildModel, JobBuildNumberScriptModel, \
    JobBuildInputMessageModel


def init_jenkins_job_last_run_message():
    print(" [SUCCESS] {} init_jenkins_job_last_run_message Running".format(str(datetime.datetime.now()).rsplit(".", 1)[0]))

    try:
        application_jenkins_job_queryset = ApplicationJenkinsJobsModel.fetch_all()
        for job_query in application_jenkins_job_queryset:
            build_query = ApplicationJenkinsJobBuildModel.objects.filter(job=job_query).order_by("-created_at").first()
            if build_query and job_query.last_run_number != build_query.number:
                last_build_dict = build_query.to_dict()
                update_dict = {
                    "last_run_number": last_build_dict["number"],
                    "last_run_username": last_build_dict["username"],
                    "last_run_ch_name": last_build_dict["ch_name"],
                    "last_run_req_source": last_build_dict["req_source"],
                    "last_run_app_from": last_build_dict["app_from"],
                    "last_run_result": last_build_dict["result"],
                    "last_run_timestamp": last_build_dict["timestamp"],
                    "last_run_datetime": last_build_dict["datetime"],
                    "last_run_duration": last_build_dict["duration"],
                    "last_run_duration_str": last_build_dict["duration_str"],
                    "last_run_revision": last_build_dict["revision"]
                }
                job_query.update(**update_dict)
            else:
                pass

    except Exception as e:
        print(" [ERROR] {} init_jenkins_job_last_run_message {}".format(str(datetime.datetime.now()).rsplit(".", 1)[0], str(e)))
    print(" [SUCCESS] {} init_jenkins_job_last_run_message Execution Complete".format(str(datetime.datetime.now()).rsplit(".", 1)[0]))


def create_job_build_number_script():
    print(" [SUCCESS] {} create_job_build_number_script Running".format(str(datetime.datetime.now()).rsplit(".", 1)[0]))

    try:
        if not JobBuildNumberScriptModel.fetch_one():
            JobBuildNumberScriptModel.create(parallel_script={"第一条记录": "第一条记录"}, input_id_submitter_dic={
                "input_id256": "zhangsan,lisi"})
        if not JobBuildInputMessageModel.fetch_one():
            JobBuildInputMessageModel.create(links_log_href="/job_name/folder_name/number/execution/nodes/wfapi",
                                             username_dict={}, stage_status="1")
    except Exception as e:
        print(" [ERROR] {} create_job_build_number_script {}".format(str(datetime.datetime.now()).rsplit(".", 1)[0],
                                                                        str(e)))
        print(" [SUCCESS] {} create_job_build_number_script Execution Complete".format(
            str(datetime.datetime.now()).rsplit(".", 1)[0]))


# 初始化定时任务
def init_jenkins_sync_data_cron_task():
    from djcelery.models import IntervalSchedule
    from djcelery.schedulers import DatabaseScheduler
    from pipeline.models import AutoSyncJenkinsDataModel

    try:
        query = AutoSyncJenkinsDataModel.fetch_one(name="定时任务")
        if not query:
            query = AutoSyncJenkinsDataModel.create(
                name="定时任务",
                minute=5,
                enable=True
            )

        interval_obj, created = IntervalSchedule.objects.get_or_create(
            every=query.minute * 60,
            period="seconds",
        )
        create_or_update_task = DatabaseScheduler.create_or_update_task
        schedule_dict = {
            "crontab": None,
            "schedule": interval_obj.schedule,
            "args": [],
            "kwargs": {},
            "task": "pipeline.celery_task.jenkins_sync_data",
            "enabled": query.enable,
            "description": ""
        }
        crontab_task_name = "{}".format("celery.jenkins_sync_data")
        create_or_update_task(crontab_task_name, **schedule_dict)
    except Exception as e:
        print(f"初始化init_jenkins_sync_data_cron_task定时任务失败: {str(e)}")
    print(" [SUCCESS] {} init_jenkins_sync_data_cron_task Execution Complete".format(str(datetime.datetime.now()).rsplit(".", 1)[0]))


def run():
    init_jenkins_job_last_run_message()
    create_job_build_number_script()
