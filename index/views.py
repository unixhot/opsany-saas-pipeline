from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from blueapps.account.decorators import login_exempt


@login_exempt
def vue(request):
    return render(request, 'index.html')
    # return render(request, 'index.html', {"SITE_URL": ""})


@login_exempt
def healthz(request):
    from pipeline.models import UserInfo, ToolsModel
    # return render(request, 'index.html')
    
    code = 1
    status = "OK"
    message = ""
    dic = {
        "check_mysql": True,
        "check_mongo": True,
        "check_superuser": True,
        "check_jenkins": True,
    }

    try:
        if not UserInfo.objects.filter():  # 校验超级管理员初始化
            dic["check_superuser"] = False
            code, status = 0, "ERROR"
            message += "超级管理员初始化失败 "
        
        if not ToolsModel.objects.filter(tool_type="jenkins"):  # Jenkins初始化
            dic["check_jenkins"] = False
            # code, status = 0, "ERROR"
            message += "Jenkins初始化失败，流水线依赖Jenkins "
    except Exception as e:
        print("healthz_check_mongo", str(e))
        dic["check_mongo"] = False
        code, status = 0, "ERROR"
        message += "MongoDB数据库初始化失败 "
    
    if not message:
        message = "Success"
    if code == 1:
        data = {"code": code, "status": status, "message": message, "details": dic}
        return JsonResponse(data)
    else:
        data = message
        return HttpResponse(content=data, status=500)