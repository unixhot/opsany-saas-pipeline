import datetime

from pipeline.models import OperationLogModel


# 流水线操作审计
def operation_audit_create_build_operation_log(user_query, job_query, operation_type, operation_detail, describe,
                                               before_change_dict={}, after_change_dict={}, builds_number=None,
                                               execution_log=None):
    operation_log_dict = {
        "user_username": user_query.username,
        "user_ch_name": user_query.ch_name,
        "operation_object_name": job_query.job_name,
        "operation_object_code": job_query.code,
        "operation_type": operation_type,
        "operation_detail": operation_detail,
        "describe": describe,
        "version": datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "before_change_dict": before_change_dict,
        "after_change_dict": after_change_dict,
        "builds_number": builds_number,
        "execution_log": execution_log
    }
    operation_log_query = OperationLogModel.create(**operation_log_dict)
    return operation_log_query
