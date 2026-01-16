from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Avg, Max
from django.core.paginator import Paginator
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import Department
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted as core_permission_granted, _build_full_top_nav
from backend.apps.personnel_management.models import (
    Employee, Attendance, Leave, Training, TrainingParticipant,
    Performance, Salary, LaborContract, Position,
    EmployeeArchive, EmployeeMovement,
    WelfareProject, WelfareDistribution,
    RecruitmentRequirement, Resume, Interview,
    EmployeeCommunication, EmployeeCare, EmployeeActivity, ActivityParticipant,
    EmployeeComplaint, EmployeeSuggestion,
)
from .forms import (
    EmployeeForm, LeaveForm, TrainingForm, PerformanceForm,
    SalaryForm, LaborContractForm, AttendanceForm, EmployeeMovementForm,
    EmployeeArchiveForm, WelfareDistributionForm, RecruitmentRequirementForm,
    WelfareProjectForm, ResumeForm, InterviewForm,
    EmployeeCommunicationForm, EmployeeCareForm, EmployeeActivityForm,
    EmployeeComplaintForm, EmployeeSuggestionForm
)


def _permission_granted(required_code, user_permissions: set) -> bool:
    """检查权限"""
    if not required_code:
        return True
    if '__all__' in user_permissions:
        return True
    return required_code in user_permissions


# 使用统一的顶部导航菜单生成函数
from backend.core.views import _build_full_top_nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, use_personnel_nav=False):
    """构建页面上下文
    
    Args:
        use_personnel_nav: 已废弃，统一使用全局系统主菜单
    """
    context = {
        "page_title": page_title or "",
        "page_icon": page_icon or "",
        "description": description or "",
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航菜单（与客户管理模块保持一致）
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 添加左侧菜单
        context['personnel_menu'] = _build_personnel_sidebar_nav(permission_set, request.path)
    else:
        context['full_top_nav'] = []
        context['personnel_menu'] = []
    
    return context


def _build_personnel_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成人事管理模块的左侧菜单导航（使用计划管理格式）
    
    Args:
        permission_set: 用户权限集合
        request_path: 当前请求路径，用于判断激活状态
        active_id: 当前激活的菜单项ID（可选）
    
    Returns:
        list: 分组菜单项列表，格式与计划管理一致
    """
    from django.urls import reverse, NoReverseMatch
    
    # 定义人事管理菜单结构（分组格式，与计划管理一致）
    PERSONNEL_MENU_STRUCTURE = [
        {
            'id': 'organization',
            'label': '组织架构',
            'icon': '🏢',
            'permission': 'personnel_management.organization.view',
            'children': [
                {
                    'label': '组织架构',
                    'url_name': 'personnel_pages:organization_management',
                    'permission': 'personnel_management.organization.view',
                    'icon': '🏢',
                    'path_keywords': ['organization', 'department', 'position'],
                    'subitems': [
                        {
                            'label': '部门管理',
                            'url_name': 'personnel_pages:department_management',
                            'permission': 'personnel_management.organization.manage_department',
                            'icon': '🏛️',
                            'path_keywords': ['department'],
                        },
                        {
                            'label': '职位管理',
                            'url_name': 'personnel_pages:position_management',
                            'permission': 'personnel_management.organization.manage_position',
                            'icon': '💼',
                            'path_keywords': ['position'],
                        },
                        {
                            'label': '组织架构图',
                            'url_name': 'personnel_pages:org_chart',
                            'permission': 'personnel_management.organization.view_chart',
                            'icon': '📊',
                            'path_keywords': ['org-chart', 'chart'],
                        },
                    ],
                },
                {
                    'label': '员工管理',
                    'url_name': 'personnel_pages:employee_management',
                    'permission': 'personnel_management.employee.view',
                    'icon': '👥',
                    'path_keywords': ['employee', 'employees'],
                    'subitems': [
                        {
                            'label': '员工列表',
                            'url_name': 'personnel_pages:employee_management',
                            'permission': 'personnel_management.employee.view',
                            'icon': '📋',
                            'path_keywords': ['employee'],
                        },
                        {
                            'label': '员工档案',
                            'url_name': 'personnel_pages:employee_archive_management',
                            'permission': 'personnel_management.employee_archive.view',
                            'icon': '📁',
                            'path_keywords': ['archive'],
                        },
                        {
                            'label': '上传档案',
                            'url_name': 'personnel_pages:employee_archive_create',
                            'permission': 'personnel_management.employee_archive.create',
                            'icon': '📤',
                            'path_keywords': ['archive/create'],
                        },
                        {
                            'label': '员工异动',
                            'url_name': 'personnel_pages:employee_movement_management',
                            'permission': 'personnel_management.employee_movement.view',
                            'icon': '🔄',
                            'path_keywords': ['movement'],
                        },
                        {
                            'label': '新增异动',
                            'url_name': 'personnel_pages:employee_movement_create',
                            'permission': 'personnel_management.movement.create',
                            'icon': '➕',
                            'path_keywords': ['movement/create'],
                        },
                    ],
                },
            ],
        },
        {
            'label': '考勤管理',
            'url_name': 'personnel_pages:attendance_management',
            'permission': 'personnel_management.attendance.view',
            'icon': '⏰',
            'path_keywords': ['attendance'],
            'subitems': [
                {
                    'label': '考勤记录',
                    'url_name': 'personnel_pages:attendance_management',
                    'permission': 'personnel_management.attendance.view',
                    'icon': '📋',
                    'path_keywords': ['attendance'],
                },
            ],
        },
        {
            'label': '请假管理',
            'url_name': 'personnel_pages:leave_management',
            'permission': 'personnel_management.leave.view',
            'icon': '📅',
            'path_keywords': ['leave', 'leaves'],
            'subitems': [
                {
                    'label': '请假列表',
                    'url_name': 'personnel_pages:leave_management',
                    'permission': 'personnel_management.leave.view',
                    'icon': '📋',
                    'path_keywords': ['leave'],
                },
            ],
        },
        {
            'label': '培训管理',
            'url_name': 'personnel_pages:training_management',
            'permission': 'personnel_management.training.view',
            'icon': '🎓',
            'path_keywords': ['training', 'trainings'],
            'subitems': [
                {
                    'label': '培训列表',
                    'url_name': 'personnel_pages:training_management',
                    'permission': 'personnel_management.training.view',
                    'icon': '📋',
                    'path_keywords': ['training'],
                },
            ],
        },
        {
            'label': '绩效考核',
            'url_name': 'personnel_pages:performance_management',
            'permission': 'personnel_management.performance.view',
            'icon': '📊',
            'path_keywords': ['performance', 'performances'],
            'subitems': [
                {
                    'label': '考核列表',
                    'url_name': 'personnel_pages:performance_management',
                    'permission': 'personnel_management.performance.view',
                    'icon': '📋',
                    'path_keywords': ['performance'],
                },
            ],
        },
        {
            'label': '薪资管理',
            'url_name': 'personnel_pages:salary_management',
            'permission': 'personnel_management.salary.view',
            'icon': '💵',
            'path_keywords': ['salary', 'salaries'],
            'subitems': [
                {
                    'label': '薪资列表',
                    'url_name': 'personnel_pages:salary_management',
                    'permission': 'personnel_management.salary.view',
                    'icon': '📋',
                    'path_keywords': ['salary'],
                },
                {
                    'label': '新增薪资',
                    'url_name': 'personnel_pages:salary_create',
                    'permission': 'personnel_management.salary.manage',
                    'icon': '➕',
                    'path_keywords': ['salary/create'],
                },
            ],
        },
        {
            'label': '劳动合同',
            'url_name': 'personnel_pages:contract_management',
            'permission': 'personnel_management.contract.view',
            'icon': '📄',
            'path_keywords': ['contract', 'contracts'],
            'subitems': [
                {
                    'label': '合同列表',
                    'url_name': 'personnel_pages:contract_management',
                    'permission': 'personnel_management.contract.view',
                    'icon': '📋',
                    'path_keywords': ['contract'],
                },
                {
                    'label': '新增合同',
                    'url_name': 'personnel_pages:contract_create',
                    'permission': 'personnel_management.contract.create',
                    'icon': '➕',
                    'path_keywords': ['contract/create'],
                },
            ],
        },
        {
            'label': '福利管理',
            'url_name': 'personnel_pages:welfare_management',
            'permission': 'personnel_management.welfare.view',
            'icon': '🎁',
            'path_keywords': ['welfare'],
            'subitems': [
                {
                    'label': '发放列表',
                    'url_name': 'personnel_pages:welfare_management',
                    'permission': 'personnel_management.welfare.view',
                    'icon': '📋',
                    'path_keywords': ['welfare'],
                },
                {
                    'label': '新增项目',
                    'url_name': 'personnel_pages:welfare_project_create',
                    'permission': 'personnel_management.welfare.create',
                    'icon': '➕',
                    'path_keywords': ['welfare/project/create'],
                },
                {
                    'label': '新增发放',
                    'url_name': 'personnel_pages:welfare_distribution_create',
                    'permission': 'personnel_management.welfare.create',
                    'icon': '➕',
                    'path_keywords': ['welfare/distribution/create'],
                },
            ],
        },
        {
            'label': '招聘管理',
            'url_name': 'personnel_pages:recruitment_management',
            'permission': 'personnel_management.recruitment.view',
            'icon': '📝',
            'path_keywords': ['recruitment'],
            'subitems': [
                {
                    'label': '需求列表',
                    'url_name': 'personnel_pages:recruitment_management',
                    'permission': 'personnel_management.recruitment.view',
                    'icon': '📋',
                    'path_keywords': ['recruitment'],
                },
                {
                    'label': '新增需求',
                    'url_name': 'personnel_pages:recruitment_requirement_create',
                    'permission': 'personnel_management.recruitment.create',
                    'icon': '➕',
                    'path_keywords': ['recruitment/requirement/create'],
                },
                {
                    'label': '新增简历',
                    'url_name': 'personnel_pages:resume_create',
                    'permission': 'personnel_management.recruitment.create',
                    'icon': '➕',
                    'path_keywords': ['recruitment/resume/create'],
                },
                {
                    'label': '新增面试',
                    'url_name': 'personnel_pages:interview_create',
                    'permission': 'personnel_management.recruitment.create',
                    'icon': '➕',
                    'path_keywords': ['recruitment/interview/create'],
                },
            ],
        },
        {
            'label': '员工关系',
            'url_name': 'personnel_pages:employee_relations_management',
            'permission': 'personnel_management.employee_relations.view',
            'icon': '🤝',
            'path_keywords': ['relations', 'employee-relations'],
            'subitems': [
                {
                    'label': '关系管理',
                    'url_name': 'personnel_pages:employee_relations_management',
                    'permission': 'personnel_management.employee_relations.view',
                    'icon': '📋',
                    'path_keywords': ['employee-relations'],
                },
                {
                    'label': '新增沟通',
                    'url_name': 'personnel_pages:employee_communication_create',
                    'permission': 'personnel_management.employee_relations.create',
                    'icon': '➕',
                    'path_keywords': ['employee-relations/communication/create'],
                },
                {
                    'label': '新增关怀',
                    'url_name': 'personnel_pages:employee_care_create',
                    'permission': 'personnel_management.employee_relations.create',
                    'icon': '➕',
                    'path_keywords': ['employee-relations/care/create'],
                },
                {
                    'label': '新增活动',
                    'url_name': 'personnel_pages:employee_activity_create',
                    'permission': 'personnel_management.employee_relations.create',
                    'icon': '➕',
                    'path_keywords': ['employee-relations/activity/create'],
                },
                {
                    'label': '新增投诉',
                    'url_name': 'personnel_pages:employee_complaint_create',
                    'permission': 'personnel_management.employee_relations.create',
                    'icon': '➕',
                    'path_keywords': ['employee-relations/complaint/create'],
                },
                {
                    'label': '新增建议',
                    'url_name': 'personnel_pages:employee_suggestion_create',
                    'permission': 'personnel_management.employee_relations.create',
                    'icon': '➕',
                    'path_keywords': ['employee-relations/suggestion/create'],
                },
            ],
        },
    ]
    
    # 构建分组菜单（格式与计划管理一致）
    menu_groups = []
    
    for group in PERSONNEL_MENU_STRUCTURE:
        # 检查分组权限
        if group.get('permission') and not _permission_granted(group['permission'], permission_set):
            continue
        
        # 处理有children的分组（如组织架构）
        if group.get('children'):
            children_items = []
            for child in group['children']:
                # 检查子项权限
                if child.get('permission') and not _permission_granted(child['permission'], permission_set):
                    continue
                
                child_item = {
                    'label': child['label'],
                    'icon': child.get('icon', ''),
                    'url': '#',
                    'active': False,
                }
                
                # 获取URL
                url_name = child.get('url_name')
                if url_name:
                    try:
                        child_item['url'] = reverse(url_name)
                    except NoReverseMatch:
                        child_item['url'] = '#'
                
                # 检查是否激活
                if request_path:
                    for keyword in child.get('path_keywords', []):
                        path_parts = request_path.split('/')
                        if keyword in path_parts or keyword in request_path:
                            child_item['active'] = True
                            break
                
                children_items.append(child_item)
            
            if children_items:
                menu_groups.append({
                    'label': group['label'],
                    'expanded': any(item['active'] for item in children_items),
                    'children': children_items,
                })
        else:
            # 处理扁平结构（没有children的菜单项）
            # 检查主菜单权限
            if group.get('permission') and not _permission_granted(group['permission'], permission_set):
                continue
            
            # 构建主菜单项
            main_item = {
                'label': group['label'],
                'icon': group.get('icon', ''),
                'url': '#',
                'active': False,
            }
            
            # 获取主菜单URL
            url_name = group.get('url_name')
            if url_name:
                try:
                    main_item['url'] = reverse(url_name)
                except NoReverseMatch:
                    main_item['url'] = '#'
            
            # 检查是否激活
            if request_path:
                for keyword in group.get('path_keywords', []):
                    path_parts = request_path.split('/')
                    if keyword in path_parts or keyword in request_path:
                        main_item['active'] = True
                        break
            
            # 处理子菜单
            children_items = []
            if group.get('subitems'):
                for subitem in group['subitems']:
                    # 检查子菜单权限
                    if subitem.get('permission') and not _permission_granted(subitem['permission'], permission_set):
                        continue
                    
                    sub_item = {
                        'label': subitem['label'],
                        'icon': subitem.get('icon', ''),
                        'url': '#',
                        'active': False,
                    }
                    
                    # 获取子菜单URL
                    sub_url_name = subitem.get('url_name')
                    if sub_url_name:
                        try:
                            sub_item['url'] = reverse(sub_url_name)
                        except NoReverseMatch:
                            sub_item['url'] = '#'
                    
                    # 检查子菜单是否激活
                    if request_path:
                        for keyword in subitem.get('path_keywords', []):
                            path_parts = request_path.split('/')
                            if keyword in path_parts or keyword in request_path:
                                sub_item['active'] = True
                                main_item['active'] = True  # 子菜单激活时，主菜单也激活
                                break
                    
                    children_items.append(sub_item)
            
            # 如果有子菜单，创建分组；否则创建单个菜单项
            if children_items:
                menu_groups.append({
                    'label': group['label'],
                    'expanded': main_item['active'] or any(item['active'] for item in children_items),
                    'children': [main_item] + children_items,
                })
            else:
                menu_groups.append({
                    'label': group['label'],
                    'expanded': False,
                    'children': [main_item],
                })
    
    return menu_groups


@login_required
def personnel_home(request):
    """人事管理主页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 员工档案统计
        if _permission_granted('personnel_management.employee.view', permission_codes):
            try:
                total_employees = Employee.objects.filter(status='active').count()
                new_employees_this_month = Employee.objects.filter(
                    entry_date__gte=this_month_start
                ).count()
                
                summary_cards.append({
                    'label': '员工档案',
                    'icon': '👤',
                    'value': f'{total_employees}',
                    'subvalue': f'在职员工 · 本月入职 {new_employees_this_month} 人',
                    'url': reverse('personnel_pages:employee_management'),
                })
            except Exception:
                pass
        
        # 考勤管理统计
        if _permission_granted('personnel_management.attendance.view', permission_codes):
            try:
                today_attendance = Attendance.objects.filter(attendance_date=today).count()
                today_late = Attendance.objects.filter(attendance_date=today, is_late=True).count()
                
                summary_cards.append({
                    'label': '考勤管理',
                    'icon': '⏰',
                    'value': f'{today_attendance}',
                    'subvalue': f'今日打卡 · 迟到 {today_late} 人',
                    'url': reverse('personnel_pages:attendance_management'),
                })
            except Exception:
                pass
        
        # 请假管理统计
        if _permission_granted('personnel_management.leave.view', permission_codes):
            try:
                pending_leaves = Leave.objects.filter(status='pending').count()
                this_month_leaves = Leave.objects.filter(start_date__gte=this_month_start).count()
                
                summary_cards.append({
                    'label': '请假管理',
                    'icon': '📅',
                    'value': f'{pending_leaves}',
                    'subvalue': f'待审批 · 本月 {this_month_leaves} 条',
                    'url': reverse('personnel_pages:leave_management'),
                })
            except Exception:
                pass
        
        # 培训管理统计
        if _permission_granted('personnel_management.training.view', permission_codes):
            try:
                ongoing_trainings = Training.objects.filter(status='ongoing').count()
                this_month_trainings = Training.objects.filter(training_date__gte=this_month_start).count()
                
                summary_cards.append({
                    'label': '培训管理',
                    'icon': '📚',
                    'value': f'{ongoing_trainings}',
                    'subvalue': f'进行中 · 本月 {this_month_trainings} 场',
                    'url': reverse('personnel_pages:training_management'),
                })
            except Exception:
                pass
        
        # 绩效考核统计
        if _permission_granted('personnel_management.performance.view', permission_codes):
            try:
                current_year = today.year
                pending_performances = Performance.objects.filter(
                    period_year=current_year,
                    status__in=['draft', 'self_assessment', 'manager_review']
                ).count()
                
                summary_cards.append({
                    'label': '绩效考核',
                    'icon': '📊',
                    'value': f'{pending_performances}',
                    'subvalue': f'待完成考核',
                    'url': reverse('personnel_pages:performance_management'),
                })
            except Exception:
                pass
        
        # 薪资管理统计
        if _permission_granted('personnel_management.salary.view', permission_codes):
            try:
                this_month_salaries = Salary.objects.filter(
                    salary_month__year=today.year,
                    salary_month__month=today.month
                ).count()
                
                summary_cards.append({
                    'label': '薪资管理',
                    'icon': '💰',
                    'value': f'{this_month_salaries}',
                    'subvalue': f'本月薪资记录',
                    'url': reverse('personnel_pages:salary_management'),
                })
            except Exception:
                pass
        
        # 劳动合同统计
        if _permission_granted('personnel_management.contract.view', permission_codes):
            try:
                active_contracts = LaborContract.objects.filter(status='active').count()
                expiring_soon = LaborContract.objects.filter(
                    end_date__isnull=False,
                    end_date__gte=today,
                    end_date__lte=today + timedelta(days=90)
                ).count()
                
                summary_cards.append({
                    'label': '劳动合同',
                    'icon': '📄',
                    'value': f'{active_contracts}',
                    'subvalue': f'生效中 · 90天内到期 {expiring_soon} 份',
                    'url': reverse('personnel_pages:contract_management'),
                })
            except Exception:
                pass
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块区域
    sections = []
    
    # 快捷操作区域
    quick_actions = []
    
    if _permission_granted('personnel_management.employee.create', permission_codes):
        try:
            quick_actions.append({
                'label': '添加员工',
                'icon': '➕',
                'description': '添加新员工档案',
                'url': reverse('personnel_pages:employee_create'),
                'link_label': '添加员工 →'
            })
        except NoReverseMatch:
            pass
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions
        })
    
    # 功能模块区域
    modules = []
    
    if _permission_granted('personnel_management.employee.view', permission_codes):
        try:
            modules.append({
                'label': '员工档案管理',
                'icon': '👤',
                'description': '管理员工基本信息、档案和合同',
                'url': reverse('personnel_pages:employee_management'),
                'link_label': '进入模块 →'
            })
        except NoReverseMatch:
            pass
    
    if _permission_granted('personnel_management.attendance.view', permission_codes):
        try:
            modules.append({
                'label': '考勤管理',
                'icon': '⏰',
                'description': '管理员工考勤记录和统计',
                'url': reverse('personnel_pages:attendance_management'),
                'link_label': '进入模块 →'
            })
        except NoReverseMatch:
            pass
    
    if _permission_granted('personnel_management.leave.view', permission_codes):
        try:
            modules.append({
                'label': '请假管理',
                'icon': '📅',
                'description': '管理员工请假申请和审批',
                'url': reverse('personnel_pages:leave_management'),
                'link_label': '进入模块 →'
            })
        except NoReverseMatch:
            pass
    
    if _permission_granted('personnel_management.organization.view', permission_codes):
        try:
            modules.append({
                'label': '组织架构',
                'icon': '🏢',
                'description': '管理组织架构、部门和职位',
                'url': reverse('personnel_pages:organization_management'),
                'link_label': '进入模块 →'
            })
        except NoReverseMatch:
            pass
    
    if modules:
        sections.append({
            'title': '功能模块',
            'description': '人事管理的各个功能模块入口',
            'items': modules
        })
    
    context = _context(
        "人事管理",
        "👥",
        "企业人事管理平台",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        use_personnel_nav=True
    )
    return render(request, "personnel_management/home.html", context)


@login_required
def employee_management(request):
    """员工档案管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee.view', permission_codes):
        messages.error(request, '您没有权限访问员工档案管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    department_id = request.GET.get('department_id', '')
    status = request.GET.get('status', '')
    
    # 获取员工列表
    try:
        employees = Employee.objects.select_related('department', 'user', 'created_by').order_by('-entry_date')
        
        # 应用筛选条件
        if search:
            employees = employees.filter(
                Q(employee_number__icontains=search) |
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        if department_id:
            employees = employees.filter(department_id=int(department_id))
        if status:
            employees = employees.filter(status=status)
        
        # 分页
        paginator = Paginator(employees, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取员工列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status='active').count()
        resigned_employees = Employee.objects.filter(status='resigned').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "员工档案管理",
        "👤",
        "管理员工档案信息",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    # 获取部门列表（用于筛选）
    try:
        departments = Department.objects.filter(is_active=True).order_by('order', 'name')
    except Exception:
        departments = []
    
    context.update({
        'page_obj': page_obj,
        'employees': page_obj.object_list if page_obj else [],
        'status_choices': Employee.STATUS_CHOICES,
        'departments': departments,
        'current_search': search,
        'current_department_id': department_id,
        'current_status': status,
    })
    return render(request, "personnel_management/employee_list.html", context)


@login_required
def employee_create(request):
    """新增员工档案"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee.create', permission_codes):
        messages.error(request, '您没有权限新增员工档案')
        return redirect('personnel_pages:employee_management')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            # 自动生成员工编号
            if not employee.employee_number:
                current_year = timezone.now().year
                max_employee = Employee.objects.filter(
                    employee_number__startswith=f'EMP-{current_year}-'
                ).aggregate(max_num=Max('employee_number'))['max_num']
                if max_employee:
                    try:
                        seq = int(max_employee.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                employee.employee_number = f'EMP-{current_year}-{seq:04d}'
            employee.created_by = request.user
            employee.save()
            messages.success(request, f'员工档案 {employee.name} 创建成功！')
            return redirect('personnel_pages:employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm()
    
    context = _context(
        "新增员工档案",
        "➕",
        "创建新的员工档案信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_form.html", context)


@login_required
def employee_update(request, employee_id):
    """编辑员工档案"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee.edit', permission_codes):
        messages.error(request, '您没有权限编辑员工档案')
        return redirect('personnel_pages:employee_detail', employee_id=employee_id)
    
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'员工档案 {employee.name} 更新成功！')
            return redirect('personnel_pages:employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm(instance=employee)
    
    context = _context(
        f"编辑员工档案 - {employee.name}",
        "✏️",
        f"编辑员工 {employee.name} 的档案信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'employee': employee,
        'is_create': False,
    })
    return render(request, "personnel_management/employee_form.html", context)


@login_required
def employee_detail(request, employee_id):
    """员工档案详情"""
    import logging
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Avg, Q
    
    logger = logging.getLogger(__name__)
    
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee.view', permission_codes):
        messages.error(request, '您没有权限查看员工详情')
        return redirect('personnel_pages:employee_management')
    
    try:
        logger.info(f'开始加载员工详情页面，employee_id={employee_id}')
        
        employee = get_object_or_404(
            Employee.objects.select_related('department', 'user', 'created_by'), 
            id=employee_id
        )
        
        logger.info(f'员工对象加载成功: {employee.name}, department={employee.department}, user={employee.user}, created_by={employee.created_by}')
        
        # 计算统计数据
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 考勤统计（本月）
        attendance_stats = employee.attendances.filter(
            attendance_date__gte=current_month_start
        ).aggregate(
            total_days=Count('id'),
            late_count=Count('id', filter=Q(is_late=True)),
            early_leave_count=Count('id', filter=Q(is_early_leave=True)),
            absent_count=Count('id', filter=Q(is_absent=True)),
            total_overtime=Sum('overtime_hours')
        )
        
        # 请假统计（本年）
        leave_stats = employee.leaves.filter(
            start_date__gte=current_year_start,
            status='approved'
        ).aggregate(
            total_count=Count('id'),
            total_days=Sum('days')
        )
        
        # 培训统计
        training_stats = employee.trainings.aggregate(
            total_count=Count('id'),
            completed_count=Count('id', filter=Q(training__status='completed')),
            avg_score=Avg('score')
        )
        
        # 绩效统计（本年）
        performance_stats = employee.performances.filter(
            period_year=now.year,
            status='completed'
        ).aggregate(
            total_count=Count('id'),
            avg_score=Avg('total_score')
        )
        
        # 项目参与统计（通过用户关联）
        project_count = 0
        recent_projects = []
        recent_project_teams = []
        if employee.user:
            try:
                from backend.apps.production_management.models import ProjectTeam
                project_teams = ProjectTeam.objects.filter(
                    user=employee.user,
                    is_active=True
                ).select_related('project').order_by('-join_date')[:5]
                project_count = ProjectTeam.objects.filter(
                    user=employee.user,
                    is_active=True
                ).values('project').distinct().count()
                recent_projects = [pt.project for pt in project_teams]
                recent_project_teams = list(project_teams)
            except Exception as e:
                logger.warning(f'加载项目参与信息失败: {str(e)}')
        
        # 薪资统计（最近12个月）
        salary_stats = employee.salaries.filter(
            salary_month__gte=current_year_start
        ).aggregate(
            total_count=Count('id'),
            avg_net_salary=Avg('net_salary'),
            total_income=Sum('total_income')
        )
        
        # 劳动合同统计
        contract_stats = employee.contracts.filter(
            status='active'
        ).aggregate(
            active_count=Count('id')
        )
        
        # 最近考勤记录（最近7天）
        recent_attendances = employee.attendances.order_by('-attendance_date')[:7]
        
        # 最近请假记录（最近5条）
        recent_leaves = employee.leaves.order_by('-created_time')[:5]
        
        # 最近培训记录（最近5条）
        recent_trainings = employee.trainings.select_related('training').order_by('-created_time')[:5]
        
        # 构建统计卡片
        summary_cards = []
        
        context = _context(
            f"员工详情 - {employee.name}",
            "👤",
            f"查看员工 {employee.name} 的详细信息",
            summary_cards=summary_cards,
            request=request,
            use_personnel_nav=True
        )
        context.update({
            'employee': employee,
            'attendance_stats': attendance_stats,
            'leave_stats': leave_stats,
            'training_stats': training_stats,
            'performance_stats': performance_stats,
            'salary_stats': salary_stats,
            'contract_stats': contract_stats,
            'recent_attendances': recent_attendances,
            'recent_leaves': recent_leaves,
            'recent_trainings': recent_trainings,
            'recent_projects': recent_projects,
            'recent_project_teams': recent_project_teams,
            'project_count': project_count,
        })
        
        logger.info('开始渲染模板')
        return render(request, "personnel_management/employee_detail.html", context)
    except Exception as e:
        logger.error(f'员工详情页面错误: {str(e)}', exc_info=True)
        from django.http import HttpResponseServerError
        from django.conf import settings
        if settings.DEBUG:
            import traceback
            error_detail = traceback.format_exc()
            return HttpResponseServerError(f"服务器内部错误: {str(e)}\n\n{error_detail}")
        else:
            return HttpResponseServerError("服务器内部错误，请稍后重试")


@login_required
def attendance_management(request):
    """考勤管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.attendance.view', permission_codes):
        messages.error(request, '您没有权限访问考勤管理')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', today.strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', today.strftime('%Y-%m-%d'))
    employee_id = request.GET.get('employee_id', '')
    
    # 获取考勤列表
    try:
        attendances = Attendance.objects.select_related('employee').order_by('-attendance_date', '-created_time')
        
        # 应用筛选条件
        if search:
            attendances = attendances.filter(
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )
        if date_from:
            attendances = attendances.filter(attendance_date__gte=date_from)
        if date_to:
            attendances = attendances.filter(attendance_date__lte=date_to)
        if employee_id:
            attendances = attendances.filter(employee_id=int(employee_id))
        
        # 分页
        paginator = Paginator(attendances, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取考勤列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        today_attendances = Attendance.objects.filter(attendance_date=today).count()
        today_late = Attendance.objects.filter(attendance_date=today, is_late=True).count()
        today_absent = Attendance.objects.filter(attendance_date=today, is_absent=True).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "考勤管理",
        "⏰",
        "管理员工考勤记录",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'attendances': page_obj.object_list if page_obj else [],
        'current_search': search,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_employee_id': employee_id,
    })
    return render(request, "personnel_management/attendance_list.html", context)


@login_required
def leave_management(request):
    """请假管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.leave.view', permission_codes):
        messages.error(request, '您没有权限访问请假管理')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    leave_type = request.GET.get('leave_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取请假列表
    try:
        leaves = Leave.objects.select_related('employee', 'approver').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            leaves = leaves.filter(
                Q(leave_number__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search) |
                Q(reason__icontains=search)
            )
        if leave_type:
            leaves = leaves.filter(leave_type=leave_type)
        if status:
            leaves = leaves.filter(status=status)
        if date_from:
            leaves = leaves.filter(start_date__gte=date_from)
        if date_to:
            leaves = leaves.filter(end_date__lte=date_to)
        
        # 分页
        paginator = Paginator(leaves, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取请假列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_leaves = Leave.objects.count()
        pending_leaves = Leave.objects.filter(status='pending').count()
        approved_leaves = Leave.objects.filter(status='approved').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "请假管理",
        "📅",
        "管理请假申请",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'leaves': page_obj.object_list if page_obj else [],
        'leave_type_choices': Leave.TYPE_CHOICES,
        'status_choices': Leave.STATUS_CHOICES,
        'current_search': search,
        'current_leave_type': leave_type,
        'current_status': status,
        'current_date_from': date_from,
        'current_date_to': date_to,
    })
    return render(request, "personnel_management/leave_list.html", context)


@login_required
def leave_create(request):
    """新增请假申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.leave.create', permission_codes):
        messages.error(request, '您没有权限申请请假')
        return redirect('personnel_pages:leave_management')
    
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            # 自动生成请假单号
            if not leave.leave_number:
                current_year = timezone.now().year
                max_leave = Leave.objects.filter(
                    leave_number__startswith=f'LEAVE-{current_year}-'
                ).aggregate(max_num=Max('leave_number'))['max_num']
                if max_leave:
                    try:
                        seq = int(max_leave.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                leave.leave_number = f'LEAVE-{current_year}-{seq:04d}'
            leave.status = 'pending'
            leave.save()
            messages.success(request, f'请假申请 {leave.leave_number} 提交成功！')
            return redirect('personnel_pages:leave_detail', leave_id=leave.id)
    else:
        form = LeaveForm()
        # 如果是当前用户申请，默认选择当前用户对应的员工
        try:
            employee = Employee.objects.get(user=request.user)
            form.fields['employee'].initial = employee
        except Employee.DoesNotExist:
            pass
    
    context = _context(
        "新增请假申请",
        "➕",
        "提交新的请假申请",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/leave_form.html", context)


@login_required
def leave_update(request, leave_id):
    """编辑请假申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.leave.create', permission_codes):
        messages.error(request, '您没有权限编辑请假申请')
        return redirect('personnel_pages:leave_management')
    
    leave = get_object_or_404(Leave, id=leave_id)
    
    # 只有草稿状态或待审批状态可以编辑
    if leave.status not in ['draft', 'pending']:
        messages.error(request, '该请假申请已审批，无法编辑')
        return redirect('personnel_pages:leave_detail', leave_id=leave_id)
    
    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, f'请假申请 {leave.leave_number} 更新成功！')
            return redirect('personnel_pages:leave_detail', leave_id=leave.id)
    else:
        form = LeaveForm(instance=leave)
    
    context = _context(
        f"编辑请假申请 - {leave.leave_number}",
        "✏️",
        f"编辑请假申请 {leave.leave_number}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'leave': leave,
        'is_create': False,
    })
    return render(request, "personnel_management/leave_form.html", context)


@login_required
def training_create(request):
    """新增培训记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.training.manage', permission_codes):
        messages.error(request, '您没有权限创建培训记录')
        return redirect('personnel_pages:training_management')
    
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save(commit=False)
            # 自动生成培训编号
            if not training.training_number:
                current_year = timezone.now().year
                max_training = Training.objects.filter(
                    training_number__startswith=f'TRAIN-{current_year}-'
                ).aggregate(max_num=Max('training_number'))['max_num']
                if max_training:
                    try:
                        seq = int(max_training.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                training.training_number = f'TRAIN-{current_year}-{seq:04d}'
            training.created_by = request.user
            training.save()
            messages.success(request, f'培训记录 {training.title} 创建成功！')
            return redirect('personnel_pages:training_detail', training_id=training.id)
    else:
        form = TrainingForm()
    
    context = _context(
        "新增培训记录",
        "➕",
        "创建新的培训记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/training_form.html", context)


@login_required
def training_update(request, training_id):
    """编辑培训记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.training.manage', permission_codes):
        messages.error(request, '您没有权限编辑培训记录')
        return redirect('personnel_pages:training_detail', training_id=training_id)
    
    training = get_object_or_404(Training, id=training_id)
    
    if request.method == 'POST':
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, f'培训记录 {training.title} 更新成功！')
            return redirect('personnel_pages:training_detail', training_id=training.id)
    else:
        form = TrainingForm(instance=training)
    
    context = _context(
        f"编辑培训记录 - {training.title}",
        "✏️",
        f"编辑培训记录 {training.title}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'training': training,
        'is_create': False,
    })
    return render(request, "personnel_management/training_form.html", context)


@login_required
def leave_detail(request, leave_id):
    """请假详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.leave.view', permission_codes):
        messages.error(request, '您没有权限查看请假详情')
        return redirect('personnel_pages:leave_management')
    
    leave_obj = get_object_or_404(Leave.objects.select_related('employee', 'approver'), id=leave_id)
    
    context = _context(
        f"请假详情 - {leave_obj.leave_number}",
        "📅",
        f"查看请假申请 {leave_obj.leave_number} 的详细信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'leave': leave_obj,
    })
    return render(request, "personnel_management/leave_detail.html", context)


@login_required
def training_management(request):
    """培训管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.training.view', permission_codes):
        messages.error(request, '您没有权限访问培训管理')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取培训列表
    try:
        trainings = Training.objects.select_related('created_by').prefetch_related('participants').order_by('-training_date', '-created_time')
        
        # 应用筛选条件
        if search:
            trainings = trainings.filter(
                Q(training_number__icontains=search) |
                Q(title__icontains=search) |
                Q(trainer__icontains=search) |
                Q(description__icontains=search)
            )
        if status:
            trainings = trainings.filter(status=status)
        if date_from:
            trainings = trainings.filter(training_date__gte=date_from)
        if date_to:
            trainings = trainings.filter(training_date__lte=date_to)
        
        # 分页
        paginator = Paginator(trainings, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取培训列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_trainings = Training.objects.count()
        ongoing_trainings = Training.objects.filter(status='ongoing').count()
        completed_trainings = Training.objects.filter(status='completed').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "培训管理",
        "📚",
        "管理培训记录",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'trainings': page_obj.object_list if page_obj else [],
        'status_choices': Training.STATUS_CHOICES,
        'current_search': search,
        'current_status': status,
        'current_date_from': date_from,
        'current_date_to': date_to,
    })
    return render(request, "personnel_management/training_list.html", context)


@login_required
def training_detail(request, training_id):
    """培训详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.training.view', permission_codes):
        messages.error(request, '您没有权限查看培训详情')
        return redirect('personnel_pages:training_management')
    
    training = get_object_or_404(Training.objects.select_related('created_by').prefetch_related('participants__employee'), id=training_id)
    
    context = _context(
        f"培训详情 - {training.title}",
        "📚",
        f"查看培训 {training.title} 的详细信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'training': training,
    })
    return render(request, "personnel_management/training_detail.html", context)


@login_required
def performance_create(request):
    """新增绩效考核"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.performance.manage', permission_codes):
        messages.error(request, '您没有权限创建绩效考核')
        return redirect('personnel_pages:performance_management')
    
    if request.method == 'POST':
        form = PerformanceForm(request.POST)
        if form.is_valid():
            performance = form.save(commit=False)
            # 自动生成考核编号
            if not performance.performance_number:
                current_year = timezone.now().year
                max_performance = Performance.objects.filter(
                    performance_number__startswith=f'PERF-{current_year}-'
                ).aggregate(max_num=Max('performance_number'))['max_num']
                if max_performance:
                    try:
                        seq = int(max_performance.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                performance.performance_number = f'PERF-{current_year}-{seq:04d}'
            performance.created_by = request.user
            performance.save()
            messages.success(request, f'绩效考核 {performance.performance_number} 创建成功！')
            return redirect('personnel_pages:performance_detail', performance_id=performance.id)
    else:
        form = PerformanceForm()
        # 默认当前年度
        form.fields['period_year'].initial = timezone.now().year
    
    context = _context(
        "新增绩效考核",
        "➕",
        "创建新的绩效考核记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/performance_form.html", context)


@login_required
def performance_update(request, performance_id):
    """编辑绩效考核"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.performance.manage', permission_codes):
        messages.error(request, '您没有权限编辑绩效考核')
        return redirect('personnel_pages:performance_detail', performance_id=performance_id)
    
    performance = get_object_or_404(Performance, id=performance_id)
    
    if request.method == 'POST':
        form = PerformanceForm(request.POST, instance=performance)
        if form.is_valid():
            form.save()
            messages.success(request, f'绩效考核 {performance.performance_number} 更新成功！')
            return redirect('personnel_pages:performance_detail', performance_id=performance.id)
    else:
        form = PerformanceForm(instance=performance)
    
    context = _context(
        f"编辑绩效考核 - {performance.performance_number}",
        "✏️",
        f"编辑绩效考核 {performance.performance_number}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'performance': performance,
        'is_create': False,
    })
    return render(request, "personnel_management/performance_form.html", context)


@login_required
def contract_create(request):
    """新增劳动合同"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.contract.manage', permission_codes):
        messages.error(request, '您没有权限创建劳动合同')
        return redirect('personnel_pages:contract_management')
    
    if request.method == 'POST':
        form = LaborContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            # 自动生成合同编号
            if not contract.contract_number:
                current_year = timezone.now().year
                max_contract = LaborContract.objects.filter(
                    contract_number__startswith=f'CONTRACT-{current_year}-'
                ).aggregate(max_num=Max('contract_number'))['max_num']
                if max_contract:
                    try:
                        seq = int(max_contract.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                contract.contract_number = f'CONTRACT-{current_year}-{seq:04d}'
            contract.created_by = request.user
            contract.status = 'active'
            contract.save()
            messages.success(request, f'劳动合同 {contract.contract_number} 创建成功！')
            return redirect('personnel_pages:contract_detail', contract_id=contract.id)
    else:
        form = LaborContractForm()
    
    context = _context(
        "新增劳动合同",
        "➕",
        "创建新的劳动合同",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/contract_form.html", context)


@login_required
def contract_update(request, contract_id):
    """编辑劳动合同"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.contract.manage', permission_codes):
        messages.error(request, '您没有权限编辑劳动合同')
        return redirect('personnel_pages:contract_detail', contract_id=contract_id)
    
    contract = get_object_or_404(LaborContract, id=contract_id)
    
    if request.method == 'POST':
        form = LaborContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, f'劳动合同 {contract.contract_number} 更新成功！')
            return redirect('personnel_pages:contract_detail', contract_id=contract.id)
    else:
        form = LaborContractForm(instance=contract)
    
    context = _context(
        f"编辑劳动合同 - {contract.contract_number}",
        "✏️",
        f"编辑劳动合同 {contract.contract_number}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'contract': contract,
        'is_create': False,
    })
    return render(request, "personnel_management/contract_form.html", context)


@login_required
def attendance_detail(request, attendance_id):
    """考勤记录详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.attendance.view', permission_codes):
        messages.error(request, '您没有权限查看考勤详情')
        return redirect('personnel_pages:attendance_management')
    
    attendance = get_object_or_404(
        Attendance.objects.select_related('employee'),
        id=attendance_id
    )
    
    context = _context(
        "考勤记录详情",
        "⏰",
        f"查看考勤记录详情：{attendance.employee.name} - {attendance.attendance_date}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'attendance': attendance,
    })
    return render(request, "personnel_management/attendance_detail.html", context)


@login_required
def attendance_create(request):
    """新增考勤记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.attendance.manage', permission_codes):
        messages.error(request, '您没有权限创建考勤记录')
        return redirect('personnel_pages:attendance_management')
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            # 计算工作时长
            if attendance.check_in_time and attendance.check_out_time:
                from datetime import datetime, timedelta
                check_in = datetime.combine(attendance.attendance_date, attendance.check_in_time)
                check_out = datetime.combine(attendance.attendance_date, attendance.check_out_time)
                if check_out < check_in:
                    check_out += timedelta(days=1)
                work_duration = check_out - check_in
                attendance.work_hours = work_duration.total_seconds() / 3600
            attendance.save()
            messages.success(request, f'考勤记录创建成功！')
            return redirect('personnel_pages:attendance_detail', attendance_id=attendance.id)
    else:
        form = AttendanceForm()
        # 默认今天
        form.fields['attendance_date'].initial = timezone.now().date()
    
    context = _context(
        "新增考勤记录",
        "➕",
        "创建新的考勤记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
    })
    return render(request, "personnel_management/attendance_form.html", context)


@login_required
def salary_create(request):
    """新增薪资记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.salary.manage', permission_codes):
        messages.error(request, '您没有权限创建薪资记录')
        return redirect('personnel_pages:salary_management')
    
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            salary = form.save(commit=False)
            # 计算总收入和实发金额
            salary.total_income = salary.base_salary + salary.performance_bonus + salary.overtime_pay + salary.allowance
            salary.total_deduction = salary.social_insurance + salary.housing_fund + salary.tax + salary.other_deduction
            salary.net_salary = salary.total_income - salary.total_deduction
            salary.created_by = request.user
            salary.save()
            messages.success(request, f'薪资记录创建成功！')
            return redirect('personnel_pages:salary_management')
    else:
        form = SalaryForm()
        # 默认当前月份
        today = timezone.now().date()
        form.fields['salary_month'].initial = today.replace(day=1)
    
    context = _context(
        "新增薪资记录",
        "➕",
        "创建新的薪资记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
    })
    return render(request, "personnel_management/salary_form.html", context)


@login_required
def salary_detail(request, salary_id):
    """薪资记录详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.salary.view', permission_codes):
        messages.error(request, '您没有权限查看薪资详情')
        return redirect('personnel_pages:salary_management')
    
    salary = get_object_or_404(
        Salary.objects.select_related('employee', 'created_by'),
        id=salary_id
    )
    
    context = _context(
        "薪资记录详情",
        "💵",
        f"查看薪资记录详情：{salary.employee.name} - {salary.salary_month.strftime('%Y年%m月')}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'salary': salary,
    })
    return render(request, "personnel_management/salary_detail.html", context)


@login_required
def salary_update(request, salary_id):
    """编辑薪资记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.salary.manage', permission_codes):
        messages.error(request, '您没有权限编辑薪资记录')
        return redirect('personnel_pages:salary_detail', salary_id=salary_id)
    
    salary = get_object_or_404(Salary, id=salary_id)
    
    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            salary = form.save(commit=False)
            # 重新计算总收入和实发金额
            salary.total_income = salary.base_salary + salary.performance_bonus + salary.overtime_pay + salary.allowance
            salary.total_deduction = salary.social_insurance + salary.housing_fund + salary.tax + salary.other_deduction
            salary.net_salary = salary.total_income - salary.total_deduction
            salary.save()
            messages.success(request, f'薪资记录更新成功！')
            return redirect('personnel_pages:salary_detail', salary_id=salary.id)
    else:
        form = SalaryForm(instance=salary)
    
    context = _context(
        f"编辑薪资记录",
        "✏️",
        f"编辑薪资记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'salary': salary,
    })
    return render(request, "personnel_management/salary_form.html", context)


@login_required
def performance_management(request):
    """绩效考核"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.performance.view', permission_codes):
        messages.error(request, '您没有权限访问绩效考核')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    current_year = today.year
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    period_type = request.GET.get('period_type', '')
    status = request.GET.get('status', '')
    period_year = request.GET.get('period_year', str(current_year))
    
    # 获取绩效列表
    try:
        performances = Performance.objects.select_related('employee', 'reviewer', 'created_by').order_by('-period_year', '-created_time')
        
        # 应用筛选条件
        if search:
            performances = performances.filter(
                Q(performance_number__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )
        if period_type:
            performances = performances.filter(period_type=period_type)
        if status:
            performances = performances.filter(status=status)
        if period_year:
            performances = performances.filter(period_year=int(period_year))
        
        # 分页
        paginator = Paginator(performances, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取绩效列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_performances = Performance.objects.filter(period_year=current_year).count()
        pending_performances = Performance.objects.filter(
            period_year=current_year,
            status__in=['draft', 'self_assessment', 'manager_review']
        ).count()
        completed_performances = Performance.objects.filter(
            period_year=current_year,
            status='completed'
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "绩效考核",
        "📊",
        "管理绩效考核",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'performances': page_obj.object_list if page_obj else [],
        'period_type_choices': Performance.PERIOD_CHOICES,
        'status_choices': Performance.STATUS_CHOICES,
        'current_search': search,
        'current_period_type': period_type,
        'current_status': status,
        'current_period_year': period_year,
        'years': range(current_year - 2, current_year + 2),
    })
    return render(request, "personnel_management/performance_list.html", context)


@login_required
def performance_detail(request, performance_id):
    """绩效详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.performance.view', permission_codes):
        messages.error(request, '您没有权限查看绩效详情')
        return redirect('personnel_pages:performance_management')
    
    performance = get_object_or_404(Performance.objects.select_related('employee', 'reviewer', 'created_by'), id=performance_id)
    
    context = _context(
        f"绩效详情 - {performance.performance_number}",
        "📊",
        f"查看绩效考核 {performance.performance_number} 的详细信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'performance': performance,
    })
    return render(request, "personnel_management/performance_detail.html", context)


@login_required
def salary_management(request):
    """薪资管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.salary.view', permission_codes):
        messages.error(request, '您没有权限访问薪资管理')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    salary_month = request.GET.get('salary_month', today.strftime('%Y-%m'))
    employee_id = request.GET.get('employee_id', '')
    
    # 获取薪资列表
    try:
        salaries = Salary.objects.select_related('employee', 'created_by').order_by('-salary_month', '-created_time')
        
        # 应用筛选条件
        if search:
            salaries = salaries.filter(
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )
        if salary_month:
            year, month = salary_month.split('-')
            salaries = salaries.filter(
                salary_month__year=int(year),
                salary_month__month=int(month)
            )
        if employee_id:
            salaries = salaries.filter(employee_id=int(employee_id))
        
        # 分页
        paginator = Paginator(salaries, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取薪资列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        if salary_month:
            year, month = salary_month.split('-')
            month_salaries = Salary.objects.filter(
                salary_month__year=int(year),
                salary_month__month=int(month)
            )
        else:
            month_salaries = Salary.objects.filter(
                salary_month__year=today.year,
                salary_month__month=today.month
            )
        
        total_count = month_salaries.count()
        total_net = month_salaries.aggregate(total=Sum('net_salary'))['total'] or Decimal('0')
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "薪资管理",
        "💰",
        "管理薪资记录",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'salaries': page_obj.object_list if page_obj else [],
        'current_search': search,
        'current_salary_month': salary_month,
        'current_employee_id': employee_id,
    })
    return render(request, "personnel_management/salary_list.html", context)


@login_required
def contract_management(request):
    """劳动合同管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.contract.view', permission_codes):
        messages.error(request, '您没有权限访问劳动合同管理')
        return redirect('personnel_pages:personnel_home')
    
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    contract_type = request.GET.get('contract_type', '')
    status = request.GET.get('status', '')
    
    # 获取合同列表
    try:
        contracts = LaborContract.objects.select_related('employee', 'created_by').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            contracts = contracts.filter(
                Q(contract_number__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )
        if contract_type:
            contracts = contracts.filter(contract_type=contract_type)
        if status:
            contracts = contracts.filter(status=status)
        
        # 分页
        paginator = Paginator(contracts, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取合同列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_contracts = LaborContract.objects.count()
        active_contracts = LaborContract.objects.filter(status='active').count()
        expiring_soon = LaborContract.objects.filter(
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=90)
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "劳动合同管理",
        "📄",
        "管理劳动合同",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'contracts': page_obj.object_list if page_obj else [],
        'contract_type_choices': LaborContract.TYPE_CHOICES,
        'status_choices': LaborContract.STATUS_CHOICES,
        'current_search': search,
        'current_contract_type': contract_type,
        'current_status': status,
    })
    return render(request, "personnel_management/contract_list.html", context)


@login_required
def contract_detail(request, contract_id):
    """合同详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.contract.view', permission_codes):
        messages.error(request, '您没有权限查看合同详情')
        return redirect('personnel_pages:contract_management')
    
    contract = get_object_or_404(LaborContract.objects.select_related('employee', 'created_by'), id=contract_id)
    
    context = _context(
        f"合同详情 - {contract.contract_number}",
        "📄",
        f"查看劳动合同 {contract.contract_number} 的详细信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'contract': contract,
    })
    return render(request, "personnel_management/contract_detail.html", context)


# ==================== 组织架构管理 ====================

@login_required
def organization_management(request):
    """组织架构管理主页"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.organization.view', permission_codes):
        messages.error(request, '您没有权限访问组织架构管理')
        return redirect('personnel_pages:personnel_home')
    
    context = _context(
        "组织架构管理",
        "🏢",
        "管理企业的组织架构，包括部门管理、职位管理等",
        request=request,
        use_personnel_nav=True
    )
    return render(request, "personnel_management/organization_management.html", context)


@login_required
def department_management(request):
    """部门管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.organization.manage_department', permission_codes):
        messages.error(request, '您没有权限访问部门管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    is_active = request.GET.get('is_active', '')
    parent_id = request.GET.get('parent_id', '')
    
    # 获取部门列表
    try:
        departments = Department.objects.select_related('parent', 'leader').all()
        
        # 应用筛选条件
        if search:
            departments = departments.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        if is_active:
            departments = departments.filter(is_active=(is_active == 'true'))
        if parent_id:
            departments = departments.filter(parent_id=parent_id)
        
        # 排序
        departments = departments.order_by('order', 'name')
        
        # 分页
        paginator = Paginator(departments, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取部门列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_departments = Department.objects.count()
        active_departments = Department.objects.filter(is_active=True).count()
        inactive_departments = Department.objects.filter(is_active=False).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有部门用于下拉筛选
    all_departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = _context(
        "部门管理",
        "🏛️",
        "管理企业的部门结构",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'departments': page_obj.object_list if page_obj else [],
        'all_departments': all_departments,
        'current_search': search,
        'current_is_active': is_active,
        'current_parent_id': parent_id,
    })
    return render(request, "personnel_management/department_management.html", context)


@login_required
def position_management(request):
    """职位管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.organization.manage_position', permission_codes):
        messages.error(request, '您没有权限访问职位管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    department_id = request.GET.get('department_id', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取职位列表
    try:
        positions = Position.objects.select_related('department').all()
        
        # 应用筛选条件
        if search:
            positions = positions.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        if department_id:
            positions = positions.filter(department_id=department_id)
        if is_active:
            positions = positions.filter(is_active=(is_active == 'true'))
        
        # 排序
        positions = positions.order_by('department', 'level', 'name')
        
        # 分页
        paginator = Paginator(positions, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取职位列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_positions = Position.objects.count()
        active_positions = Position.objects.filter(is_active=True).count()
        inactive_positions = Position.objects.filter(is_active=False).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有部门用于下拉筛选
    all_departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = _context(
        "职位管理",
        "💼",
        "管理企业的职位信息",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'positions': page_obj.object_list if page_obj else [],
        'all_departments': all_departments,
        'current_search': search,
        'current_department_id': department_id,
        'current_is_active': is_active,
    })
    return render(request, "personnel_management/position_management.html", context)


@login_required
def org_chart(request):
    """组织架构图"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.organization.view_chart', permission_codes):
        messages.error(request, '您没有权限查看组织架构图')
        return redirect('personnel_pages:personnel_home')
    
    # 获取所有部门（树形结构）
    try:
        departments = Department.objects.filter(is_active=True).select_related('parent', 'leader').order_by('order', 'name')
        
        # 构建部门树
        def build_tree(parent_id=None):
            children = [dept for dept in departments if (dept.parent_id if dept.parent else None) == parent_id]
            result = []
            for dept in children:
                dept_dict = {
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'leader': dept.leader.get_full_name() if dept.leader else '未设置',
                    'employee_count': dept.employees.filter(status='active').count(),
                    'children': build_tree(dept.id)
                }
                result.append(dept_dict)
            return result
        
        department_tree = build_tree()
        
        # 统计信息
        total_departments = departments.count()
        total_employees = Employee.objects.filter(status='active').count()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取组织架构数据失败: %s', str(e))
        department_tree = []
        total_departments = 0
        total_employees = 0
    
    import json
    context = _context(
        "组织架构图",
        "📊",
        "可视化展示企业的组织架构",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'department_tree': json.dumps(department_tree, ensure_ascii=False),
        'total_departments': total_departments,
        'total_employees': total_employees,
    })
    return render(request, "personnel_management/org_chart.html", context)


# ==================== 员工档案管理 ====================

@login_required
def employee_archive_management(request):
    """员工档案管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_archive.view', permission_codes):
        messages.error(request, '您没有权限访问员工档案管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    employee_id = request.GET.get('employee_id', '')
    category = request.GET.get('category', '')
    expiring_soon = request.GET.get('expiring_soon', '')
    
    # 获取档案列表
    try:
        archives = EmployeeArchive.objects.select_related('employee', 'created_by').all()
        
        # 应用筛选条件
        if search:
            archives = archives.filter(
                Q(file_name__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search) |
                Q(description__icontains=search)
            )
        if employee_id:
            archives = archives.filter(employee_id=employee_id)
        if category:
            archives = archives.filter(category=category)
        if expiring_soon == 'true':
            from datetime import timedelta
            today = timezone.now().date()
            future_date = today + timedelta(days=90)
            archives = archives.filter(expiry_date__gte=today, expiry_date__lte=future_date)
        
        # 排序
        archives = archives.order_by('-created_time')
        
        # 分页
        paginator = Paginator(archives, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取档案列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_archives = EmployeeArchive.objects.count()
        expiring_count = EmployeeArchive.objects.filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=timezone.now().date() + timedelta(days=90)
        ).count()
        archived_count = EmployeeArchive.objects.filter(is_archived=True).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有员工用于下拉筛选
    all_employees = Employee.objects.filter(status='active').order_by('name')
    
    context = _context(
        "员工档案管理",
        "📁",
        "管理员工的档案信息，包括档案文件、档案分类等",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    from datetime import timedelta
    today = timezone.now().date()
    next_month = today + timedelta(days=30)
    
    context.update({
        'page_obj': page_obj,
        'archives': page_obj.object_list if page_obj else [],
        'all_employees': all_employees,
        'category_choices': EmployeeArchive.CATEGORY_CHOICES,
        'current_search': search,
        'current_employee_id': employee_id,
        'current_category': category,
        'current_expiring_soon': expiring_soon,
        'today': today,
        'next_month': next_month,
    })
    return render(request, "personnel_management/employee_archive_management.html", context)


@login_required
def employee_archive_create(request):
    """上传员工档案文件"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_archive.create', permission_codes):
        messages.error(request, '您没有权限上传员工档案')
        return redirect('personnel_pages:employee_archive_management')
    
    if request.method == 'POST':
        form = EmployeeArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            archive = form.save(commit=False)
            archive.created_by = request.user
            archive.save()
            messages.success(request, f'员工档案文件上传成功！')
            return redirect('personnel_pages:employee_archive_management')
    else:
        form = EmployeeArchiveForm()
    
    context = _context(
        "上传员工档案",
        "📤",
        "上传员工档案文件",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_archive_form.html", context)


# ==================== 员工异动管理 ====================

@login_required
def employee_movement_management(request):
    """员工异动管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_movement.view', permission_codes):
        messages.error(request, '您没有权限访问员工异动管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    employee_id = request.GET.get('employee_id', '')
    movement_type = request.GET.get('movement_type', '')
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 获取异动列表
    try:
        movements = EmployeeMovement.objects.select_related(
            'employee', 'old_department', 'new_department', 
            'approver', 'created_by'
        ).all()
        
        # 应用筛选条件
        if search:
            movements = movements.filter(
                Q(movement_number__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(employee__employee_number__icontains=search) |
                Q(reason__icontains=search)
            )
        if employee_id:
            movements = movements.filter(employee_id=employee_id)
        if movement_type:
            movements = movements.filter(movement_type=movement_type)
        if status:
            movements = movements.filter(status=status)
        if start_date:
            movements = movements.filter(movement_date__gte=start_date)
        if end_date:
            movements = movements.filter(movement_date__lte=end_date)
        
        # 排序
        movements = movements.order_by('-movement_date', '-created_time')
        
        # 分页
        paginator = Paginator(movements, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取异动列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_movements = EmployeeMovement.objects.count()
        pending_movements = EmployeeMovement.objects.filter(status='pending').count()
        this_month_movements = EmployeeMovement.objects.filter(
            movement_date__year=timezone.now().year,
            movement_date__month=timezone.now().month
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有员工用于下拉筛选
    all_employees = Employee.objects.filter(status__in=['active', 'suspended']).order_by('name')
    
    context = _context(
        "员工异动管理",
        "🔄",
        "管理员工的异动记录，包括调岗、晋升、降职等",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'movements': page_obj.object_list if page_obj else [],
        'all_employees': all_employees,
        'movement_type_choices': EmployeeMovement.MOVEMENT_TYPE_CHOICES,
        'status_choices': EmployeeMovement.STATUS_CHOICES,
        'current_search': search,
        'current_employee_id': employee_id,
        'current_movement_type': movement_type,
        'current_status': status,
        'current_start_date': start_date,
        'current_end_date': end_date,
    })
    return render(request, "personnel_management/employee_movement_management.html", context)


@login_required
def employee_movement_detail(request, movement_id):
    """员工异动详情"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_movement.view', permission_codes):
        messages.error(request, '您没有权限查看员工异动详情')
        return redirect('personnel_pages:employee_movement_management')
    
    movement = get_object_or_404(
        EmployeeMovement.objects.select_related(
            'employee', 'old_department', 'new_department',
            'approver', 'created_by'
        ),
        id=movement_id
    )
    
    context = _context(
        "员工异动详情",
        "🔄",
        f"查看员工异动记录详情：{movement.movement_number}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'movement': movement,
    })
    return render(request, "personnel_management/employee_movement_detail.html", context)


@login_required
def employee_movement_create(request):
    """创建员工异动"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.movement.create', permission_codes):
        messages.error(request, '您没有权限创建员工异动')
        return redirect('personnel_pages:employee_movement_management')
    
    if request.method == 'POST':
        form = EmployeeMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            # movement_number会在save方法中自动生成
            movement.save()
            messages.success(request, f'员工异动记录创建成功！异动编号：{movement.movement_number}')
            return redirect('personnel_pages:employee_movement_detail', movement_id=movement.id)
    else:
        form = EmployeeMovementForm()
    
    context = _context(
        "创建员工异动",
        "➕",
        "创建新的员工异动记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_movement_form.html", context)


@login_required
def employee_movement_approve(request, movement_id):
    """员工异动审批"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('personnel_management.movement.approve', permission_codes):
        messages.error(request, '您没有权限审批员工异动')
        return redirect('personnel_pages:employee_movement_management')
    
    movement = get_object_or_404(EmployeeMovement, id=movement_id)
    
    if movement.status != 'pending':
        messages.warning(request, '该异动记录已处理，无法再次审批')
        return redirect('personnel_pages:employee_movement_detail', movement_id=movement_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            movement.status = 'approved'
            movement.approver = request.user
            movement.approval_time = timezone.now()
            movement.approval_comment = comment
            
            # 如果异动类型是调岗、晋升、降职等，更新员工信息
            if movement.movement_type in ['transfer', 'promotion', 'demotion', 'reinstatement']:
                if movement.new_department:
                    movement.employee.department = movement.new_department
                if movement.new_position:
                    movement.employee.position = movement.new_position
                if movement.new_salary:
                    # 注意：这里可能需要更复杂的薪资更新逻辑
                    pass
                movement.employee.save()
            
            # 标记为已完成
            if movement.movement_type in ['transfer', 'promotion', 'demotion', 'reinstatement']:
                movement.status = 'completed'
            
            movement.save()
            messages.success(request, f'员工异动 {movement.movement_number} 已批准')
            
        elif action == 'reject':
            movement.status = 'rejected'
            movement.approver = request.user
            movement.approval_time = timezone.now()
            movement.approval_comment = comment
            movement.save()
            messages.success(request, f'员工异动 {movement.movement_number} 已拒绝')
        
        return redirect('personnel_pages:employee_movement_detail', movement_id=movement_id)
    
    # GET 请求，显示审批页面
    context = _context(
        "审批员工异动",
        "✅",
        f"审批员工异动记录：{movement.movement_number}",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'movement': movement,
    })
    return render(request, "personnel_management/employee_movement_approve.html", context)


# ==================== 福利管理 ====================

@login_required
def welfare_management(request):
    """福利管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.welfare.view', permission_codes):
        messages.error(request, '您没有权限访问福利管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    project_id = request.GET.get('project_id', '')
    employee_id = request.GET.get('employee_id', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 获取福利发放列表
    try:
        distributions = WelfareDistribution.objects.select_related(
            'welfare_project', 'employee', 'created_by'
        ).all()
        
        # 应用筛选条件
        if project_id:
            distributions = distributions.filter(welfare_project_id=project_id)
        if employee_id:
            distributions = distributions.filter(employee_id=employee_id)
        if start_date:
            distributions = distributions.filter(distribution_date__gte=start_date)
        if end_date:
            distributions = distributions.filter(distribution_date__lte=end_date)
        
        # 排序
        distributions = distributions.order_by('-distribution_date', '-created_time')
        
        # 分页
        paginator = Paginator(distributions, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取福利发放列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_distributions = WelfareDistribution.objects.count()
        total_projects = WelfareProject.objects.filter(is_active=True).count()
        this_month_distributions = WelfareDistribution.objects.filter(
            distribution_date__year=timezone.now().year,
            distribution_date__month=timezone.now().month
        ).count()
        total_amount = WelfareDistribution.objects.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有福利项目和员工用于下拉筛选
    all_projects = WelfareProject.objects.filter(is_active=True).order_by('name')
    all_employees = Employee.objects.filter(status='active').order_by('name')
    
    context = _context(
        "福利管理",
        "🎁",
        "管理企业的员工福利，包括福利项目、福利发放等",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'distributions': page_obj.object_list if page_obj else [],
        'all_projects': all_projects,
        'all_employees': all_employees,
        'current_project_id': project_id,
        'current_employee_id': employee_id,
        'current_start_date': start_date,
        'current_end_date': end_date,
    })
    return render(request, "personnel_management/welfare_management.html", context)


@login_required
def welfare_distribution_create(request):
    """创建福利发放记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.welfare.create', permission_codes):
        messages.error(request, '您没有权限创建福利发放记录')
        return redirect('personnel_pages:welfare_management')
    
    if request.method == 'POST':
        form = WelfareDistributionForm(request.POST)
        if form.is_valid():
            distribution = form.save(commit=False)
            distribution.created_by = request.user
            distribution.save()
            messages.success(request, f'福利发放记录创建成功！')
            return redirect('personnel_pages:welfare_management')
    else:
        form = WelfareDistributionForm()
        # 默认今天
        form.fields['distribution_date'].initial = timezone.now().date()
    
    context = _context(
        "创建福利发放",
        "➕",
        "创建新的福利发放记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/welfare_distribution_form.html", context)


# ==================== 招聘管理 ====================

@login_required
def recruitment_management(request):
    """招聘管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.recruitment.view', permission_codes):
        messages.error(request, '您没有权限访问招聘管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    department_id = request.GET.get('department_id', '')
    status = request.GET.get('status', '')
    
    # 获取招聘需求列表
    try:
        requirements = RecruitmentRequirement.objects.select_related(
            'department', 'approver', 'created_by'
        ).all()
        
        # 应用筛选条件
        if search:
            requirements = requirements.filter(
                Q(requirement_number__icontains=search) |
                Q(position__icontains=search) |
                Q(department__name__icontains=search)
            )
        if department_id:
            requirements = requirements.filter(department_id=department_id)
        if status:
            requirements = requirements.filter(status=status)
        
        # 排序
        requirements = requirements.order_by('-created_time')
        
        # 分页
        paginator = Paginator(requirements, 30)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取招聘需求列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_requirements = RecruitmentRequirement.objects.count()
        pending_requirements = RecruitmentRequirement.objects.filter(status='pending').count()
        recruiting_requirements = RecruitmentRequirement.objects.filter(status='recruiting').count()
        total_resumes = Resume.objects.count()
        total_interviews = Interview.objects.count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取所有部门用于下拉筛选
    all_departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = _context(
        "招聘管理",
        "📝",
        "管理企业的招聘流程，包括招聘需求、简历管理、面试管理等",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'requirements': page_obj.object_list if page_obj else [],
        'all_departments': all_departments,
        'status_choices': RecruitmentRequirement.STATUS_CHOICES,
        'current_search': search,
        'current_department_id': department_id,
        'current_status': status,
    })
    return render(request, "personnel_management/recruitment_management.html", context)


@login_required
def recruitment_requirement_create(request):
    """创建招聘需求"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.recruitment.create', permission_codes):
        messages.error(request, '您没有权限创建招聘需求')
        return redirect('personnel_pages:recruitment_management')
    
    if request.method == 'POST':
        form = RecruitmentRequirementForm(request.POST)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.created_by = request.user
            # requirement_number会在save方法中自动生成
            requirement.save()
            messages.success(request, f'招聘需求创建成功！需求编号：{requirement.requirement_number}')
            return redirect('personnel_pages:recruitment_management')
    else:
        form = RecruitmentRequirementForm()
        # 默认状态为草稿
        form.fields['status'].initial = 'draft'
    
    context = _context(
        "创建招聘需求",
        "➕",
        "创建新的招聘需求",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/recruitment_requirement_form.html", context)


# ==================== 员工关系管理 ====================

@login_required
def employee_relations_management(request):
    """员工关系管理"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.view', permission_codes):
        messages.error(request, '您没有权限访问员工关系管理')
        return redirect('personnel_pages:personnel_home')
    
    # 获取筛选参数
    relation_type = request.GET.get('relation_type', '')  # communication, care, activity, complaint, suggestion
    
    # 统计信息
    try:
        total_communications = EmployeeCommunication.objects.count()
        total_cares = EmployeeCare.objects.count()
        total_activities = EmployeeActivity.objects.count()
        total_complaints = EmployeeComplaint.objects.filter(status__in=['pending', 'processing']).count()
        total_suggestions = EmployeeSuggestion.objects.filter(status='pending').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取最近的数据
    try:
        recent_communications = EmployeeCommunication.objects.select_related('employee').order_by('-communication_date')[:5]
        recent_cares = EmployeeCare.objects.select_related('employee').order_by('-care_date')[:5]
        recent_activities = EmployeeActivity.objects.order_by('-activity_date')[:5]
        recent_complaints = EmployeeComplaint.objects.select_related('employee').filter(status__in=['pending', 'processing']).order_by('-complaint_date')[:5]
        recent_suggestions = EmployeeSuggestion.objects.select_related('employee').filter(status='pending').order_by('-suggestion_date')[:5]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取最近数据失败: %s', str(e))
        recent_communications = []
        recent_cares = []
        recent_activities = []
        recent_complaints = []
        recent_suggestions = []
    
    context = _context(
        "员工关系管理",
        "🤝",
        "管理员工关系，包括员工沟通、员工关怀、员工活动等",
        summary_cards=summary_cards,
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'recent_communications': recent_communications,
        'recent_cares': recent_cares,
        'recent_activities': recent_activities,
        'recent_complaints': recent_complaints,
        'recent_suggestions': recent_suggestions,
        'current_relation_type': relation_type,
    })
    return render(request, "personnel_management/employee_relations_management.html", context)


@login_required
def employee_communication_create(request):
    """创建员工沟通记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.create', permission_codes):
        messages.error(request, '您没有权限创建员工沟通记录')
        return redirect('personnel_pages:employee_relations_management')
    
    if request.method == 'POST':
        form = EmployeeCommunicationForm(request.POST)
        if form.is_valid():
            communication = form.save(commit=False)
            communication.created_by = request.user
            communication.save()
            messages.success(request, f'员工沟通记录创建成功！')
            return redirect('personnel_pages:employee_relations_management')
    else:
        form = EmployeeCommunicationForm()
        # 默认当前时间
        from datetime import datetime
        form.fields['communication_date'].initial = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    context = _context(
        "创建员工沟通记录",
        "➕",
        "创建新的员工沟通记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_communication_form.html", context)


@login_required
def employee_care_create(request):
    """创建员工关怀记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.create', permission_codes):
        messages.error(request, '您没有权限创建员工关怀记录')
        return redirect('personnel_pages:employee_relations_management')
    
    if request.method == 'POST':
        form = EmployeeCareForm(request.POST)
        if form.is_valid():
            care = form.save(commit=False)
            care.created_by = request.user
            care.save()
            messages.success(request, f'员工关怀记录创建成功！')
            return redirect('personnel_pages:employee_relations_management')
    else:
        form = EmployeeCareForm()
        # 默认今天
        form.fields['care_date'].initial = timezone.now().date()
    
    context = _context(
        "创建员工关怀记录",
        "➕",
        "创建新的员工关怀记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_care_form.html", context)


@login_required
def employee_activity_create(request):
    """创建员工活动"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.create', permission_codes):
        messages.error(request, '您没有权限创建员工活动')
        return redirect('personnel_pages:employee_relations_management')
    
    if request.method == 'POST':
        form = EmployeeActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = request.user
            # activity_number会在save方法中自动生成
            activity.save()
            messages.success(request, f'员工活动创建成功！活动编号：{activity.activity_number}')
            return redirect('personnel_pages:employee_relations_management')
    else:
        form = EmployeeActivityForm()
        # 默认状态为策划中
        form.fields['status'].initial = 'planning'
        # 默认当前时间
        from datetime import datetime
        form.fields['activity_date'].initial = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    context = _context(
        "创建员工活动",
        "➕",
        "创建新的员工活动",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_activity_form.html", context)


@login_required
def employee_complaint_create(request):
    """创建员工投诉"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.create', permission_codes):
        messages.error(request, '您没有权限创建员工投诉')
        return redirect('personnel_pages:employee_relations_management')
    
    if request.method == 'POST':
        form = EmployeeComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            # complaint_number会在save方法中自动生成
            complaint.save()
            messages.success(request, f'员工投诉创建成功！投诉编号：{complaint.complaint_number}')
            return redirect('personnel_pages:employee_relations_management')
    else:
        form = EmployeeComplaintForm()
        # 默认状态为待处理
        form.fields['status'].initial = 'pending'
        # 默认当前时间
        from datetime import datetime
        form.fields['complaint_date'].initial = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    context = _context(
        "创建员工投诉",
        "➕",
        "创建新的员工投诉",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_complaint_form.html", context)


@login_required
def employee_suggestion_create(request):
    """创建员工建议"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.employee_relations.create', permission_codes):
        messages.error(request, '您没有权限创建员工建议')
        return redirect('personnel_pages:employee_relations_management')
    
    if request.method == 'POST':
        form = EmployeeSuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            # suggestion_number会在save方法中自动生成
            suggestion.save()
            messages.success(request, f'员工建议创建成功！建议编号：{suggestion.suggestion_number}')
            return redirect('personnel_pages:employee_relations_management')
    else:
        form = EmployeeSuggestionForm()
        # 默认状态为待处理
        form.fields['status'].initial = 'pending'
        # 默认当前时间
        from datetime import datetime
        form.fields['suggestion_date'].initial = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    context = _context(
        "创建员工建议",
        "➕",
        "创建新的员工建议",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/employee_suggestion_form.html", context)


@login_required
def welfare_project_create(request):
    """创建福利项目"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.welfare.create', permission_codes):
        messages.error(request, '您没有权限创建福利项目')
        return redirect('personnel_pages:welfare_management')
    
    if request.method == 'POST':
        form = WelfareProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'福利项目 "{project.name}" 创建成功！')
            return redirect('personnel_pages:welfare_management')
    else:
        form = WelfareProjectForm()
        # 默认启用
        form.fields['is_active'].initial = True
    
    context = _context(
        "创建福利项目",
        "➕",
        "创建新的福利项目",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/welfare_project_form.html", context)


@login_required
def resume_create(request):
    """创建简历"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.recruitment.create', permission_codes):
        messages.error(request, '您没有权限创建简历')
        return redirect('personnel_pages:recruitment_management')
    
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            # resume_number会在save方法中自动生成
            resume.save()
            messages.success(request, f'简历创建成功！简历编号：{resume.resume_number}')
            return redirect('personnel_pages:recruitment_management')
    else:
        form = ResumeForm()
        # 默认状态为待处理
        form.fields['status'].initial = 'pending'
    
    context = _context(
        "创建简历",
        "➕",
        "创建新的简历",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/resume_form.html", context)


@login_required
def interview_create(request):
    """创建面试记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.recruitment.create', permission_codes):
        messages.error(request, '您没有权限创建面试记录')
        return redirect('personnel_pages:recruitment_management')
    
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            # interview_number会在save方法中自动生成
            interview.save()
            messages.success(request, f'面试记录创建成功！面试编号：{interview.interview_number}')
            return redirect('personnel_pages:recruitment_management')
    else:
        form = InterviewForm()
        # 默认状态为已安排
        form.fields['status'].initial = 'scheduled'
        # 默认当前时间
        from datetime import datetime
        form.fields['interview_date'].initial = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    context = _context(
        "创建面试记录",
        "➕",
        "创建新的面试记录",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "personnel_management/interview_form.html", context)

