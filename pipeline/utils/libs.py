import datetime

import xmltodict


# 毫秒时间转n时n分n秒
def change_time(timestamp=0):
    try:
        try:
            timestamp = int(timestamp) // 1000
        except Exception as e:
            print(e)
            return 0
        # date_time = time.localtime(timestamp)
        if timestamp < 1:
            return "1秒"
        one_day_eight_hour = datetime.timedelta(hours=8)
        date_time = datetime.datetime.fromtimestamp(timestamp) - one_day_eight_hour
        datetime_str = ""
        day = date_time.day - 1
        if day:
            datetime_str += "{}天".format(day)
        if date_time.hour:
            datetime_str += "{}小时".format(date_time.hour)
        if date_time.minute:
            datetime_str += "{}分".format(date_time.minute)
        if date_time.second:
            datetime_str += "{}秒".format(date_time.second)
    except Exception as e:
        print(e)
        return 0
    return datetime_str


# xml =-dict 互相转换
def xml_dict(xml_config=None, dict_config=None):
    if xml_config:
        # print("xml_dict__xml_config", xml_config)
        config_dict = xmltodict.parse(xml_config)
        # print("dict_json_xml", config_dict)
        return config_dict
    elif dict_config:
        # print("xml_dict__dict_config", dict_config)
        config_xml = xmltodict.unparse(dict_config)
        # print("xml_dict__dict_config", config_xml)
        return config_xml
    else:
        return False


# 流水线脚本命令数据整理
def pipeline_tool_list(pipeline_tool_list):
    """整理数据"""
    type_list = list(set([type.get("tool_type") for type in pipeline_tool_list]))
    result_data = [{"tool_type": type, "data": []} for type in type_list]
    for result in result_data:
        for tool in pipeline_tool_list:
            if tool.get("tool_type") == result.get("tool_type"):
                result["data"].append(tool)
    return result_data


def pipeline_tool_data(pipeline_tool_list):
    type_list = list(set([type.get("tool_type") for type in pipeline_tool_list]))
    result = dict()
    for tool in pipeline_tool_list:
        if result.get(tool.get("tool_type")):
            result[tool.get("tool_type")].append(tool)
        else:
            result[tool.get("tool_type")] = [tool]
    return result


def parse_url_format(data):
    """解析成url格式字符"""
    import urllib.parse
    return urllib.parse.quote(data)


def check_variable_name(variable_name):
    # import re
    # 字母, 数字， 下划线， 字母开头
    # NUM_LETTER = re.compile("^[a-zA-Z][A-Za-z0-9_]*$")
    # res = NUM_LETTER.match(variable_name)
    return variable_name


def extract_arguments_with_id(data):
    id_arguments_list = []
    for item in data:
        if 'parallel' in item:
            for parallel in item['parallel']:
                if 'branches' in parallel:
                    for branch in parallel['branches']:
                        if 'steps' in branch:
                            for step in branch['steps']:
                                if 'arguments' in step:
                                    for arg in step['arguments']:
                                        if arg['key'] == 'id':
                                            id_arguments_list.append(step['arguments'])
                                            break
        elif 'branches' in item:
            for branch in item['branches']:
                if 'steps' in branch:
                    for step in branch['steps']:
                        if 'arguments' in step:
                            for arg in step['arguments']:
                                if arg['key'] == 'id':
                                    id_arguments_list.append(step['arguments'])
                                    break

    # 初始化一个空字典，用来存储处理后的数据
    result = {}

    if id_arguments_list:
        # 遍历大列表中的每个小列表
        for sublist in id_arguments_list:
            # 初始化 id 和 submitter
            id_value = None
            submitter_value = None

            # 遍历小列表中的每个字典
            for entry in sublist:
                if entry['key'] == 'id':
                    id_value = entry['value']['value']  # 提取 id 的值
                if entry['key'] == 'submitter':
                    submitter_value = entry['value']['value']  # 提取 submitter 的值

            # 将 id_value 作为键，submitter_value 作为值存入字典
            if id_value and submitter_value:
                result[id_value] = submitter_value
    return result


def extract_input_arguments(data):
    """
        [
        [{
            'key': 'message',
            'value': {
                'isLiteral': True,
                'value': '是否继续执行构建'
            }
        }, {
            'key': 'submitter',
            'value': {
                'isLiteral': True,
                'value': 'xiongqianyuan'
            }
        }, {
            'key': 'id',
            'value': {
                'isLiteral': True,
                'value': '2ca6d343-1dce-49ff-ae8f-70a6f18af5ab'
            }
        }],
        [{
            'key': 'message',
            'value': {
                'isLiteral': True,
                'value': '是否继续执行构建'
            }
        }, {
            'key': 'submitter',
            'value': {
                'isLiteral': True,
                'value': 'xiongqianyuan'
            }
        }, {
            'key': 'id',
            'value': {
                'isLiteral': True,
                'value': '5676c3a0-2715-4292-81ce-df90de541be4'
            }
        }]
    ]
    :param data:
    :return:
    """
    input_arguments = []
    def recurse(item):
        if isinstance(item, list):
            for sub_item in item:
                recurse(sub_item)
        elif isinstance(item, dict):
            if 'name' in item and item['name'] == 'input' and 'arguments' in item:
                input_arguments.append(item['arguments'])
            for key, value in item.items():
                recurse(value)
    recurse(data)

    return input_arguments


def extract_input_arguments_2(id_arguments_list):
    """
        {
	        '2ca6d343-1dce-49ff-ae8f-70a6f18af5ab': 'xiongqianyuan',
	        '5676c3a0-2715-4292-81ce-df90de541be4': 'xiongqianyuan'
        }
    :param id_arguments_list:
    :return:
    """
    result = {}
    # 遍历大列表中的每个小列表
    for sublist in id_arguments_list:
        # 初始化 id 和 submitter
        id_value = None
        submitter_value = None

        # 遍历小列表中的每个字典
        for entry in sublist:
            if entry['key'] == 'id':
                id_value = entry['value']['value']  # 提取 id 的值
            if entry['key'] == 'submitter':
                submitter_value = entry['value']['value']  # 提取 submitter 的值

        # 将 id_value 作为键，submitter_value 作为值存入字典
        if id_value and submitter_value:
            result[id_value] = submitter_value
    return result


if __name__ == '__main__':
    pass
