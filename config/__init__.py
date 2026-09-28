# -*- coding: utf-8 -*-
from __future__ import absolute_import

__all__ = ['celery_app', 'RUN_VER', 'APP_CODE', 'SECRET_KEY', 'BK_URL', 'BASE_DIR', 'PAAS_ESB_URL', 'PAAS_LOGIN_URL']

import os

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from blueapps.core.celery import celery_app

# app 基本信息

# SaaS运行版本，如非必要请勿修改
RUN_VER = 'open'
# SaaS应用ID
APP_CODE = 'pipeline'
# SaaS安全密钥，注意请勿泄露该密钥
SECRET_KEY = os.getenv("APP_TOKEN", "442601e0-7fe8-449a-b0f2-f14c31cf9024")
# SaaS平台URL
BK_URL = os.getenv("BK_PAAS_HOST", "https://192.168.0.111")
PAAS_ESB_URL = "http://192.168.0.111:8002"
PAAS_LOGIN_URL = "http://192.168.0.111:8003"

# Upload目录
UPLOAD_PATH = os.getenv("UPLOAD_PATH", "/opt/opsany")

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 工作台首页默认用户图标路径
DEFAULT_USER_ICON = os.getenv("DEFAULT_USER_ICON",
                              "uploads/workbench/user_icon/edfb99ee-08d6-41b8-ac5f-117fb86b0912.png")


DEFAULT_LANGUAGE = "chinese_simplified"
DEFAULT_THEME = "theme-default"