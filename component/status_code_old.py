# -*- coding: utf-8 -*-
"""
Copyright © 2012-2020 OpsAny. All Rights Reserved.
"""  # noqa

from enum import Enum


class ErrorStatusCode(Enum):
    # code = 400
    INVALID_REQUEST = (400, 40000, '不合法的请求')

    # code = 401
    INVALID_TOKEN = (401, 40100, '无效的token')
    USER_NOT_EXISTED_OR_WRONG_PASSWORD = (401, 40101, '用户名/密码错误')
    NOT_HAVE_USER_INFO = (401, 40102, '没有相应用户信息')
    TOOL_AUTH_ERROR = (401, 40103, '权限错误！无法访问该工具，请确认配置后提交!')

    # code = 403
    USER_NOT_POWER = (403, 40300, "没有操作权限")
    USER_GIT_NOT_POWER = (403, 40301, "没有操作当前仓库权限")
    USER_NOT_APPLICATION_POWER = (403, 40302, "没有该应用访问权限")

    # code = 404
    DATA_NOT_EXISTED = (404, 40400, '数据不存在')
    JENKINS_NOT_EXISTED = (404, 40401, "找不到Jenkins服务，请到工具管理添加Jenkins工具")  # 状态码前端在用不可修改
    GIT_NOT_EXISTED = (404, 40403, "找不到Gitlab服务，请到工具管理添加Gitlab工具")  # 状态码前端在用不可修改
    INVALID_LAYER_ID = (404, 40404, 'layer_id不存在')
    NOT_ADD_ACCESSKEY = (404, 40405, "当前用户没有添加accessKey")
    ACCESSKEY_ERROR = (404, 40406, "access错误")
    NOT_IMPORT_ACCESS = (404, 40407, "请输入access信息")
    BUSINESS_NOT_EXISTED = (404, 40408, "业务不存在")
    APPLICATION_NOT_EXISTED = (404, 40409, "应用不存在")
    TOOL_NOT_EXISTED = (404, 40410, "工具不存在")
    JOB_NOT_FOUNT = (404, 40411, "流水线不存在")

    BUILD_NOT_EXISTED = (404, 40412, "构建信息不存在")
    TYPE_NOT_EXISTED = (404, 40413, "类型不存在")
    REPOSITORY_NOT_EXISTED = (404, 40414, "制品库不存在")
    URL_NOT_EXISTED = (404, 40415, "接口不存在")

    GROUP_NOT_EXISTED = (404, 40416, "分组不存在")
    TEMPLATE_NOT_EXISTED = (404, 40417, "模板不存在")
    JENKINS_CREDENTIALS_NOT_EXISTED = (404, 40418, "凭据不存在")
    JENKINS_PLUGIN_NOT_EXISTED = (404, 40419, "缺少相关插件")
    USER_NOT_EXISTED = (404, 40420, "用户不存在")
    REQUEST_API_NOT_FOUNT = (404, 40421, "切换失败，可能是您Jenkins版本问题导致错误的发生，请更新至2.328或以下最近版本试试吧！")

    # code = 422
    RECORD_HAS_EXISTED = (422, 42200, '记录已经存在')
    NO_PARAMS = (422, 42201, '参数不能为空')
    MODEL_HAS_NO_PK_NAME = (422, 42202, '模型中不含有主键字段')
    THIS_DATA_NOT_PASS_VERIFY = (422, 42203, '当前数据未能通过验证，请检查您的数据内容！')
    NOT_FIND_MODEL = (422, 42204, '没有找到相关模型信息')
    MUST_INPUT_MESSAGE = (422, 42205, '必须输入相关信息')
    INST_HAS_APPLICATION = (422, 42206, '当前业务有应用与其关联，禁止删除！')
    INST_HAS_SERVICE = (422, 42207, '当前应用有服务与其关联，禁止删除！')
    MESSAGE_NOT_FIND = (422, 42208, '没有找到相关信息')
    STAFF_MANAGER_HAS_EXISTED = (422, 42209, '负责人已存在')
    OPERATION_ERROR = (422, 42210, "操作失败")
    TOOL_HAS_EXISTED = (422, 42211, '该类型的工具已存在，无法创建！')
    TOOL_NAME_HAS_EXISTED = (422, 42212, '工具名已存在')

    STATUS_ERROR = (422, 42213, '状态更新失败')
    TOOL_CONNECTION_ERROR = (422, 42214, '连接出错！无法访问该工具，请确认配置后提交!')
    DATABASE_ERROR = (422, 42215, '入库失败，请检查数据！')
    JENKINS_AUTH_ERROR = (422, 42216, "Jenkins服务器连接异常，请确认该服务状态!")
    JENKINS_STATUS_ERROR = (422, 42217, "Jenkins服务器权限错误，请确认配置!")
    JOB_NAME_HAS_EXISTED = (422, 42218, '名称已被占用')
    JOB_NAME_RENAME_SAME = (422, 42219, '新名称和当前的一样')
    JENKINS_JOB_BUILD_ERROR = (422, 42220, '构建失败')
    NEXUS_STATUS_ERROR = (422, 42221, "Nexus服务器权限错误，请确认配置!")
    NEXUS_HAS_EXISTED = (422, 42222, "制品库名称已存在")

    SYNTAX_ERROR = (422, 42223, '语法错误')

    INST_HAS_JENKINS = (422, 42224, '当前应用有流水线与其关联，无法删除！')
    _NAME_HAS_EXISTED = (422, 42225, '唯一标识已存在')
    REPOSITORY_ASSET_NOT_UPLOAD = (422, 42226, "当前制品库暂不支持上传资源")
    PORT_MUST_UNIQUE = (422, 42227, "端口被占用")
    APP_REPO_ERROR = (422, 42228, "当前制品库与应用关联，无法删除！")
    APP_HAS_REPO = (422, 42229, "当前应用有制品库与其关联，无法删除！")
    MODEL_NAME_NOT_CHINESE = (422, 42230, "唯一标识只能是字母、数字、下划线且以字母开头！")
    REPO_NOT_UPDATE = (422, 42231, "该存储库不允许更新资产！")
    GROUP_HAS_EXISTED = (422, 42232, "分组已存在")
    GROUP_DELETE_HAS_EXISTED = (422, 42233, "分组下有模板，无法删除！")
    TEMPLATE_HAS_EXISTED = (422, 42234, "模板已存在")
    BUILT_IN_NOT_OPERATION = (422, 42235, "内置数据，不可操作！")
    INST_HAS_NEXUS = (422, 42236, '当前应用有制品库与其关联，无法删除！')
    JENKINS_CREDENTIALS_HAS_EXISTED = (422, 42237, '凭据ID已存在，请更换ID')
    JENKINS_CREDENTIALS_NAME_HAS_EXISTED = (422, 42238, '凭据名称已存在')
    THIS_IS_FOLDER = (422, 42239, "这是一个文件夹")
    NAME_NOT_CHINESE = (422, 42240, "参数名只能是字母、数字、下划线且以字母开头！")
    NAME_FORMAT_ERROR = (422, 42241, "参数格式错误")
    NAME_UNIQUE_ERROR = (422, 42242, "参数名不可重复")
    INST_HAS_GITLAB = (422, 42243, '当前代码仓库正在被引用,无法删除')
    MODEL_CODE_FIELD_ERROR = (422, 42244, '当前模型字段缺失')
    CUSTOM_ERROR = (422, 42245, '')

    # code 500
    SERVER_ERROR = (500, 50000, '操作失败')
    JENKINS_HTTP_ERROR = (500, 50001, 'Jenkins HTTP ERROR')
    GITLAB_INTERNAL_SERVER_ERROR = (502, 502003, "Gitlab服务异常")

    # code 502
    JENKINS_SERVER_ERROR = (502, 502001, "Jenkins服务器错误，请检查Jenkins服务是否运行正常")
    GITLAB_SERVER_ERROR = (502, 502003, "Gitlab服务器错误，请检查Gitlab服务是否运行正常")
    ST2_SERVER_ERROR = (502, 502003, "StackStorm服务器错误，请检查StackStorm服务是否运行正常")


def error(error_info=ErrorStatusCode.INVALID_REQUEST, errors=None, custom_message=None):
    http_code, error_code, error_msg = error_info.value
    params = {
        'code': http_code,
        'message': error_msg,
        'errcode': error_code,
    }
    if errors:
        params['errors'] = errors
    if custom_message:
        params['message'] = custom_message
    return params


class SuccessStatusCode(Enum):
    # code = 200
    # 测试使用
    TEST_SUCCESS = (200, 20000, '服务器连接成功')

    # 模型组部分 04 - 07
    MESSAGE_CREATE_SUCCESS = (200, 20001, '相关信息创建成功')
    MESSAGE_GET_SUCCESS = (200, 20002, '相关信息信息获取成功')
    MESSAGE_DELETE_SUCCESS = (200, 20003, '相关信息删除成功')
    MESSAGE_UPDATE_SUCCESS = (200, 20004, '相关信息更新成功')

    MENU_GET_SUCCESS = (200, 20005, '获得菜单列表成功')
    OPERATION_SUCCESS = (200, 20006, '操作成功')

    JENKINS_JOB_BUILD_SUCCESS = (200, 20007, '构建成功')

    REFRESH_STATUS_SUCCESS = (200, 20008, '状态更新成功')

    JOB_BUILD_SUCCESS = (200, 20009, '操作成功，开始执行。')
    OPERATION_STOP_SUCCESS = (200, 20010, '停止构建操作指令发送成功')
    ROLE_SUCCESS = (200, 20011, '授权成功')
    DEPLOY_TASK_RUN_SUCCESS = (200, 20012, '操作成功，开始执行。')
    DEPLOY_TASK_CANCEL_SUCCESS = (200, 20013, '操作成功，正在中止。')
    UPLOAD_SUCCESS = (200, 20012, '上传成功')


def success(success_info=SuccessStatusCode.TEST_SUCCESS, data=None, message=None):
    http_code, success_code, success_msg = success_info.value
    params = {
        'code': http_code,
        'successcode': success_code,
        'message': success_msg,
    }
    if message:
        params["message"] = message
    if data is not None: params['data'] = data
    return params
