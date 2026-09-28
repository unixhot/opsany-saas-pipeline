# OpsAny 持续部署（pipeline）

[English](./README.en.md) | [繁體中文](./README.zh-TW.md)

OpsAny 持续部署平台是 [OpsAny 智能运维平台](https://www.opsany.com) 的 DevOps 应用，支持对接 Jenkins API 进行图形化流水线编排，提供凭据管理、定时任务同步、构建记录同步等能力，帮助企业实现标准化、可视化的 CI/CD 流水线管理。

## 功能特性

- **流水线编排**：对接 Jenkins API，图形化编排 CI/CD 流水线
- **Jenkins 凭据管理**：管理 Jenkins 凭据（用户名密码、SSH、Token 等）与凭据类型
- **定时任务同步**：同步 Jenkins 定时任务，支持更新 cron 任务
- **构建记录同步**：同步流水线下的构建记录，追踪构建历史
- **批量导入流水线**：从 Jenkins 批量导入已有流水线
- **业务树**：按业务树组织与选择应用，创建流水线时关联业务
- **主机选择**：对接管控平台获取主机列表与主机分组
- **概览统计**：近 7 天执行统计、频繁使用应用等概览看板

## 技术栈

- 后端：Python 3.6 + Django 2.2
- 前端：Vue 2.6
- 数据库：MySQL + MongoDB（mongoengine）
- 容器化：Docker

## 项目结构

```bash
.
|-- blueapps                        # Python 开发框架模块
|-- blueking                        # ESB 调用模块
|-- component                       # 公共组件
|-- config                          # 应用配置目录
|   |-- __init__.py                 # 应用 RUN_VER、APP_CODE 和 SECRET_KEY 等配置
|   |-- dev.py                      # 本地开发配置
|   |-- default.py                  # 全局配置
|   |-- prod.py                     # 生产环境配置
|   |-- stag.py                     # 预发布环境配置
|-- docker                          # Docker 容器化部署相关文件
|-- frontend                        # 前端源码
|-- index                           # 平台入口
|-- pipeline                        # 流水线核心业务逻辑
|-- static                          # 前端构建产物
|-- templates                       # 公共模板文件
|-- app.yml                         # 生产打包部署配置
|-- manage.py                       # Django 工程 manage
|-- requirements.txt                # Python 依赖包列表
|-- runtime.txt                     # Python 版本配置
|-- LICENSE                         # Apache License 2.0
```

## 依赖服务

- **OpsAny PaaS**：运行在 OpsAny PaaS 之上，依赖统一登录、ESB API 网关等服务
- **OpsAny 应用平台（devops）**：主要依赖关系，需要应用平台的应用信息、授权信息等
- **Jenkins**：流水线编排对接的 CI/CD 引擎

## 快速开始

### 本地开发

1. 克隆代码并安装依赖：

```bash
pip install -r requirements.txt
```

2. 配置数据库连接（`config/dev.py`），并初始化数据库：

```bash
python manage.py migrate
```

3. 启动后端服务：

```bash
python manage.py runserver 127.0.0.1:8000
```

4. 启动前端：

```bash
cd frontend
npm install
npm run serve
```

> 更多部署与使用说明，请参考 [OpsAny 官方文档](https://docs.opsany.com)。

## 开源协议

本项目基于 [Apache License 2.0](./LICENSE) 开源，Copyright © OpsAny.
