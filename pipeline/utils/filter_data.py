import time

from pipeline.utils import libs


def filter_build_info_data(build_info):
    # 运行状态， 运行编号， 修改版本，触发信息， 持续时长，开始时间
    result_dic = {
        "number": build_info.get("number"),  # 运行编号
        "timestamp": build_info.get("timestamp"),  # 开始时间
        "datetime": time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.localtime(
                                      build_info.get("timestamp") // 1000)) if build_info.get(
            "timestamp") else None,
        # 开始时间
        "result": build_info.get("result"),  # 运行状态
        "duration": build_info.get("duration"),  # 持续时长
        "building": build_info.get("building"),  # 是否正在构建
        "queue_num": build_info.get("queueId")
    }

    if build_info.get("duration"):
        result_dic["duration_str"] = libs.change_time(build_info.get("duration"))
    else:
        result_dic["duration_str"] = "0"

    for actions_dic in build_info.get("actions", {}):
        if actions_dic.get("_class") == "hudson.plugins.git.util.BuildData" and actions_dic.get("lastBuiltRevision"):
            result_dic["revision"] = actions_dic.get("lastBuiltRevision", {}).get("SHA1")
    return result_dic
