# -*- coding: utf-8 -*-
import mongoengine

from config import RUN_VER
if RUN_VER == 'open':
    from blueapps.patch.settings_open_saas import *  # noqa
else:
    from blueapps.patch.settings_paas_services import *  # noqa

# 本地开发环境
RUN_MODE = 'DEVELOP'

# APP本地静态资源目录
STATIC_URL = '/static/'
UPLOAD_PATH = "E:/womaiyun/"
UPLOAD_SCRIPT_PATH = os.path.join("uploads", DEVOPS_NAME, "script")
UPLOAD_COMMAND_PATH = os.path.join("uploads", DEVOPS_NAME, "command")

PATH_LIST = [
    os.path.join(UPLOAD_PATH, UPLOAD_SCRIPT_PATH),
    os.path.join(UPLOAD_PATH, UPLOAD_COMMAND_PATH)
]

for PATH in PATH_LIST:
    if not os.path.exists(PATH):
        os.makedirs(PATH)

# APP静态资源目录url
# REMOTE_STATIC_URL = '%sremote/' % STATIC_URL

# Celery 消息队列设置 RabbitMQ
# BROKER_URL = 'amqp://guest:guest@localhost:5672//'
# Celery 消息队列设置 Redis
BROKER_URL = 'redis://localhost:6379/0'

DEBUG = True

# 本地开发数据库设置
# USE FOLLOWING SQL TO CREATE THE DATABASE NAMED APP_CODE
# SQL: CREATE DATABASE `framework_py` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci; # noqa: E501
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DEVOPS_NAME,
        'USER': "root",
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
    },
}


# MongoDB配置
MONGO_CONN = mongoengine.connect(
    db="devops",  # 需要进行操作的数据库名称
    alias='default',  # 必须定义一个default数据库
    host="localhost",
    username="",
    password="",
    port=27017,
    connect=False
)

# 自定义中间件
MIDDLEWARE += (
    'pipeline.utils.middleware.CreateUserMiddleware',
)

# 多人开发时，无法共享的本地配置可以放到新建的 local_settings.py 文件中
# 并且把 local_settings.py 加入版本管理忽略文件中
try:
    from .local_settings import *  # noqa
except ImportError:
    pass
