# -*- coding: utf-8 -*-
from config import RUN_VER
from urllib import parse

if RUN_VER == 'open':
    from blueapps.patch.settings_open_saas import *  # noqa
else:
    from blueapps.patch.settings_paas_services import *  # noqa

# 预发布环境
RUN_MODE = 'STAGING'

# 正式环境的日志级别可以在这里配置
# V2
# import logging
# logging.getLogger('root').setLevel('INFO')
# V3
# import logging
# logging.getLogger('app').setLevel('INFO')

UPLOAD_PATH = os.getenv("UPLOAD_PATH", "/opt/opsany/")

# 预发布环境数据库可以在这里配置

DATABASES.update(
    {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'pipeline',  # 数据库名
            'USER': "pipeline",  # 数据库用户
            'PASSWORD': os.getenv("MYSQL_PASSWORD", "123456.coM"),  # 数据库密码
            'HOST': os.getenv("MYSQL_HOST", "192.168.0.111"),  # 数据库主机
            'PORT': os.getenv("MYSQL_PORT", "3306"),  # 数据库端口
        },
    }
)

import mongoengine

MONGO_CONN = mongoengine.connect(
    db=DEVOPS_NAME,  # 需要进行操作的数据库名称
    alias='default',  # 必须定义一个default数据库
    host=os.getenv("MONGO_HOST", "192.168.0.111"),
    port=os.getenv("MONGO_PORT", 27017),
    username='devops',
    password=os.getenv("MONGO_PASSWORD", '123456.coM'),
    connect=False,
    # authentication_source="admin",           # 进行身份认证的数据库，通常这个数据库为admin
)

CORS_ORIGIN_WHITELIST = [
    'http://localhost:8000',
]

CORS_ALLOW_CREDENTIALS = True

ELASTIC_APM = {
  'SERVICE_NAME': 'saas-pipeline',
  'SECRET_TOKEN': '',
  'SERVER_URL': 'https://192.168.0.112:8200',
  'ENVIRONMENT': 'dev',
}

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.0.111")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_USERNAME = parse.quote(os.getenv("REDIS_USERNAME", "") or "")
REDIS_PASSWORD = parse.quote(os.getenv("REDIS_PASSWORD", "123456.coM"))

# Redis Celery AMQP
BROKER_URL = 'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/17'.format(REDIS_USERNAME=REDIS_USERNAME, REDIS_PASSWORD=REDIS_PASSWORD, REDIS_HOST=REDIS_HOST, REDIS_PORT=REDIS_PORT)

