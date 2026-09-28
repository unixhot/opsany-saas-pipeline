# OpsAny 持續部署（pipeline）

[简体中文](./README.md) | [English](./README.en.md)

OpsAny 持續部署平台是 [OpsAny 智能維運平台](https://www.opsany.com) 的 DevOps 應用，支援對接 Jenkins API 進行圖形化流水線編排，提供憑證管理、定時任務同步、建置記錄同步等能力，幫助企業實現標準化、可視化的 CI/CD 流水線管理。

## 功能特性

- **流水線編排**：對接 Jenkins API，圖形化編排 CI/CD 流水線
- **Jenkins 憑證管理**：管理 Jenkins 憑證（使用者名稱密碼、SSH、Token 等）與憑證類型
- **定時任務同步**：同步 Jenkins 定時任務，支援更新 cron 任務
- **建置記錄同步**：同步流水線下的建置記錄，追蹤建置歷史
- **批次匯入流水線**：從 Jenkins 批次匯入既有流水線
- **業務樹**：按業務樹組織與選擇應用，建立流水線時關聯業務
- **主機選擇**：對接管控平台取得主機列表與主機分組
- **概覽統計**：近 7 天執行統計、頻繁使用應用等概覽看板

## 技術棧

- 後端：Python 3.6 + Django 2.2
- 前端：Vue 2.6
- 資料庫：MySQL + MongoDB（mongoengine）
- 容器化：Docker

## 項目結構

```bash
.
|-- blueapps                        # Python 開發框架模組
|-- blueking                        # ESB 呼叫模組
|-- component                       # 公共組件
|-- config                          # 應用設定目錄
|   |-- __init__.py                 # 應用 RUN_VER、APP_CODE 和 SECRET_KEY 等設定
|   |-- dev.py                      # 本機開發設定
|   |-- default.py                  # 全域設定
|   |-- prod.py                     # 生產環境設定
|   |-- stag.py                     # 預發布環境設定
|-- docker                          # Docker 容器化部署相關檔案
|-- frontend                        # 前端原始碼
|-- index                           # 平台入口
|-- pipeline                        # 流水線核心業務邏輯
|-- static                          # 前端建置產物
|-- templates                       # 公共範本檔案
|-- app.yml                         # 生產打包部署設定
|-- manage.py                       # Django 工程 manage
|-- requirements.txt                # Python 依賴套件列表
|-- runtime.txt                     # Python 版本設定
|-- LICENSE                         # Apache License 2.0
```

## 依賴服務

- **OpsAny PaaS**：運行在 OpsAny PaaS 之上，依賴統一登入、ESB API 閘道等服務
- **OpsAny 應用平台（devops）**：主要依賴關係，需要應用平台的應用資訊、授權資訊等
- **Jenkins**：流水線編排對接的 CI/CD 引擎

## 快速開始

### 本機開發

1. 複製程式碼並安裝依賴：

```bash
pip install -r requirements.txt
```

2. 設定資料庫連線（`config/dev.py`），並初始化資料庫：

```bash
python manage.py migrate
```

3. 啟動後端服務：

```bash
python manage.py runserver 127.0.0.1:8000
```

4. 啟動前端：

```bash
cd frontend
npm install
npm run serve
```

> 更多部署與使用說明，請參考 [OpsAny 官方文檔](https://docs.opsany.com)。

## 開源協議

本項目基於 [Apache License 2.0](./LICENSE) 開源，Copyright © OpsAny.
