# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^account/', include('blueapps.account.urls')),
    url(r'^', include('index.urls')),
    url(r'^api/pipeline/v0_1/', include('pipeline.urls')),
    url(r'^api/pipeline/esb/v0_1/', include('pipeline.esb_urls'))
]
