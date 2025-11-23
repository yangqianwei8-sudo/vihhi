"""
生产启动相关视图
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal

from backend.apps.project_center.models import Project, ProjectTeam, ServiceProfession
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.production_quality.models_startup import (
    ProjectStartup,
    ProjectDrawingDirectory,
    ProjectDrawingFile,
    ProjectTaskBreakdown,
    ProjectStartupApproval,
)
from backend.apps.production_quality.views_pages import _context
from backend.apps.production_quality.services_startup import (
    create_default_drawing_directories,
    validate_startup_submission,
)


@login_required
def production_startup_list(request):
    """生产启动列表"""
    permission_set = get_user_permission_codes(request.user)
    
    # 获取用户可访问的项目
    if request.user.is_superuser:
        projects = Project.objects.filter(status__in=['initiation_approved', 'waiting_receive', 'configuring', 'waiting_start'])
    else:
        projects = Project.objects.filter(
            Q(project_manager=request.user) |
            Q(business_manager=request.user) |
            Q(created_by=request.user) |
            Q(team_members__user=request.user),
            status__in=['initiation_approved', 'waiting_receive', 'configuring', 'waiting_start']
        ).distinct()
    
    startups = ProjectStartup.objects.filter(
        project__in=projects
    ).select_related('project', 'project_manager_assigned', 'received_by').order_by('-created_time')
    
    context = _context(
        page_title='生产启动列表',
        page_icon='🚀',
        description='管理项目生产启动流程',
        request=request
    )
    context['startups'] = startups
    context['status_choices'] = ProjectStartup.STATUS_CHOICES
    
    return render(request, 'production_quality/startup_list.html', context)


@login_required
def production_startup_receive(request, project_id):
    """第一步：技术部经理接收项目"""
    project = get_object_or_404(Project, id=project_id)
    
    # 权限检查：只有技术部经理可以接收
    technical_manager_role = request.user.roles.filter(code='technical_manager').exists()
    if not technical_manager_role and not request.user.is_superuser:
        messages.error(request, '您没有权限接收项目')
        return redirect('production_quality_pages:production_startup_list')
    
    # 检查项目状态
    if project.status != 'initiation_approved':
        messages.warning(request, '只有已审批通过的项目才能接收')
        return redirect('production_quality_pages:production_startup_list')
    
    # 获取或创建启动记录
    startup, created = ProjectStartup.objects.get_or_create(
        project=project,
        defaults={
            'status': 'project_received',
            'received_by': request.user,
            'received_time': timezone.now(),
        }
    )
    
    # 如果是新创建的，自动创建默认图纸目录结构
    if created:
        create_default_drawing_directories(project, created_by=request.user)
    
    if request.method == 'POST':
        project_manager_id = request.POST.get('project_manager')
        if not project_manager_id:
            messages.error(request, '请选择项目经理')
            return redirect('production_quality_pages:production_startup_receive', project_id=project.id)
        
        project_manager = get_object_or_404(User, id=project_manager_id)
        
        with transaction.atomic():
            startup.project_manager_assigned = project_manager
            startup.project_manager_assigned_time = timezone.now()
            startup.status = 'drawings_uploading'
            startup.save()
            
            # 更新项目状态
            project.status = 'configuring'
            project.project_manager = project_manager
            project.save()
            
            # 创建项目团队记录
            ProjectTeam.objects.get_or_create(
                project=project,
                user=project_manager,
                role='project_manager',
                defaults={
                    'unit': 'management',
                    'is_active': True,
                }
            )
            
            # 发送通知给项目经理
            from backend.apps.project_center.models import ProjectTeamNotification
            ProjectTeamNotification.objects.create(
                project=project,
                recipient=project_manager,
                operator=request.user,
                title='项目已分配',
                message=f'项目"{project.name}"已分配给您，请开始配置项目团队和上传图纸。',
                category='team_change',
                action_url=reverse('production_quality_pages:production_startup_detail', args=[startup.id]),
                context={
                    'startup_id': startup.id,
                    'action': 'assigned',
                },
            )
        
        messages.success(request, f'项目已分配给项目经理：{project_manager.get_full_name() or project_manager.username}')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    # 获取可用项目经理列表
    available_managers = User.objects.filter(
        roles__code='project_manager'
    ).distinct().select_related('department')
    
    context = _context(
        page_title='接收项目',
        page_icon='📥',
        description=f'项目：{project.name}',
        request=request
    )
    context['project'] = project
    context['startup'] = startup
    context['available_managers'] = available_managers
    
    return render(request, 'production_quality/startup_receive.html', context)


@login_required
def production_startup_detail(request, startup_id):
    """生产启动详情页"""
    startup = get_object_or_404(
        ProjectStartup.objects.select_related(
            'project', 'project_manager_assigned', 'received_by',
            'submitted_by', 'approved_by', 'rejected_by'
        ),
        id=startup_id
    )
    
    # 权限检查
    can_view = (
        request.user.is_superuser or
        startup.project.project_manager == request.user or
        startup.project.business_manager == request.user or
        startup.project.created_by == request.user or
        startup.project.team_members.filter(user=request.user).exists()
    )
    
    if not can_view:
        messages.error(request, '您没有权限查看此项目')
        return redirect('production_quality_pages:production_startup_list')
    
    # 获取图纸目录（如果没有则创建默认结构）
    directories = ProjectDrawingDirectory.objects.filter(
        project=startup.project
    ).order_by('order', 'id')
    
    if not directories.exists():
        create_default_drawing_directories(startup.project, created_by=request.user)
        directories = ProjectDrawingDirectory.objects.filter(
            project=startup.project
        ).order_by('order', 'id')
    
    # 获取图纸文件
    drawing_files = ProjectDrawingFile.objects.filter(
        project=startup.project
    ).select_related('directory', 'uploaded_by').order_by('-uploaded_time')
    
    # 获取任务分解
    task_breakdowns = ProjectTaskBreakdown.objects.filter(
        project=startup.project
    ).select_related('profession', 'assigned_to', 'created_by').order_by('order', 'id')
    
    # 计算任务节省目标总额
    total_saving_target = task_breakdowns.aggregate(
        total=Sum('saving_target')
    )['total'] or Decimal('0')
    
    # 获取审批记录
    approvals = ProjectStartupApproval.objects.filter(
        startup=startup
    ).select_related('approver').order_by('-approval_time', '-created_time')
    
    context = _context(
        page_title='生产启动详情',
        page_icon='🚀',
        description=f'项目：{startup.project.name}',
        request=request
    )
    context['startup'] = startup
    context['project'] = startup.project
    context['directories'] = directories
    context['drawing_files'] = drawing_files
    context['task_breakdowns'] = task_breakdowns
    context['total_saving_target'] = total_saving_target
    context['contract_saving_target'] = startup.project.estimated_savings or Decimal('0')
    context['approvals'] = approvals
    
    # 权限判断
    is_project_manager = startup.project.project_manager == request.user
    is_technical_manager = request.user.roles.filter(code='technical_manager').exists() or request.user.is_superuser
    
    context['can_upload_drawings'] = is_project_manager and startup.status in ['drawings_uploading', 'team_configuring', 'tasks_creating']
    context['can_configure_team'] = is_project_manager and startup.status in ['drawings_uploading', 'team_configuring', 'tasks_creating']
    context['can_create_tasks'] = is_project_manager and startup.status in ['team_configuring', 'tasks_creating', 'waiting_approval']
    context['can_submit'] = is_project_manager and startup.status == 'tasks_creating'
    context['can_approve'] = is_technical_manager and startup.status == 'waiting_approval'
    
    return render(request, 'production_quality/startup_detail.html', context)


@login_required
def production_startup_upload_drawings(request, startup_id):
    """第二步：图纸载入"""
    startup = get_object_or_404(ProjectStartup, id=startup_id)
    
    # 权限检查：只有项目经理可以上传图纸
    if startup.project.project_manager != request.user and not request.user.is_superuser:
        messages.error(request, '您没有权限上传图纸')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    if request.method == 'POST':
        # 处理图纸上传逻辑
        directory_id = request.POST.get('directory_id')
        files = request.FILES.getlist('drawing_files')
        
        if not files:
            messages.error(request, '请选择要上传的文件')
            return redirect('production_quality_pages:production_startup_upload_drawings', startup_id=startup.id)
        
        if len(files) > 50:
            messages.error(request, '单次最多只能上传50个文件')
            return redirect('production_quality_pages:production_startup_upload_drawings', startup_id=startup.id)
        
        directory = None
        if directory_id:
            directory = ProjectDrawingDirectory.objects.filter(
                id=directory_id,
                project=startup.project
            ).first()
        
        uploaded_count = 0
        with transaction.atomic():
            for file in files:
                ProjectDrawingFile.objects.create(
                    project=startup.project,
                    directory=directory,
                    file=file,
                    file_name=file.name,
                    file_type=file.name.split('.')[-1].lower() if '.' in file.name else 'other',
                    file_size=file.size,
                    uploaded_by=request.user,
                )
                uploaded_count += 1
            
            # 更新启动状态
            if not startup.drawings_uploaded:
                startup.drawings_uploaded = True
                startup.drawings_upload_time = timezone.now()
                startup.drawings_uploaded_by = request.user
                if startup.status == 'drawings_uploading':
                    startup.status = 'team_configuring'
                startup.save()
        
        messages.success(request, f'成功上传 {uploaded_count} 个文件')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    # 获取目录结构（如果没有则创建默认结构）
    directories = ProjectDrawingDirectory.objects.filter(
        project=startup.project
    ).order_by('order', 'id')
    
    if not directories.exists():
        create_default_drawing_directories(startup.project, created_by=request.user)
        directories = ProjectDrawingDirectory.objects.filter(
            project=startup.project
        ).order_by('order', 'id')
    
    # 获取图纸文件
    drawing_files = ProjectDrawingFile.objects.filter(
        project=startup.project
    ).select_related('directory', 'uploaded_by').order_by('-uploaded_time')
    
    context = _context(
        page_title='图纸载入',
        page_icon='📁',
        description=f'项目：{startup.project.name}',
        request=request
    )
    context['startup'] = startup
    context['project'] = startup.project
    context['directories'] = directories
    context['drawing_files'] = drawing_files
    
    return render(request, 'production_quality/startup_upload_drawings.html', context)


@login_required
def production_startup_configure_team(request, startup_id):
    """第三步：配置团队"""
    startup = get_object_or_404(ProjectStartup, id=startup_id)
    
    # 权限检查：只有项目经理可以配置团队
    if startup.project.project_manager != request.user and not request.user.is_superuser:
        messages.error(request, '您没有权限配置团队')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    if request.method == 'POST':
        # 处理团队配置逻辑
        team_members = request.POST.getlist('team_members[]')
        roles = request.POST.getlist('roles[]')
        professions = request.POST.getlist('professions[]')
        
        with transaction.atomic():
            # 添加团队成员
            for i, user_id in enumerate(team_members):
                if not user_id:
                    continue
                try:
                    user = User.objects.get(id=user_id)
                    role = roles[i] if i < len(roles) else 'engineer'
                    profession_id = professions[i] if i < len(professions) and professions[i] else None
                    
                    profession = None
                    if profession_id:
                        profession = ServiceProfession.objects.filter(id=profession_id).first()
                    
                    ProjectTeam.objects.get_or_create(
                        project=startup.project,
                        user=user,
                        role=role,
                        service_profession=profession,
                        defaults={
                            'unit': ProjectTeam.ROLE_UNIT_MAP.get(role, 'management'),
                            'is_active': True,
                        }
                    )
                except User.DoesNotExist:
                    continue
            
            # 更新团队配置状态
            startup.team_configured = True
            startup.team_configured_time = timezone.now()
            if startup.status == 'team_configuring':
                startup.status = 'tasks_creating'
            startup.save()
        
        messages.success(request, '团队配置已保存')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    # 获取现有团队成员
    team_members = ProjectTeam.objects.filter(
        project=startup.project,
        is_active=True
    ).select_related('user', 'service_profession')
    
    # 获取可用人员
    available_users = User.objects.filter(
        is_active=True
    ).select_related('department')
    
    # 获取服务专业
    service_professions = ServiceProfession.objects.filter(
        service_type__in=startup.project.service_professions.values_list('service_type', flat=True)
    ).select_related('service_type').order_by('service_type__order', 'order')
    
    context = _context(
        page_title='配置团队',
        page_icon='👥',
        description=f'项目：{startup.project.name}',
        request=request
    )
    context['startup'] = startup
    context['project'] = startup.project
    context['team_members'] = team_members
    context['available_users'] = available_users
    context['service_professions'] = service_professions
    
    return render(request, 'production_quality/startup_configure_team.html', context)


@login_required
def production_startup_create_tasks(request, startup_id):
    """第四步：任务清单"""
    startup = get_object_or_404(ProjectStartup, id=startup_id)
    
    # 权限检查：只有项目经理可以创建任务
    if startup.project.project_manager != request.user and not request.user.is_superuser:
        messages.error(request, '您没有权限创建任务')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    if request.method == 'POST':
        # 处理任务创建逻辑
        import json
        tasks_data = json.loads(request.POST.get('tasks_data', '[]'))
        
        if not tasks_data:
            messages.error(request, '请至少创建一个任务')
            return redirect('production_quality_pages:production_startup_create_tasks', startup_id=startup.id)
        
        total_saving = Decimal('0')
        
        with transaction.atomic():
            # 删除旧任务
            ProjectTaskBreakdown.objects.filter(project=startup.project).delete()
            
            # 创建新任务
            for idx, task_data in enumerate(tasks_data):
                profession_id = task_data.get('profession_id')
                assigned_to_id = task_data.get('assigned_to_id')
                task_name = task_data.get('task_name', '')
                task_content = task_data.get('task_content', '')
                scope = task_data.get('scope', [])
                building_area = Decimal(str(task_data.get('building_area', 0) or 0))
                saving_target_per_sqm = Decimal(str(task_data.get('saving_target_per_sqm', 0) or 0))
                
                if not profession_id or not task_name:
                    continue
                
                profession = ServiceProfession.objects.filter(id=profession_id).first()
                if not profession:
                    continue
                
                assigned_to = None
                if assigned_to_id:
                    assigned_to = User.objects.filter(id=assigned_to_id).first()
                
                saving_target = building_area * saving_target_per_sqm if building_area and saving_target_per_sqm else None
                if saving_target:
                    total_saving += saving_target
                
                ProjectTaskBreakdown.objects.create(
                    project=startup.project,
                    task_code=f'TASK-{startup.project.project_number}-{idx+1:03d}',
                    task_name=task_name,
                    profession=profession,
                    assigned_to=assigned_to,
                    task_content=task_content,
                    scope=scope,
                    building_area=building_area if building_area > 0 else None,
                    saving_target_per_sqm=saving_target_per_sqm if saving_target_per_sqm > 0 else None,
                    saving_target=saving_target,
                    order=idx,
                    created_by=request.user,
                )
            
            # 更新启动记录
            startup.tasks_created = True
            startup.tasks_created_time = timezone.now()
            startup.total_tasks = len(tasks_data)
            startup.total_saving_target = total_saving
            startup.contract_saving_target = startup.project.estimated_savings
            startup.save()
        
        # 验证节省目标
        contract_target = startup.project.estimated_savings or Decimal('0')
        required_target = contract_target * Decimal('1.5')
        
        if total_saving < required_target:
            messages.warning(
                request,
                f'任务节省目标总额（{total_saving:.2f}元）低于合同目标的1.5倍（{required_target:.2f}元），请重新分解任务'
            )
            return redirect('production_quality_pages:production_startup_create_tasks', startup_id=startup.id)
        
        messages.success(request, f'成功创建 {len(tasks_data)} 个任务，节省目标总额：{total_saving:.2f}元')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    # 获取现有任务
    task_breakdowns = ProjectTaskBreakdown.objects.filter(
        project=startup.project
    ).select_related('profession', 'assigned_to').order_by('order', 'id')
    
    # 获取服务专业
    service_professions = ServiceProfession.objects.filter(
        service_type__in=startup.project.service_professions.values_list('service_type', flat=True)
    ).select_related('service_type').order_by('service_type__order', 'order')
    
    # 获取团队成员
    team_members = ProjectTeam.objects.filter(
        project=startup.project,
        is_active=True
    ).select_related('user', 'service_profession')
    
    context = _context(
        page_title='任务清单',
        page_icon='📋',
        description=f'项目：{startup.project.name}',
        request=request
    )
    context['startup'] = startup
    context['project'] = startup.project
    context['task_breakdowns'] = task_breakdowns
    context['service_professions'] = service_professions
    context['team_members'] = team_members
    context['contract_saving_target'] = startup.project.estimated_savings or Decimal('0')
    context['required_saving_target'] = (startup.project.estimated_savings or Decimal('0')) * Decimal('1.5')
    
    return render(request, 'production_quality/startup_create_tasks.html', context)


@login_required
def production_startup_submit(request, startup_id):
    """提交审批"""
    startup = get_object_or_404(ProjectStartup, id=startup_id)
    
    # 权限检查：只有项目经理可以提交
    if startup.project.project_manager != request.user and not request.user.is_superuser:
        messages.error(request, '您没有权限提交审批')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    # 验证提交条件
    is_valid, error_messages = validate_startup_submission(startup)
    if not is_valid:
        for error_msg in error_messages:
            messages.error(request, error_msg)
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    with transaction.atomic():
        startup.status = 'waiting_approval'
        startup.submitted_by = request.user
        startup.submitted_time = timezone.now()
        startup.save()
        
        # 创建审批记录
        ProjectStartupApproval.objects.create(
            startup=startup,
            approver=None,
            decision='pending',
        )
        
        # 发送通知给技术部经理
        from backend.apps.project_center.models import ProjectTeamNotification
        technical_managers = User.objects.filter(roles__code='technical_manager')
        for manager in technical_managers:
            ProjectTeamNotification.objects.create(
                project=startup.project,
                recipient=manager,
                operator=request.user,
                title='项目启动待审批',
                message=f'项目"{startup.project.name}"的生产启动配置已提交，请审批。',
                category='team_change',
                action_url=reverse('production_quality_pages:production_startup_approve', args=[startup.id]),
                context={
                    'startup_id': startup.id,
                    'action': 'pending_approval',
                },
            )
    
    messages.success(request, '已提交审批，等待技术部经理审批')
    return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)


@login_required
def production_startup_approve(request, startup_id):
    """审批生产启动"""
    startup = get_object_or_404(ProjectStartup, id=startup_id)
    
    # 权限检查：只有技术部经理可以审批
    technical_manager_role = request.user.roles.filter(code='technical_manager').exists()
    if not technical_manager_role and not request.user.is_superuser:
        messages.error(request, '您没有权限审批')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    if startup.status != 'waiting_approval':
        messages.warning(request, '当前状态不允许审批')
        return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comment = request.POST.get('comment', '').strip()
        
        if decision == 'approved':
            with transaction.atomic():
                startup.status = 'approved'
                startup.approved_by = request.user
                startup.approved_time = timezone.now()
                startup.approval_comment = comment
                startup.started_time = timezone.now()
                startup.save()
                
                # 更新项目状态
                startup.project.status = 'in_progress'
                startup.project.save()
                
                # 更新审批记录
                approval = startup.approvals.filter(decision='pending').first()
                if approval:
                    approval.approver = request.user
                    approval.approval_time = timezone.now()
                    approval.decision = 'approved'
                    approval.comment = comment
                    approval.save()
                
                # 创建任务推送给团队成员
                from backend.apps.project_center.models import ProjectTask
                task_breakdowns = ProjectTaskBreakdown.objects.filter(project=startup.project)
                for task_breakdown in task_breakdowns:
                    if task_breakdown.assigned_to:
                        ProjectTask.objects.create(
                            project=startup.project,
                            title=f'任务：{task_breakdown.task_name}',
                            task_type='project_complete_info',
                            description=task_breakdown.task_content,
                            assigned_to=task_breakdown.assigned_to,
                            assigned_role='engineer',
                            target_unit='internal_tech',
                            created_by=request.user,
                        )
                
                # 发送通知给项目经理
                from backend.apps.project_center.models import ProjectTeamNotification
                ProjectTeamNotification.objects.create(
                    project=startup.project,
                    recipient=startup.project.project_manager,
                    operator=request.user,
                    title='项目启动已审批通过',
                    message=f'项目"{startup.project.name}"的生产启动已审批通过，项目已正式启动。',
                    category='team_change',
                    action_url=reverse('production_quality_pages:production_startup_detail', args=[startup.id]),
                    context={
                        'startup_id': startup.id,
                        'action': 'approved',
                    },
                )
            
            messages.success(request, '项目启动已审批通过')
            return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
        
        elif decision == 'rejected':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, '请填写驳回原因')
                return redirect('production_quality_pages:production_startup_approve', startup_id=startup.id)
            
            with transaction.atomic():
                startup.status = 'rejected'
                startup.rejected_by = request.user
                startup.rejected_time = timezone.now()
                startup.rejection_reason = rejection_reason
                startup.save()
                
                # 更新审批记录
                approval = startup.approvals.filter(decision='pending').first()
                if approval:
                    approval.approver = request.user
                    approval.approval_time = timezone.now()
                    approval.decision = 'rejected'
                    approval.comment = rejection_reason
                    approval.save()
                
                # 发送通知给项目经理
                from backend.apps.project_center.models import ProjectTeamNotification
                ProjectTeamNotification.objects.create(
                    project=startup.project,
                    recipient=startup.project.project_manager,
                    operator=request.user,
                    title='项目启动审批已驳回',
                    message=f'项目"{startup.project.name}"的生产启动审批被驳回。驳回原因：{rejection_reason}',
                    category='team_change',
                    action_url=reverse('production_quality_pages:production_startup_detail', args=[startup.id]),
                    context={
                        'startup_id': startup.id,
                        'action': 'rejected',
                    },
                )
            
            messages.warning(request, '已驳回项目启动申请')
            return redirect('production_quality_pages:production_startup_detail', startup_id=startup.id)
    
    context = _context(
        page_title='审批项目启动',
        page_icon='✅',
        description=f'项目：{startup.project.name}',
        request=request
    )
    context['startup'] = startup
    context['project'] = startup.project
    
    return render(request, 'production_quality/startup_approve.html', context)
