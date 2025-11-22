"""项目立项视图"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from .models import (
    Project,
    ProjectInitiationApproval,
    ProjectTeamNotification,
    ProjectTeam,
    ServiceType,
    ServiceProfession,
)
from .forms_initiation import (
    ProjectInitiationStep1Form,
    ProjectInitiationStep2Form,
    ProjectInitiationStep3Form,
    ProjectInitiationStep4Form,
    ProjectInitiationSubmitForm,
)
from backend.apps.system_management.models import User, Department, Role
from backend.apps.system_management.services import get_user_permission_codes


def _is_business_department_user(user):
    """判断用户是否属于商务部"""
    if not user or not user.department:
        return False
    # 检查部门代码或名称
    dept_code = user.department.code or ''
    dept_name = user.department.name or ''
    return 'BUSINESS' in dept_code.upper() or '商务' in dept_name


def _get_business_manager():
    """获取商务部经理"""
    from backend.apps.system_management.models import Role, Department
    
    # 方法1: 通过角色查找
    try:
        business_manager_role = Role.objects.filter(code='business_manager').first()
        if business_manager_role:
            business_managers = business_manager_role.users.filter(is_active=True)
            if business_managers.exists():
                return business_managers.first()
    except Exception:
        pass
    
    # 方法2: 通过部门查找（商务部负责人）
    try:
        business_dept = Department.objects.filter(
            code__icontains='BUSINESS'
        ).first()
        if business_dept and business_dept.manager:
            return business_dept.manager
    except Exception:
        pass
    
    # 方法3: 通过职位查找
    try:
        manager = User.objects.filter(
            position__icontains='商务',
            is_active=True
        ).first()
        if manager:
            return manager
    except Exception:
        pass
    
    return None


def _get_technical_manager():
    """获取技术部经理"""
    from backend.apps.system_management.models import Role, Department
    
    # 方法1: 通过角色查找
    try:
        technical_manager_role = Role.objects.filter(code='technical_manager').first()
        if technical_manager_role:
            technical_managers = technical_manager_role.users.filter(is_active=True)
            if technical_managers.exists():
                return technical_managers.first()
    except Exception:
        pass
    
    # 方法2: 通过部门查找（技术部负责人）
    try:
        tech_dept = Department.objects.filter(
            code__icontains='TECH'
        ).first()
        if tech_dept and tech_dept.manager:
            return tech_dept.manager
    except Exception:
        pass
    
    # 方法3: 通过职位查找
    try:
        manager = User.objects.filter(
            position__icontains='技术',
            is_active=True
        ).first()
        if manager:
            return manager
    except Exception:
        pass
    
    return None


@login_required
def project_initiation_receive(request, project_id):
    """技术部经理接收项目立项"""
    project = get_object_or_404(Project, id=project_id)
    approval = get_object_or_404(ProjectInitiationApproval, project=project)
    
    # 权限检查：只有技术部经理可以接收
    if approval.status != 'pending_technical_manager':
        messages.warning(request, '当前状态不允许接收')
        return redirect('project_pages:project_initiation_detail', project_id=project.id)
    
    technical_manager_role = request.user.roles.filter(code='technical_manager').exists()
    if not technical_manager_role and approval.technical_manager != request.user:
        messages.error(request, '您没有权限接收此项目')
        return redirect('project_pages:project_initiation_detail', project_id=project.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '').strip()
        
        if action == 'receive':
            with transaction.atomic():
                # 技术部经理接收项目
                approval.technical_manager_approved_time = timezone.now()
                approval.technical_manager_comment = comment
                approval.status = 'approved'
                approval.approved_by = request.user
                approval.approved_time = timezone.now()
                project.status = 'initiation_approved'
                
                # 生成项目编号
                if not project.project_number:
                    import datetime
                    from django.db.models import Max
                    current_year = datetime.datetime.now().year
                    max_number = Project.objects.filter(
                        project_number__startswith=f'VIH-{current_year}-'
                    ).aggregate(max_num=Max('project_number'))['max_num']
                    
                    if max_number:
                        try:
                            seq = int(max_number.split('-')[-1]) + 1
                        except (ValueError, IndexError):
                            seq = 1
                    else:
                        seq = 1
                    project.project_number = f"VIH-{current_year}-{seq:03d}"
                
                approval.save()
                project.save()
                
                # 通知提交人项目已接收
                ProjectTeamNotification.objects.create(
                    project=project,
                    recipient=approval.submitted_by,
                    operator=request.user,
                    title='项目已接收',
                    message=f'项目"{project.name}"立项已通过，技术部经理已接收项目，项目编号：{project.project_number}。',
                    category='team_change',
                    action_url=reverse('project_pages:project_initiation_detail', args=[project.id]),
                    context={
                        'approval_id': approval.id,
                        'action': 'received',
                        'notification_type': 'project_initiation_received',
                    },
                )
                
                messages.success(request, f'项目已接收，项目编号：{project.project_number}')
                return redirect('project_pages:project_initiation_detail', project_id=project.id)
        
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, '请填写驳回原因')
                return redirect('project_pages:project_initiation_receive', project_id=project.id)
            
            with transaction.atomic():
                approval.rejected_by = request.user
                approval.rejected_time = timezone.now()
                approval.rejection_reason = rejection_reason
                approval.status = 'rejected'
                project.status = 'initiation_rejected'
                
                # 通知提交人审批被驳回
                ProjectTeamNotification.objects.create(
                    project=project,
                    recipient=approval.submitted_by,
                    operator=request.user,
                    title='项目立项已驳回',
                    message=f'项目"{project.name}"立项审批被驳回。驳回原因：{rejection_reason}',
                    category='team_change',
                    action_url=reverse('project_pages:project_initiation_detail', args=[project.id]),
                    context={
                        'approval_id': approval.id,
                        'action': 'rejected',
                        'notification_type': 'project_initiation_rejected',
                    },
                )
                
                approval.save()
                project.save()
                
                messages.warning(request, '已驳回项目立项申请')
                return redirect('project_pages:project_initiation_detail', project_id=project.id)
    
    # 显示接收页面（使用审批页面的模板，但显示完整项目信息）
    context = {
        'page_title': '接收项目立项',
        'page_icon': '📥',
        'description': project.name,
        'project': project,
        'approval': approval,
    }
    
    return render(request, 'project_center/initiation_receive.html', context)


# 占位函数 - 需要恢复完整实现
@login_required
def project_initiation_create(request):
    """创建项目立项"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
def project_initiation_step2(request, project_id):
    """项目立项 - 第二步"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
def project_initiation_step3(request, project_id):
    """项目立项 - 第三步"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
def project_initiation_step4(request, project_id):
    """项目立项 - 第四步"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
def project_initiation_submit(request, project_id):
    """提交项目立项审批"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
def project_initiation_list(request):
    """项目立项列表"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('home')


@login_required
def project_initiation_detail(request, project_id):
    """项目立项详情"""
    # 权限检查：只有商务部员工可以查看
    if not _is_business_department_user(request.user):
        messages.error(request, '您没有权限查看项目立项')
        return redirect('home')
    
    project = get_object_or_404(Project, id=project_id)
    approval = getattr(project, 'initiation_approval', None)
    
    # 判断是否是审批人
    is_approver = False
    if approval:
        # 商务部经理可以审批
        business_manager = _get_business_manager()
        if business_manager and business_manager == request.user and approval.status == 'pending_supervisor':
            is_approver = True
        
        # 技术部经理可以接收
        technical_manager = _get_technical_manager()
        if technical_manager and technical_manager == request.user and approval.status == 'pending_technical_manager':
            is_approver = True
    
    # 判断是否可以编辑：只有商务部员工可以编辑，且项目状态为草稿或被驳回
    can_edit = _is_business_department_user(request.user) and project.status in ['draft', 'initiation_rejected'] and project.created_by == request.user
    
    # 判断是否可以重新提交审批：项目被驳回后，编辑完成可以重新提交
    can_resubmit = False
    if approval and project.status == 'initiation_rejected' and project.created_by == request.user:
        can_resubmit = True
    
    # 判断是否可以审批 (for business manager)
    can_approve = False
    if approval and approval.status == 'pending_supervisor':
        business_manager = _get_business_manager()
        if business_manager and business_manager == request.user:
            can_approve = True
    
    # 判断是否可以接收 (for technical manager)
    can_receive = False
    if approval and approval.status == 'pending_technical_manager':
        technical_manager_role = request.user.roles.filter(code='technical_manager').exists()
        technical_manager = _get_technical_manager()
        if technical_manager_role or (technical_manager and technical_manager == request.user):
            can_receive = True
    
    # 判断是否可以撤回：只有项目创建人可以在技术部经理未审批前撤回
    can_withdraw = False
    if approval and project.created_by == request.user:
        if approval.status in ['pending_supervisor', 'pending_technical_manager'] and project.status == 'waiting_initiation_approval':
            can_withdraw = True
    
    context = {
        'page_title': f'项目立项详情 - {project.project_number or "待生成编号"}',
        'page_icon': '📋',
        'description': project.name,
        'project': project,
        'approval': approval,
        'can_edit': can_edit,
        'can_approve': can_approve,
        'can_withdraw': can_withdraw,
        'can_resubmit': can_resubmit,
        'can_receive': can_receive,
    }
    return render(request, 'project_center/initiation_detail.html', context)


@login_required
def project_initiation_approve(request, project_id):
    """审批项目立项"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
@require_http_methods(["POST"])
def project_initiation_withdraw(request, project_id):
    """撤回项目立项审批"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
@require_http_methods(["POST"])
def project_initiation_delete(request, project_id):
    """删除项目立项"""
    messages.error(request, '功能正在恢复中，请稍后再试')
    return redirect('project_pages:project_initiation_list')


@login_required
@require_http_methods(["GET"])
def get_service_professions(request):
    """获取指定服务类型对应的服务专业列表（AJAX）"""
    return JsonResponse({'error': '功能正在恢复中'}, status=503)
