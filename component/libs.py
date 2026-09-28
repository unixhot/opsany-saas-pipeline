from collections import OrderedDict

import yaml


class GetUserInfo:
    def get_user_info(self, request=None, bk_token=None):
        bk_esb_username = request.COOKIES.get("bk_token_username") or request.COOKIES.get("bk_esb_username")
        from pipeline.models import UserInfo
        return UserInfo.fetch_one(username=bk_esb_username)

    def get_user_role(self, request=None, bk_token=None):
        from component.esb_api import EsbApi
        if not bk_token:
            bk_token = request.COOKIES.get("bk_token")
        esb_obj = EsbApi(bk_token)
        user_info = esb_obj.get_user_info()
        return user_info.get("role")
    
    def get_user_info_from_esb_username(self, request):
        bk_esb_username = request.COOKIES.get("bk_esb_username")
        from pipeline.models import UserInfo
        return UserInfo.fetch_one(username=bk_esb_username)


def first_error_message(form):
    error_data = form.errors.as_data()
    error_data_list = list(error_data.items())
    # if not error_data_list:
    #     return ""
    error_message = error_data_list[0][1][0].message
    message = "{}".format(error_message)
    return message


# 生成有序的字典（传参为yaml字符串）
def ordered_yaml_load(yaml_str, Loader=yaml.SafeLoader,
                      object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(yaml_str, OrderedLoader)


# 生成有序的yaml字符串（传参为OrderedDict）
def ordered_yaml_dump(data, stream=None, Dumper=yaml.SafeDumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


if __name__ == '__main__':
    pass
