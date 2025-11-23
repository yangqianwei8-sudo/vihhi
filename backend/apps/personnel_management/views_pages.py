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
from .models import (
    Employee, Attendance, Leave, Training, TrainingParticipant,
    Performance, Salary, LaborContract,
)
from .forms import (
    EmployeeForm, LeaveForm, TrainingForm, PerformanceForm,
    SalaryForm, LaborContractForm, AttendanceForm
)


def _permission_granted(required_code, user_permissions: set) -> bool:
    """检查权限"""
    if not required_code:
        return True
    if '__all__' in user_permissions:
        return True
    return required_code in user_permissions


def _context(page_title, page_icon, description, summary_cards=None, request=None, use_personnel_nav=False):
    """构建页面上下文"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        if use_personnel_nav:
            context['full_top_nav'] = _build_personnel_top_nav(permission_set)
        else:
            context['full_top_nav'] = []
    else:
        context['full_top_nav'] = []
    
    return context


def _build_personnel_top_nav(permission_set):
    """生成人事管理专用的顶部导航菜单 - 7个子功能横向排列"""
    # 定义人事管理功能模块（从左到右的顺序）
    personnel_modules = [
        {
            'label': '员工档案',
            'url_name': 'personnel_pages:employee_management',
            'permission': 'personnel_management.employee.view',
            'icon': '👤',
        },
        {
            'label': '考勤管理',
            'url_name': 'personnel_pages:attendance_management',
            'permission': 'personnel_management.attendance.view',
            'icon': '⏰',
        },
        {
            'label': '请假管理',
            'url_name': 'personnel_pages:leave_management',
            'permission': 'personnel_management.leave.view',
            'icon': '📅',
        },
        {
            'label': '培训管理',
            'url_name': 'personnel_pages:training_management',
            'permission': 'personnel_management.training.view',
            'icon': '📚',
        },
        {
            'label': '绩效考核',
            'url_name': 'personnel_pages:performance_management',
            'permission': 'personnel_management.performance.view',
            'icon': '📊',
        },
        {
            'label': '薪资管理',
            'url_name': 'personnel_pages:salary_management',
            'permission': 'personnel_management.salary.view',
            'icon': '💰',
        },
        {
            'label': '劳动合同',
            'url_name': 'personnel_pages:contract_management',
            'permission': 'personnel_management.contract.view',
            'icon': '📄',
        },
    ]
    
    # 过滤有权限的模块
    nav_items = []
    for module in personnel_modules:
        if _permission_granted(module['permission'], permission_set):
            try:
                url = reverse(module['url_name'])
            except NoReverseMatch:
                url = '#'
            nav_items.append({
                'label': module['label'],
                'url': url,
                'icon': module.get('icon', ''),
            })
    
    return nav_items


@login_required
def personnel_home(request):
    """人事管理主页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 收集统计数据
    stats_cards = []
    
    try:
        # 员工档案统计
        if _permission_granted('personnel_management.employee.view', permission_codes):
            try:
                total_employees = Employee.objects.filter(status='active').count()
                new_employees_this_month = Employee.objects.filter(
                    entry_date__gte=this_month_start
                ).count()
                
                stats_cards.append({
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
                
                stats_cards.append({
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
                
                stats_cards.append({
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
                
                stats_cards.append({
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
                
                stats_cards.append({
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
                
                stats_cards.append({
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
                    end_date__gte=today,
                    end_date__lte=today + timedelta(days=90)
                ).count()
                
                stats_cards.append({
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
    
    context = _context(
        "人事管理",
        "👥",
        "企业人事管理平台",
        summary_cards=stats_cards,
        request=request,
        use_personnel_nav=True
    )
    return render(request, "personnel_management/home.html", context)


@login_required
def employee_management(request):
    """员工档案管理"""
    permission_codes = get_user_permission_codes(request.user)
    
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
        
        summary_cards = [
            {"label": "员工总数", "value": total_employees, "hint": "系统中维护的员工总数"},
            {"label": "在职员工", "value": active_employees, "hint": "状态为在职的员工数量"},
            {"label": "已离职", "value": resigned_employees, "hint": "状态为离职的员工数量"},
        ]
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
    employee = get_object_or_404(Employee.objects.select_related('department', 'user'), id=employee_id)
    
    context = _context(
        f"员工详情 - {employee.name}",
        "👤",
        f"查看员工 {employee.name} 的详细信息",
        request=request,
        use_personnel_nav=True
    )
    context.update({
        'employee': employee,
    })
    return render(request, "personnel_management/employee_detail.html", context)


@login_required
def attendance_management(request):
    """考勤管理"""
    permission_codes = get_user_permission_codes(request.user)
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
        
        summary_cards = [
            {"label": "今日打卡", "value": today_attendances, "hint": "今日打卡记录数"},
            {"label": "今日迟到", "value": today_late, "hint": "今日迟到人数"},
            {"label": "今日缺勤", "value": today_absent, "hint": "今日缺勤人数"},
        ]
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
        
        summary_cards = [
            {"label": "请假总数", "value": total_leaves, "hint": "系统中维护的请假申请总数"},
            {"label": "待审批", "value": pending_leaves, "hint": "状态为待审批的请假数量"},
            {"label": "已批准", "value": approved_leaves, "hint": "状态为已批准的请假数量"},
        ]
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
    if not _permission_granted('personnel_management.leave.apply', permission_codes):
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
        
        summary_cards = [
            {"label": "培训总数", "value": total_trainings, "hint": "系统中维护的培训总数"},
            {"label": "进行中", "value": ongoing_trainings, "hint": "状态为进行中的培训数量"},
            {"label": "已完成", "value": completed_trainings, "hint": "状态为已完成的培训数量"},
        ]
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
            return redirect('personnel_pages:attendance_management')
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
def salary_update(request, salary_id):
    """编辑薪资记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('personnel_management.salary.manage', permission_codes):
        messages.error(request, '您没有权限编辑薪资记录')
        return redirect('personnel_pages:salary_management')
    
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
            return redirect('personnel_pages:salary_management')
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
        
        summary_cards = [
            {"label": "本年度考核", "value": total_performances, "hint": f"{current_year}年绩效考核总数"},
            {"label": "待完成", "value": pending_performances, "hint": "状态为待完成的考核数量"},
            {"label": "已完成", "value": completed_performances, "hint": "状态为已完成的考核数量"},
        ]
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
        
        summary_cards = [
            {"label": "记录数", "value": total_count, "hint": "薪资记录数量"},
            {"label": "实发总额", "value": f"¥{total_net:,.2f}", "hint": "实发薪资总额"},
        ]
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
            end_date__gte=today,
            end_date__lte=today + timedelta(days=90)
        ).count()
        
        summary_cards = [
            {"label": "合同总数", "value": total_contracts, "hint": "系统中维护的合同总数"},
            {"label": "生效中", "value": active_contracts, "hint": "状态为生效中的合同数量"},
            {"label": "即将到期", "value": expiring_soon, "hint": "90天内到期的合同数量"},
        ]
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

