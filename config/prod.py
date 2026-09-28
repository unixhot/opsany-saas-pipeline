# -*- coding: utf-8 -*-
from config import RUN_VER

if RUN_VER == 'open':
    from blueapps.patch.settings_open_saas import *  # noqa
else:
    from blueapps.patch.settings_paas_services import *  # noqa

# 正式环境
RUN_MODE = 'PRODUCT'

# 只对正式环境日志级别进行配置，可以在这里修改
LOG_LEVEL = 'ERROR'

UPLOAD_PATH = os.getenv("UPLOAD_PATH", "/opt/opsany/")
# V2
# import logging
# logging.getLogger('root').setLevel('INFO')
# V3
# import logging
# logging.getLogger('app').setLevel('INFO')


# 正式环境数据库可以在这里配置

DATABASES.update(
    {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DEVOPS_NAME,  # 数据库名
            'USER': DEVOPS_NAME,  # 数据库用户
            'PASSWORD': os.getenv("MYSQL_PASSWORD", "123456"),  # 数据库密码
            'HOST': os.getenv("MYSQL_HOST", "127.0.0.1"),  # 数据库主机
            'PORT': int(os.getenv("MYSQL_PORT", "3306")),  # 数据库端口
            'OPTIONS': {
                "init_command": "SET default_storage_engine=INNODB",
            }

        },
    }
)

import mongoengine

MONGO_CONN = mongoengine.connect(
    db=DEVOPS_NAME,  # 需要进行操作的数据库名称
    alias='default',  # 必须定义一个default数据库
    host=os.getenv("MONGO_HOST", "127.0.0.1"),
    port=int(os.getenv("MONGO_PORT", 27017)),
    username=DEVOPS_NAME,
    password=os.getenv("MONGO_PASSWORD", DEVOPS_NAME),
    connect=False,
    # authentication_source="admin",           # 进行身份认证的数据库，通常这个数据库为admin
)

CORS_ORIGIN_WHITELIST = [
    'http://localhost:8000',
]

CORS_ALLOW_CREDENTIALS = True

