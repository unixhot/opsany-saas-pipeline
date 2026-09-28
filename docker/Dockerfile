# Base Image
FROM registry.cn-beijing.aliyuncs.com/opsany/python:3.6.15-alpine3.15

# Install Python Env
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk add --no-cache gcc g++ make libffi-dev openssl-dev zlib-dev jpeg-dev mariadb-dev openssh-client tzdata nginx \
    && pip --no-cache-dir install supervisor==4.2.5 uwsgi==2.0.21 -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com 

# Crate Install PATH
RUN mkdir -p /opt/opsany/logs/pipeline && mkdir /etc/supervisord.d && mkdir -p /opt/opsany/uwsgi

# Add Code File
ADD ./src /opt/opsany/pipeline

# Install SaaS Env
RUN pip --no-cache-dir install -r /opt/opsany/pipeline/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Time Setting
ENV TZ="Asia/Shanghai"

#Supervisord Config
ADD supervisord.conf /etc/supervisord.conf
ADD nginx.conf /etc/nginx/nginx.conf
ADD pipeline-uwsgi.ini /opt/opsany/uwsgi/pipeline.ini
ADD pipeline-supervisor.ini /etc/supervisord.d/pipeline.ini
ADD nginx-supervisor.ini /etc/supervisord.d/nginx.ini
ADD pipeline-nginx.conf /etc/nginx/http.d/default.conf

# Outside Port
EXPOSE 80

#supervisord start
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
