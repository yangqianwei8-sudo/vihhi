from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import render

@api_view(['GET'])
def api_root(request, format=None):
    """API 根目录，显示所有可用的 API 端点"""
    return Response({
        'system': reverse('system:user-list', request=request, format=format),
        'projects': reverse('project:project-list', request=request, format=format),
        'customers': reverse('customer:client-list', request=request, format=format),
        'message': '维海科技生产信息化管理系统 API',
        'version': '1.0.0'
    })

def api_docs(request):
    """API 文档页面"""
    return render(request, 'api/docs.html')
