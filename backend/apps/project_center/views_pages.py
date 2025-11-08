from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import Project, ProjectTeam, PaymentPlan, ProjectMilestone, ProjectDocument, ProjectArchive
from backend.apps.system_management.models import User

@login_required
def project_create(request):
    """新建项目页面"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 生成项目编号
                import datetime
                current_year = datetime.datetime.now().year
                project_number_seq = request.POST.get('project_number_seq', '').strip()
                
                if project_number_seq:
                    # 手动填写的序号
                    project_number = f"VIH-{current_year}-{project_number_seq.zfill(3)}"
                else:
                    # 自动生成序号
                    from django.db.models import Max
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
                    project_number = f"VIH-{current_year}-{seq:03d}"
                
                # 获取表单数据
                action = request.POST.get('action', 'submit')
                is_draft = action == 'draft'
                
                # 如果是草稿，允许某些字段为空；否则验证必填字段
                service_type = request.POST.get('service_type') or None
                business_type = request.POST.get('business_type') or None
                design_stage = request.POST.get('design_stage') or None
                
                if not is_draft:
                    # 提交时验证必填字段
                    if not service_type:
                        messages.error(request, '请选择服务类型')
                        return redirect('project_pages:project_create')
                    if not business_type:
                        messages.error(request, '请选择项目业态')
                        return redirect('project_pages:project_create')
                    if not design_stage:
                        messages.error(request, '请选择图纸阶段')
                        return redirect('project_pages:project_create')
                
                # 处理合同金额（转换为 Decimal 类型）
                from decimal import Decimal, InvalidOperation
                contract_amount_str = request.POST.get('contract_amount', '').strip()
                contract_amount = None
                if contract_amount_str:
                    try:
                        # 移除可能的逗号等分隔符
                        contract_amount_str = contract_amount_str.replace(',', '').replace('，', '')
                        contract_amount = Decimal(contract_amount_str)
                    except (ValueError, TypeError, InvalidOperation):
                        contract_amount = None
                
                # 创建项目
                project = Project.objects.create(
                    subsidiary=request.POST.get('subsidiary', 'sichuan'),
                    project_number=project_number,
                    name=request.POST.get('name') or '未命名项目',
                    alias=request.POST.get('alias', ''),
                    service_type=service_type,
                    business_type=business_type,
                    design_stage=design_stage,
                    service_professions=request.POST.getlist('service_professions'),
                    contract_number=request.POST.get('contract_number', ''),
                    contract_amount=contract_amount,
                    contract_date=request.POST.get('contract_date') or None,
                    contract_file=request.FILES.get('contract_file'),
                    client_company_name=request.POST.get('client_company_name', ''),
                    created_by=request.user,
                    business_manager=request.user,
                    status='draft' if is_draft else 'waiting_receive'
                )
                
                # 创建回款计划
                payment_phases = request.POST.getlist('payment_phase[]')
                payment_ratios = request.POST.getlist('payment_ratio[]')
                payment_dates = request.POST.getlist('payment_date[]')
                payment_triggers = request.POST.getlist('payment_trigger[]')
                
                for i, phase in enumerate(payment_phases):
                    if phase and i < len(payment_ratios) and i < len(payment_dates):
                        try:
                            from decimal import Decimal, InvalidOperation
                            
                            # 转换回款比例（确保是字符串）
                            ratio_input = payment_ratios[i]
                            if not ratio_input:
                                continue
                            
                            # 移除可能的空格和特殊字符
                            ratio_str = str(ratio_input).strip().replace(',', '').replace('，', '')
                            if not ratio_str:
                                continue
                            
                            try:
                                ratio = Decimal(ratio_str)
                            except (ValueError, InvalidOperation):
                                continue
                            
                            # 确保 contract_amount 是 Decimal 类型
                            if project.contract_amount:
                                # 如果已经是 Decimal，直接使用；否则转换为 Decimal
                                if isinstance(project.contract_amount, Decimal):
                                    contract_amt = project.contract_amount
                                else:
                                    contract_amt = Decimal(str(project.contract_amount))
                            else:
                                contract_amt = Decimal('0')
                            
                            # 计算回款金额：合同金额 * 比例 / 100
                            amount = contract_amt * ratio / Decimal('100')
                            
                            PaymentPlan.objects.create(
                                project=project,
                                phase_name=phase,
                                planned_amount=amount,
                                planned_date=payment_dates[i],
                                notes=payment_triggers[i] if i < len(payment_triggers) else ''
                            )
                        except (ValueError, TypeError, InvalidOperation) as e:
                            # 如果金额转换失败，跳过这条回款计划
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f'回款计划创建失败: {str(e)}, phase: {phase}, ratio: {payment_ratios[i] if i < len(payment_ratios) else None}')
                            continue
                
                messages.success(request, '项目创建成功！')
                if request.POST.get('action') == 'submit':
                    return redirect('project_pages:project_complete', project_id=project.id)
                return redirect('project_pages:project_list')
        except Exception as e:
            messages.error(request, f'项目创建失败：{str(e)}')
    
    import datetime
    current_year = datetime.datetime.now().year
    
    return render(request, 'project_center/project_create.html', {
        'subsidiary_choices': Project.SUBSIDIARY_CHOICES,
        'service_types': Project.SERVICE_TYPES,
        'business_types': Project.BUSINESS_TYPES,
        'design_stages': Project.DESIGN_STAGES,
        'service_professions_map': Project.SERVICE_PROFESSIONS_MAP,
        'current_year': current_year,
    })

@login_required
def project_complete(request, project_id):
    """项目信息完善页面"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            project.client_company_name = request.POST.get('client_company_name', '')
            project.client_contact_person = request.POST.get('client_contact_person', '')
            project.client_phone = request.POST.get('client_phone', '')
            project.client_email = request.POST.get('client_email', '')
            project.client_address = request.POST.get('client_address', '')
            project.design_company = request.POST.get('design_company', '')
            project.design_contact_person = request.POST.get('design_contact_person', '')
            project.design_phone = request.POST.get('design_phone', '')
            project.design_email = request.POST.get('design_email', '')
            project.project_address = request.POST.get('project_address', '')
            project.building_area = request.POST.get('building_area') or None
            project.underground_area = request.POST.get('underground_area') or None
            project.aboveground_area = request.POST.get('aboveground_area') or None
            project.building_height = request.POST.get('building_height') or None
            project.aboveground_floors = request.POST.get('aboveground_floors') or None
            project.underground_floors = request.POST.get('underground_floors') or None
            project.structure_type = request.POST.get('structure_type', '')
            project.client_special_requirements = request.POST.get('client_special_requirements', '')
            project.technical_difficulties = request.POST.get('technical_difficulties', '')
            project.risk_assessment = request.POST.get('risk_assessment', '')
            project.status = 'configuring'
            project.save()
            
            messages.success(request, '项目信息完善成功！')
            return redirect('project_pages:project_team', project_id=project.id)
        except Exception as e:
            messages.error(request, f'信息完善失败：{str(e)}')
    
    return render(request, 'project_center/project_complete.html', {
        'project': project,
    })

@login_required
def project_team(request, project_id):
    """团队配置页面"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 更新项目负责人
                project_manager_id = request.POST.get('project_manager')
                if project_manager_id:
                    project.project_manager_id = project_manager_id
                    project.save()
                
                # 配置专业团队（支持内部和外部）
                professions = project.service_professions or []
                for profession in professions:
                    # 内部专业负责人
                    leader_id = request.POST.get(f'profession_{profession}_leader')
                    if leader_id:
                        ProjectTeam.objects.update_or_create(
                            project=project,
                            user_id=leader_id,
                            defaults={
                                'role': 'professional_leader', 
                                'is_active': True,
                                'is_external': False
                            }
                        )
                    
                    # 内部专业工程师
                    engineer_ids = request.POST.getlist(f'profession_{profession}_engineers[]')
                    for engineer_id in engineer_ids:
                        ProjectTeam.objects.update_or_create(
                            project=project,
                            user_id=engineer_id,
                            defaults={
                                'role': 'engineer', 
                                'is_active': True,
                                'is_external': False
                            }
                        )
                    
                    # 外部专业负责人
                    external_leader_id = request.POST.get(f'profession_{profession}_external_leader')
                    if external_leader_id:
                        ProjectTeam.objects.update_or_create(
                            project=project,
                            user_id=external_leader_id,
                            defaults={
                                'role': 'external_leader', 
                                'is_active': True,
                                'is_external': True
                            }
                        )
                    
                    # 外部专业工程师
                    external_engineer_ids = request.POST.getlist(f'profession_{profession}_external_engineers[]')
                    for engineer_id in external_engineer_ids:
                        ProjectTeam.objects.update_or_create(
                            project=project,
                            user_id=engineer_id,
                            defaults={
                                'role': 'external_engineer', 
                                'is_active': True,
                                'is_external': True
                            }
                        )
                
                # 配置支持团队
                assistant_ids = request.POST.getlist('assistants[]')
                for user_id in assistant_ids:
                    ProjectTeam.objects.update_or_create(
                        project=project,
                        user_id=user_id,
                        defaults={
                            'role': 'technical_assistant', 
                            'is_active': True,
                            'is_external': False
                        }
                    )
                
                # 配置造价团队（区分土建和安装）
                cost_civil_ids = request.POST.getlist('cost_civil[]')
                cost_installation_ids = request.POST.getlist('cost_installation[]')
                for user_id in cost_civil_ids:
                    ProjectTeam.objects.update_or_create(
                        project=project,
                        user_id=user_id,
                        defaults={
                            'role': 'cost_engineer_civil', 
                            'is_active': True,
                            'is_external': False
                        }
                    )
                for user_id in cost_installation_ids:
                    ProjectTeam.objects.update_or_create(
                        project=project,
                        user_id=user_id,
                        defaults={
                            'role': 'cost_engineer_installation', 
                            'is_active': True,
                            'is_external': False
                        }
                    )
                
                # 配置外部造价团队
                external_cost_civil_ids = request.POST.getlist('external_cost_civil[]')
                external_cost_installation_ids = request.POST.getlist('external_cost_installation[]')
                for user_id in external_cost_civil_ids:
                    ProjectTeam.objects.update_or_create(
                        project=project,
                        user_id=user_id,
                        defaults={
                            'role': 'external_cost_engineer_civil', 
                            'is_active': True,
                            'is_external': True
                        }
                    )
                for user_id in external_cost_installation_ids:
                    ProjectTeam.objects.update_or_create(
                        project=project,
                        user_id=user_id,
                        defaults={
                            'role': 'external_cost_engineer_installation', 
                            'is_active': True,
                            'is_external': True
                        }
                    )
                
                project.status = 'waiting_start'
                project.save()
                
                messages.success(request, '团队配置成功！')
                return redirect('project_pages:project_detail', project_id=project.id)
        except Exception as e:
            messages.error(request, f'团队配置失败：{str(e)}')
    
    # 获取内部用户列表（按部门和组织架构）
    internal_users = User.objects.filter(user_type='internal').select_related('department')
    
    # 获取外部用户列表
    external_users = User.objects.filter(user_type='external')
    
    # 按职位分类
    project_managers = internal_users.filter(position__icontains='项目负责人')
    professional_leaders = internal_users.filter(position__icontains='专业负责人')
    professional_engineers = internal_users.filter(position__icontains='专业工程师')
    technical_assistants = internal_users.filter(position__icontains='技术助理')
    cost_engineers_civil = internal_users.filter(position__icontains='土建造价')
    cost_engineers_installation = internal_users.filter(position__icontains='安装造价')
    
    external_leaders = external_users.filter(position__icontains='专业负责人')
    external_engineers = external_users.filter(position__icontains='专业工程师')
    external_cost_civil = external_users.filter(position__icontains='土建造价')
    external_cost_installation = external_users.filter(position__icontains='安装造价')
    
    return render(request, 'project_center/project_team.html', {
        'project': project,
        'project_managers': project_managers,
        'professional_leaders': professional_leaders,
        'professional_engineers': professional_engineers,
        'technical_assistants': technical_assistants,
        'cost_engineers_civil': cost_engineers_civil,
        'cost_engineers_installation': cost_engineers_installation,
        'external_leaders': external_leaders,
        'external_engineers': external_engineers,
        'external_cost_civil': external_cost_civil,
        'external_cost_installation': external_cost_installation,
    })

@login_required
def project_list(request):
    """项目总览看板页面"""
    projects = Project.objects.all()
    
    # 筛选条件
    subsidiary = request.GET.get('subsidiary')
    service_type = request.GET.get('service_type')
    project_manager_id = request.GET.get('project_manager')
    status = request.GET.getlist('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if subsidiary:
        projects = projects.filter(subsidiary=subsidiary)
    if service_type:
        projects = projects.filter(service_type=service_type)
    if project_manager_id:
        projects = projects.filter(project_manager_id=project_manager_id)
    if status:
        projects = projects.filter(status__in=status)
    if date_from:
        projects = projects.filter(start_date__gte=date_from)
    if date_to:
        projects = projects.filter(start_date__lte=date_to)
    
    # 统计信息
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='in_progress').count()
    completed_projects = Project.objects.filter(status='completed').count()
    total_contract_amount = sum(p.contract_amount or 0 for p in Project.objects.all())
    total_estimated_savings = sum(p.estimated_savings or 0 for p in Project.objects.all())
    
    return render(request, 'project_center/project_list.html', {
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'total_contract_amount': total_contract_amount,
        'total_estimated_savings': total_estimated_savings,
        'subsidiary_choices': Project.SUBSIDIARY_CHOICES,
        'service_types': Project.SERVICE_TYPES,
        'status_choices': Project.PROJECT_STATUS,
        'project_managers': User.objects.filter(position__icontains='项目负责人'),
    })

@login_required
def project_detail(request, project_id):
    """项目详情仪表盘页面"""
    project = get_object_or_404(Project, id=project_id)
    
    # 获取项目统计数据
    milestones = project.milestones.all()
    payment_plans = project.payment_plans.all()
    team_members = project.team_members.filter(is_active=True)
    
    return render(request, 'project_center/project_detail.html', {
        'project': project,
        'milestones': milestones,
        'payment_plans': payment_plans,
        'team_members': team_members,
    })

@login_required
def project_query(request):
    """项目信息查询页面"""
    projects = Project.objects.all()
    
    # 查询条件
    project_number = request.GET.get('project_number')
    project_name = request.GET.get('project_name')
    client_name = request.GET.get('client_name')
    service_type = request.GET.getlist('service_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if project_number:
        projects = projects.filter(project_number__icontains=project_number)
    if project_name:
        projects = projects.filter(name__icontains=project_name)
    if client_name:
        projects = projects.filter(client_company_name__icontains=client_name)
    if service_type:
        projects = projects.filter(service_type__in=service_type)
    if date_from:
        projects = projects.filter(created_time__gte=date_from)
    if date_to:
        projects = projects.filter(created_time__lte=date_to)
    
    return render(request, 'project_center/project_query.html', {
        'projects': projects,
        'service_types': Project.SERVICE_TYPES,
    })

@login_required
def project_archive(request, project_id):
    """项目归档管理页面"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            # 获取最新归档版本
            latest_archive = ProjectArchive.objects.filter(project=project).order_by('-archive_version').first()
            next_version = (latest_archive.archive_version + 1) if latest_archive else 1
            
            # 创建归档
            archive = ProjectArchive.objects.create(
                project=project,
                archive_version=next_version,
                archived_by=request.user,
                archive_content={
                    'project_info': {
                        'project_number': project.project_number,
                        'name': project.name,
                        'status': project.status,
                    },
                    'documents': [doc.id for doc in project.documents.all()],
                    'milestones': [m.id for m in project.milestones.all()],
                },
                view_permissions=request.POST.getlist('view_permissions[]'),
                download_permissions=request.POST.getlist('download_permissions[]'),
                modify_permissions=request.POST.getlist('modify_permissions[]'),
                notes=request.POST.get('notes', '')
            )
            
            project.status = 'archived'
            project.save()
            
            messages.success(request, '项目归档成功！')
            return redirect('project_pages:project_list')
        except Exception as e:
            messages.error(request, f'归档失败：{str(e)}')
    
    archives = ProjectArchive.objects.filter(project=project).order_by('-archive_version')
    
    return render(request, 'project_center/project_archive.html', {
        'project': project,
        'archives': archives,
    })

