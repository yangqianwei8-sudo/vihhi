from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages

def home(request):
    """系统首页"""
    # 如果未登录，重定向到登录页
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html')

def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', 'home')
                    return redirect(next_url)
                else:
                    messages.error(request, '用户账户已被禁用')
            else:
                messages.error(request, '用户名或密码错误')
        else:
            messages.error(request, '请输入用户名和密码')
    
    return render(request, 'login.html')

def logout_view(request):
    """登出页面"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')

@csrf_exempt
def health_check(request):
    """健康检查端点"""
    return JsonResponse({
        'status': 'healthy',
        'service': '维海科技生产信息化管理系统',
        'version': '1.0.0',
        'timestamp': '2025-11-06T14:01:28Z'
    })
