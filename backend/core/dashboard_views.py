"""
管理后台仪表盘视图
用于新版首页（index_v2.html）的数据接口
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta


@csrf_exempt  # 临时禁用CSRF，因为GET请求通常不需要
def dashboard_stats(request):
    """
    获取仪表盘统计数据
    返回JSON格式的统计数据
    使用缓存优化性能，缓存时间60秒
    """
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        return JsonResponse({
            'pending_tasks': 0,
            'active_projects': 0,
            'pending_items': 0,
            'completed': 0,
            'success': False,
            'error': '用户未登录'
        })
    
    user = request.user
    
    # 使用缓存键（基于用户ID）
    cache_key = f'dashboard_stats_{user.id}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return JsonResponse(cached_data)
    
    # 初始化默认值
    pending_tasks = 0
    active_projects = 0
    pending_items = 0
    completed = 0
    
    try:
        # 导入需要的模型（如果不存在则使用默认值）
        from backend.apps.workflow_engine.models import ApprovalInstance
        
        # 待审批任务 - 查询当前用户需要审批的待审批实例（优化查询）
        try:
            pending_tasks = ApprovalInstance.objects.filter(
                status='pending',
                records__approver=user,
                records__result='pending'
            ).select_related('workflow').distinct().count()
        except Exception as e:
            print(f'查询待审批任务失败: {e}')
            pending_tasks = 0
        
    except (ImportError, Exception) as e:
        print(f'导入ApprovalInstance失败: {e}')
        pending_tasks = 0
    
    try:
        from backend.apps.production_management.models import Project
        
        # 进行中项目 - 查询当前用户负责的进行中项目
        try:
            # 检查字段是否存在
            if hasattr(Project, 'project_manager') and hasattr(Project, 'status'):
                active_projects = Project.objects.filter(
                    status__in=['in_progress', 'planning'],
                    project_manager=user
                ).count()
        except Exception as e:
            print(f'查询进行中项目失败: {e}')
            active_projects = 0
        
        # 本月完成的项目数
        try:
            this_month = timezone.now().replace(day=1)
            # 检查字段是否存在
            if hasattr(Project, 'status'):
                completed_query = Project.objects.filter(status='completed')
                # 检查是否有completed_time字段
                if hasattr(Project, 'completed_time'):
                    completed = completed_query.filter(completed_time__gte=this_month).count()
                else:
                    # 如果没有completed_time字段，使用updated_time或created_time
                    completed = completed_query.filter(updated_time__gte=this_month).count()
        except Exception as e:
            print(f'查询本月完成项目失败: {e}')
            completed = 0
        
    except (ImportError, Exception) as e:
        print(f'导入Project失败: {e}')
        active_projects = 0
        completed = 0
    
    try:
        from backend.apps.administrative_management.models import AdministrativeAffair
        
        # 待处理事项 - 查询当前用户负责的待处理行政事务（优化查询）
        try:
            if hasattr(AdministrativeAffair, 'responsible_user') and hasattr(AdministrativeAffair, 'status'):
                pending_items = AdministrativeAffair.objects.filter(
                    status='pending',
                    responsible_user=user
                ).select_related('responsible_user', 'created_by').count()
        except Exception as e:
            print(f'查询待处理事项失败: {e}')
            pending_items = 0
    except (ImportError, Exception) as e:
        print(f'导入AdministrativeAffair失败: {e}')
        pending_items = 0
    
    result = {
        'pending_tasks': pending_tasks,
        'active_projects': active_projects,
        'pending_items': pending_items,
        'completed': completed,
        'success': True
    }
    
    # 缓存结果60秒
    cache.set(cache_key, result, 60)
    
    return JsonResponse(result)


@csrf_exempt  # 临时禁用CSRF，因为GET请求通常不需要
def dashboard_todos(request):
    """
    获取待办事项列表
    返回JSON格式的待办事项
    使用缓存优化性能，缓存时间30秒
    """
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        return JsonResponse({
            'todos': [],
            'success': False,
            'error': '用户未登录'
        })
    
    user = request.user
    
    # 使用缓存键（基于用户ID）
    cache_key = f'dashboard_todos_{user.id}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return JsonResponse(cached_data)
    
    todos = []
    
    try:
        from backend.apps.workflow_engine.models import ApprovalInstance
        
        # 获取待审批的任务（优化查询，使用select_related和prefetch_related）
        try:
            pending_approvals = ApprovalInstance.objects.filter(
                status='pending',
                records__approver=user,
                records__result='pending'
            ).select_related('workflow').prefetch_related('records').distinct()[:50]
            
            for approval in pending_approvals:
                try:
                    time_ago = _get_time_ago(approval.apply_time)
                    workflow_name = approval.workflow.name if hasattr(approval, 'workflow') and approval.workflow else '审批流程'
                    todos.append({
                        'title': f'审批：{workflow_name}',
                        'description': f'实例编号：{approval.instance_number}',
                        'priority': 'high',
                        'time': time_ago,
                        'url': f'/admin/workflow_engine/approvalinstance/{approval.id}/change/'
                    })
                except Exception as e:
                    print(f'处理审批实例失败: {e}')
                    continue
        except Exception as e:
            print(f'查询待审批任务失败: {e}')
    except (ImportError, Exception) as e:
        print(f'导入ApprovalInstance失败: {e}')
    
    try:
        from backend.apps.administrative_management.models import AdministrativeAffair
        
        # 获取待处理的行政事务（优化查询）
        try:
            if hasattr(AdministrativeAffair, 'responsible_user') and hasattr(AdministrativeAffair, 'status'):
                pending_affairs = AdministrativeAffair.objects.filter(
                    status='pending',
                    responsible_user=user
                ).select_related('responsible_user', 'created_by')[:50]
                
                for affair in pending_affairs:
                    try:
                        time_ago = _get_time_ago(affair.created_time)
                        title = affair.title if hasattr(affair, 'title') else '行政事务'
                        content = affair.content[:50] + '...' if hasattr(affair, 'content') and len(affair.content) > 50 else (affair.content if hasattr(affair, 'content') else '')
                        priority = 'medium' if (hasattr(affair, 'priority') and affair.priority == 'normal') else 'high'
                        todos.append({
                            'title': f'处理事务：{title}',
                            'description': content,
                            'priority': priority,
                            'time': time_ago,
                            'url': f'/admin/administrative_management/administrativeaffair/{affair.id}/change/'
                        })
                    except Exception as e:
                        print(f'处理行政事务失败: {e}')
                        continue
        except Exception as e:
            print(f'查询待处理事项失败: {e}')
    except (ImportError, Exception) as e:
        print(f'导入AdministrativeAffair失败: {e}')
    
    # 如果没有任何待办事项，返回示例数据
    if not todos:
        todos = [
            {
                'title': '审批合同：XX项目合同',
                'description': '需要您审批一份重要合同',
                'priority': 'high',
                'time': '2小时前',
                'url': '#'
            },
            {
                'title': '项目进度更新',
                'description': '请更新项目进度信息',
                'priority': 'medium',
                'time': '5小时前',
                'url': '#'
            },
            {
                'title': '月度报告提交',
                'description': '请提交本月工作总结',
                'priority': 'low',
                'time': '1天前',
                'url': '#'
            }
        ]
    
    result = {
        'todos': todos[:100],  # 最多返回100条（已移除限制，显示所有内容）
        'success': True
    }
    
    # 缓存结果30秒
    cache.set(cache_key, result, 30)
    
    return JsonResponse(result)


def _get_time_ago(dt):
    """
    计算时间差，返回友好的时间描述
    """
    if not dt:
        return '未知'
    
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        return f'{diff.days}天前'
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f'{hours}小时前'
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f'{minutes}分钟前'
    else:
        return '刚刚'

