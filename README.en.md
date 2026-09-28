# OpsAny Continuous Deployment (pipeline)

[简体中文](./README.md) | [繁體中文](./README.zh-TW.md)

The OpsAny Continuous Deployment platform is a DevOps application of the [OpsAny intelligent operations platform](https://www.opsany.com). It integrates with the Jenkins API for graphical pipeline orchestration, providing credential management, scheduled task synchronization, build record synchronization, and more, helping enterprises standardize and visualize their CI/CD pipeline management.

## Features

- **Pipeline orchestration**: Integrates with the Jenkins API for graphical CI/CD pipeline orchestration
- **Jenkins credential management**: Manages Jenkins credentials (username/password, SSH, tokens, etc.) and credential types
- **Scheduled task synchronization**: Syncs Jenkins scheduled tasks and supports updating cron jobs
- **Build record synchronization**: Syncs build records under a pipeline to track build history
- **Batch pipeline import**: Imports existing pipelines from Jenkins in bulk
- **Business tree**: Organizes and selects applications by business tree when creating pipelines
- **Host selection**: Integrates with the control platform to fetch host lists and host groups
- **Overview statistics**: Dashboards for last-7-days execution statistics, frequently used applications, and more

## Tech Stack

- Backend: Python 3.6 + Django 2.2
- Frontend: Vue 2.6
- Database: MySQL + MongoDB (mongoengine)
- Containerization: Docker

## Project Structure

```bash
.
|-- blueapps                        # Python development framework module
|-- blueking                        # ESB invocation module
|-- component                       # Shared components
|-- config                          # Application configuration directory
|   |-- __init__.py                 # RUN_VER, APP_CODE, SECRET_KEY and other configs
|   |-- dev.py                      # Local development configuration
|   |-- default.py                  # Global configuration
|   |-- prod.py                     # Production configuration
|   |-- stag.py                     # Staging configuration
|-- docker                          # Docker containerization files
|-- frontend                        # Frontend source code
|-- index                           # Platform entry
|-- pipeline                        # Core pipeline business logic
|-- static                          # Frontend build artifacts
|-- templates                       # Shared template files
|-- app.yml                         # Production packaging/deployment config
|-- manage.py                       # Django manage.py
|-- requirements.txt                # Python dependency list
|-- runtime.txt                     # Python version configuration
|-- LICENSE                         # Apache License 2.0
```

## Dependencies

- **OpsAny PaaS**: Runs on top of OpsAny PaaS, relying on unified login, the ESB API gateway, and other services
- **OpsAny Application Platform (devops)**: Primary dependency; requires application information, authorization information, etc. from the application platform
- **Jenkins**: The CI/CD engine for pipeline orchestration

## Quick Start

### Local Development

1. Clone the code and install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the database connection (`config/dev.py`) and initialize the database:

```bash
python manage.py migrate
```

3. Start the backend service:

```bash
python manage.py runserver 127.0.0.1:8000
```

4. Start the frontend:

```bash
cd frontend
npm install
npm run serve
```

> For more deployment and usage instructions, please refer to the [OpsAny official documentation](https://docs.opsany.com).

## License

This project is open sourced under the [Apache License 2.0](./LICENSE). Copyright © OpsAny.
