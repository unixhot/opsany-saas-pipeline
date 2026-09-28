## 生产环境启动

```
INSTALL_PATH="/opt/opsany"
PAAS_DOCKER_REG="registry.cn-beijing.aliyuncs.com/opsany"
mkdir -p ${INSTALL_PATH}/logs/pipeline

docker run -d --restart=always --name opsany-saas-ce-pipeline \
       -p 7017:80 \
       -v ${INSTALL_PATH}/conf/opsany-saas/pipeline/pipeline-supervisor.ini:/etc/supervisord.d/pipeline.ini \
       -v ${INSTALL_PATH}/conf/opsany-saas/pipeline/pipeline-uwsgi.ini:/opt/opsany/uwsgi/pipeline.ini \
       -v ${INSTALL_PATH}/conf/opsany-saas/pipeline/pipeline-init.py:/opt/opsany/pipeline/config/__init__.py \
       -v ${INSTALL_PATH}/conf/opsany-saas/pipeline/pipeline-prod.py:/opt/opsany/pipeline/config/prod.py \
       -v ${INSTALL_PATH}/conf/opsany-saas/pipeline/pipeline-nginx.conf:/etc/nginx/http.d/default.conf \
       -v ${INSTALL_PATH}/logs/pipeline:/opt/opsany/logs/pipeline \
       -v /etc/localtime:/etc/localtime:ro \
       ${PAAS_DOCKER_REG}/opsany-saas-ce-pipeline:1.7.0
```
