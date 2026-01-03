import csv
import io
import json
import datetime
import os
from decimal import Decimal, InvalidOperation
from datetime import timedelta
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.forms import inlineformset_factory
from django.conf import settings
from openpyxl import Workbook
from django.utils.html import format_html, format_html_join
from django.core.paginator import Paginator

from .models import (
    Project,
    ProjectTeam,
    ProjectTeamChangeLog,
    ProjectTeamNotification,
    ProjectTask,
    ProjectMilestone,
    ProjectDocument,
    ProjectArchive,
    ProjectDrawingSubmission,
    ProjectDrawingFile,
    ProjectDrawingReview,
    ProjectStartNotice,
    ProjectFlowLog,
    ProjectDesignReply,
    ProjectMeetingRecord,
    ServiceType,
    ServiceProfession,
    BusinessType,
    PreOptimizationMaterial,
)
from .serializers import ProjectSerializer, ProjectCreateSerializer

from backend.apps.system_management.models import User, Department
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _build_full_top_nav, _build_unified_sidebar_nav
# calculate_output_value 改为延迟导入，避免在数据库表不存在时导致模块加载失败


logger = logging.getLogger(__name__)
ROLE_LABELS = dict(ProjectTeam.ROLE_CHOICES)
UNIT_LABELS = dict(ProjectTeam.UNIT_CHOICES)

ROLE_META = {
    'project_manager': {'unit': 'management', 'label': ROLE_LABELS.get('project_manager'), 'per_profession': False, 'multiple': False, 'is_external': False},
    'business_manager': {'unit': 'business', 'label': ROLE_LABELS.get('business_manager'), 'per_profession': False, 'multiple': False, 'is_external': False},
    'professional_leader': {'unit': 'internal_tech', 'label': ROLE_LABELS.get('professional_leader'), 'per_profession': True, 'multiple': False, 'is_external': False},
    'engineer': {'unit': 'internal_tech', 'label': ROLE_LABELS.get('engineer'), 'per_profession': True, 'multiple': True, 'is_external': False},
    'technical_assistant': {'unit': 'internal_tech', 'label': ROLE_LABELS.get('technical_assistant'), 'per_profession': False, 'multiple': True, 'is_external': False},
    'external_leader': {'unit': 'external_tech', 'label': ROLE_LABELS.get('external_leader'), 'per_profession': True, 'multiple': False, 'is_external': True},
    'external_engineer': {'unit': 'external_tech', 'label': ROLE_LABELS.get('external_engineer'), 'per_profession': True, 'multiple': True, 'is_external': True},
    'cost_reviewer_civil': {'unit': 'internal_cost', 'label': ROLE_LABELS.get('cost_reviewer_civil'), 'per_profession': False, 'multiple': True, 'is_external': False},
    'cost_reviewer_installation': {'unit': 'internal_cost', 'label': ROLE_LABELS.get('cost_reviewer_installation'), 'per_profession': False, 'multiple': True, 'is_external': False},
    'cost_engineer_civil': {'unit': 'internal_cost', 'label': ROLE_LABELS.get('cost_engineer_civil'), 'per_profession': False, 'multiple': True, 'is_external': False},
    'cost_engineer_installation': {'unit': 'internal_cost', 'label': ROLE_LABELS.get('cost_engineer_installation'), 'per_profession': False, 'multiple': True, 'is_external': False},
    'external_cost_reviewer_civil': {'unit': 'external_cost', 'label': ROLE_LABELS.get('external_cost_reviewer_civil'), 'per_profession': False, 'multiple': True, 'is_external': True},
    'external_cost_reviewer_installation': {'unit': 'external_cost', 'label': ROLE_LABELS.get('external_cost_reviewer_installation'), 'per_profession': False, 'multiple': True, 'is_external': True},
    'external_cost_engineer_civil': {'unit': 'external_cost', 'label': ROLE_LABELS.get('external_cost_engineer_civil'), 'per_profession': False, 'multiple': True, 'is_external': True},
    'external_cost_engineer_installation': {'unit': 'external_cost', 'label': ROLE_LABELS.get('external_cost_engineer_installation'), 'per_profession': False, 'multiple': True, 'is_external': True},
}

PROFESSION_KEYWORDS = {
    'structure': ['结构'],
    'architecture': ['建筑'],
    'electrical': ['电气'],
    'water_supply_drainage': ['给排水', '排水', '给水'],
    'hvac': ['暖通', '空调'],
    'curtain_wall': ['幕墙'],
    'doors_windows_railings': ['门窗栏杆'],
    'landscape': ['总坪景观'],
    'construction': ['构造'],
    'energy_saving': ['节能'],
    'basement_reduce_area': ['地库'],
    'basement_add_parking': ['地库'],
    'parking_efficiency': ['停车效率'],
    'municipal_road': ['市政道路'],
}

# 生产管理左侧导航菜单结构（分组格式）
PRODUCTION_MANAGEMENT_SIDEBAR_MENU = [
    {
        'id': 'production_home',
        'label': '生产管理首页',
        'icon': '🏠',
        'url_name': 'production_pages:production_management_home',
        'permission': 'production_management.view_all',
    },
    {
        'id': 'project_management',
        'label': '生产启动',
        'icon': '🏗️',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'project_list',
                'label': '项目启动列表',
                'icon': '📋',
                'url_name': 'production_pages:project_list',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'project_create',
                'label': '新建生产启动',
                'icon': '➕',
                'url_name': 'production_pages:project_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'consultation_opinion',
        'label': '咨询意见书',
        'icon': '📋',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'get_preliminary_reply',
                'label': '获取初步回复',
                'url_name': 'production_pages:preliminary_reply_list',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'ai_advisor',
                'label': 'AI设计优化顾问',
                'url_name': 'production_pages:ai_advisor',
                'permission': 'production_management.view_all',
            },
        ],
    },
    {
        'id': 'tripartite_communication',
        'label': '三方沟通成果',
        'icon': '🤝',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'tripartite_meeting_minutes',
                'label': '三方会议纪要',
                'url_name': 'production_pages:tripartite_meeting_minutes',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'create_tripartite_communication',
                'label': '创建三方沟通成果',
                'url_name': 'production_pages:tripartite_communication_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'drawing_review_opinion',
        'label': '核图意见书',
        'icon': '✅',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'on_site_tracking_revision',
                'label': '驻场跟踪改图',
                'url_name': 'production_pages:on_site_tracking_revision',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'get_revision_drawings',
                'label': '获取返图',
                'url_name': 'production_pages:revision_drawings_list',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'create_drawing_review_opinion',
                'label': '创建核图意见书',
                'url_name': 'production_pages:drawing_review_opinion_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'weekly_report',
        'label': '每周快报',
        'icon': '📊',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'get_stage_drawings',
                'label': '获取阶段图纸',
                'url_name': 'production_pages:stage_drawings_list',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'create_weekly_report',
                'label': '创建每周快报',
                'url_name': 'production_pages:weekly_report_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'process_optimization_report',
        'label': '过程优化报告',
        'icon': '📈',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'get_process_drawings',
                'label': '获取过程图纸',
                'url_name': 'production_pages:process_drawings_list',
                'permission': 'production_management.view_all',
            },
            {
                'id': 'create_process_optimization_report',
                'label': '创建过程优化报告',
                'url_name': 'production_pages:process_optimization_report_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'reporting_files',
        'label': '汇报文件',
        'icon': '📄',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'create_interim_report',
                'label': '创建中间汇报文件',
                'url_name': 'production_pages:interim_report_create',
                'permission': 'production_management.create',
            },
            {
                'id': 'create_final_report',
                'label': '创建最终汇报文件',
                'url_name': 'production_pages:final_report_create',
                'permission': 'production_management.create',
            },
        ],
    },
    {
        'id': 'optimization_materials',
        'label': '优化前后资料',
        'icon': '📦',
        'permission': 'production_management.view_assigned',  # 使用view_assigned，有view_all的用户也能看到（_permission_granted会自动处理）
        'children': [
            {
                'id': 'pre_optimization_disc_application',
                'label': '优化前刻盘申请',
                'url_name': 'production_pages:pre_optimization_disc_application',
                'permission': 'production_management.create',
            },
            {
                'id': 'pre_optimization_materials',
                'label': '优化前资料',
                'url_name': 'production_pages:pre_optimization_materials',
                'permission': 'production_management.view_assigned',  # 使用view_assigned，有view_all的用户也能看到
            },
            {
                'id': 'post_optimization_disc_application',
                'label': '优化后刻盘申请',
                'url_name': 'production_pages:post_optimization_disc_application',
                'permission': 'production_management.create',
            },
            {
                'id': 'post_optimization_materials',
                'label': '优化后资料',
                'url_name': 'production_pages:post_optimization_materials',
                'permission': 'production_management.view_assigned',  # 使用view_assigned，有view_all的用户也能看到
            },
        ],
    },
    {
        'id': 'service_result_confirmation',
        'label': '服务成果确认',
        'icon': '✔️',
        'permission': 'production_management.view_all',
        'children': [
            {
                'id': 'create_result_confirmation',
                'label': '创建成果确认函',
                'url_name': 'production_pages:result_confirmation_create',
                'permission': 'production_management.create',
            },
        ],
    },
]

# 保留原有的导航项定义（用于兼容）
PRODUCTION_MANAGEMENT_NAV_ITEMS = [
    {
        'id': 'project_list',
        'label': '项目总览',
        'url_name': 'production_pages:project_list',
        'permissions': ('production_management.view_all', 'production_management.view_assigned'),
    },
    {
        'id': 'project_tasks',
        'label': '任务工作台',
        'url_name': 'production_pages:project_task_dashboard',
        'permissions': ('production_management.view_assigned',),
    },
    {
        'id': 'project_create',
        'label': '新建生产启动',
        'url_name': 'production_pages:project_create',
        'permissions': ('production_management.create',),
    },
    {
        'id': 'project_import_admin',
        'label': '批量导入',
        'url_name': 'production_pages:project_import_admin',
        'permissions': (),  # 权限在视图中通过系统管理员判断
        'require_admin': True,
    },
]

PROJECT_FLOW_ACTIONS = {
    'mark_documents_uploaded': {
        'label': '上传优化前资料',
        'from': ['pending_documents'],
        'to': 'precheck',
        'payload_timestamp_key': 'documents_uploaded_at',
    },
    'precheck_pass': {
        'label': '预审通过',
        'from': ['precheck'],
        'to': 'start_notice',
        'payload_timestamp_key': 'precheck_passed_at',
    },
    'precheck_fail': {
        'label': '预审退回',
        'from': ['precheck'],
        'to': 'pending_documents',
        'payload_timestamp_key': 'precheck_failed_at',
    },
    'publish_start_notice': {
        'label': '发布开工通知',
        'from': ['start_notice'],
        'to': 'opinions',
        'payload_timestamp_key': 'start_notice_published_at',
        'deadline_hours': 48,
    },
    'finish_opinions': {
        'label': '意见编制完成',
        'from': ['opinions'],
        'to': 'internal_review',
        'payload_timestamp_key': 'opinions_completed_at',
    },
    'complete_internal_review': {
        'label': '内部审核完成',
        'from': ['internal_review'],
        'to': 'ready_to_push',
        'payload_timestamp_key': 'internal_review_completed_at',
    },
    'push_report': {
        'label': '推送咨询意见书',
        'from': ['ready_to_push'],
        'to': 'pushed',
        'payload_timestamp_key': 'report_pushed_at',
    },
}

PROJECT_TASK_DEFINITIONS = {
    'project_complete_info': {
        'title': '完善项目信息',
        'description': '请完善项目的客户信息、设计方信息以及其他详细资料，确保项目信息完整准确。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 24,
    },
    'configure_team': {
        'title': '配置项目团队',
        'description': '请为项目配置各专业的负责人、工程师等团队成员，确保团队结构完整。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 48,
    },
    'client_upload_pre_docs': {
        'title': '上传优化前资料',
        'description': '请上传图纸、计算书、模型、任务书等优化前资料，便于我方进行预审。',
        'assigned_role': 'client_lead',
        'target_unit': 'client_side',
        'deadline_hours': 24,
    },
    'client_resubmit_pre_docs': {
        'title': '补充上传优化前资料',
        'description': '预审未通过，请根据退回意见重新整理并上传资料。',
        'assigned_role': 'client_lead',
        'target_unit': 'client_side',
        'deadline_hours': 24,
    },
    'internal_precheck_docs': {
        'title': '完成资料预审',
        'description': '请组织团队对甲方提交的资料进行完整性与深度预审，并在系统中记录结果。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 12,
    },
    'client_issue_start_notice': {
        'title': '发布开工通知',
        'description': '资料预审通过，请在系统内发布《开工通知》，以启动48小时生产倒计时。',
        'assigned_role': 'client_lead',
        'target_unit': 'client_side',
        'deadline_hours': 24,
    },
    'internal_compile_opinions': {
        'title': '编制咨询意见',
        'description': '请组织各专业工程师在48小时内完成咨询意见填报与节省测算。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 48,
    },
    'internal_review_opinions': {
        'title': '完成内部审核',
        'description': '请按计划组织专业负责人与项目经理完成意见的内部审核与签发。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 12,
    },
    'push_report_to_client': {
        'title': '推送咨询意见书',
        'description': '审核通过后，请及时推送咨询意见书至甲方与设计方负责人。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 6,
    },
    'design_reply_opinions': {
        'title': '设计方回复咨询意见',
        'description': '请逐条回复咨询意见，并标记同意/不同意及理由，完成后提交审批。',
        'assigned_role': 'design_lead',
        'target_unit': 'design_side',
        'deadline_hours': 48,
    },
    'client_confirm_meeting': {
        'title': '甲方确认三方会议',
        'description': '请确认三方会议时间安排，并在系统中同步会议需求。',
        'assigned_role': 'client_lead',
        'target_unit': 'client_side',
        'deadline_hours': 24,
    },
    'organize_tripartite_meeting': {
        'title': '组织三方会议',
        'description': '请协调甲方与设计方，安排三方会议并记录沟通结论。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 24,
    },
    'design_upload_revisions': {
        'title': '设计方上传改图成果',
        'description': '请根据会议结论上传修改后的图纸和说明材料。',
        'assigned_role': 'design_lead',
        'target_unit': 'design_side',
        'deadline_hours': 48,
    },
    'internal_verify_revisions': {
        'title': '我方核图确认',
        'description': '请逐项核对设计方改图结果，并标记核图意见。',
        'assigned_role': 'project_manager',
        'target_unit': 'management',
        'deadline_hours': 24,
    },
    'client_confirm_outcome': {
        'title': '甲方确认优化成果',
        'description': '请确认优化成果及核图结论，完成后系统将进入结算归档。',
        'assigned_role': 'client_lead',
        'target_unit': 'client_side',
        'deadline_hours': 24,
    },
}


FLOW_TASK_AUTOMATIONS = {
    'publish_start_notice': {
        'complete': ['client_issue_start_notice'],
        'create': ['internal_compile_opinions'],
    },
    'finish_opinions': {
        'complete': ['internal_compile_opinions'],
        'create': ['internal_review_opinions'],
    },
    'complete_internal_review': {
        'complete': ['internal_review_opinions'],
        'create': ['push_report_to_client'],
    },
    'push_report': {
        'complete': ['push_report_to_client'],
        'create': ['design_reply_opinions', 'client_confirm_meeting'],
    },
}


TASK_COMPLETION_FOLLOWUPS = {
    'design_reply_opinions': ['organize_tripartite_meeting'],
    'client_confirm_meeting': [],
    'organize_tripartite_meeting': ['design_upload_revisions'],
    'design_upload_revisions': ['internal_verify_revisions'],
    'internal_verify_revisions': ['client_confirm_outcome'],
}

SERVICE_TYPE_DESCRIPTIONS = {
    'result_optimization': '专注于成果经济性和工程价值的优化提升',
    'process_optimization': '优化设计流程，实现多专业协同的过程控制',
    'detailed_review': '针对图纸进行全面细致的审查与问题闭环',
    'full_process_consulting': '覆盖方案至施工全生命周期的专业咨询',
}

TIMELINE_STAGE_PRESETS = {
    "result_optimization": [
        "优化前图纸",
        "咨询意见书",
        "三方沟通成果",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "detailed_review": [
        "优化前图纸",
        "咨询意见书",
        "三方沟通成果",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "process_optimization": [
        "优化前图纸",
        "过程优化报告",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "full_process_consulting": [
        "咨询意见周报",
        "过程咨询报告",
        "核图意见书",
        "完工确认函",
    ],
}

DEFAULT_TIMELINE_STAGES = ["立项", "设计", "执行", "收尾"]

SERVICE_TIMELINE_TEMPLATES = {
    "result_optimization": [
        "优化前图纸",
        "咨询意见书",
        "三方沟通成果",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "detailed_review": [
        "优化前图纸",
        "咨询意见书",
        "三方沟通成果",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "process_optimization": [
        "优化前图纸",
        "过程优化报告",
        "核图意见书",
        "优化后图纸",
        "完工确认函",
    ],
    "full_process_consulting": [
        "咨询意见周报",
        "过程咨询报告",
        "核图意见书",
        "完工确认函",
    ],
}


def build_project_create_context(form_data=None):
    form_dict = {}
    if form_data:
        # QueryDict -> dict
        try:
            form_dict = form_data.dict()
        except AttributeError:
            form_dict = dict(form_data)

    return {
        'current_year': datetime.datetime.now().year,
        'today': datetime.date.today().isoformat(),
        'form_data': form_dict,
        'departments': Department.objects.filter(is_active=True).order_by('order', 'id'),
        'users': User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
    }


def build_project_edit_context(project, permission_set, form_data=None, user=None):
    if form_data is not None and hasattr(form_data, 'dict'):
        try:
            form_dict = form_data.dict()
        except Exception:
            form_dict = dict(form_data)
    else:
        form_dict = {}

    def _get_value(key, default=''):
        if form_dict:
            return form_dict.get(key, default) if form_dict.get(key, default) is not None else default
        return default

    initial_values = {
        'name': _get_value('name', project.name),
    }

    context = {
        'project': project,
        'initial_values': initial_values,
        'read_only': _is_project_readonly(permission_set),
        'departments': Department.objects.filter(is_active=True).order_by('order', 'id'),
        'users': User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
    }
    return _with_nav(context, permission_set, 'project_list', user)


def _has_permission(permission_set, *codes):
    if '__all__' in permission_set:
        return True
    return any(code in permission_set for code in codes)


def _has_global_project_view(permission_set, user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'user_type', 'internal') != 'internal':
        return False
    return _has_permission(permission_set, 'production_management.view_all')


def _require_permission(request, permission_set, message, *codes):
    if _has_permission(permission_set, *codes):
        return True
    messages.error(request, message)
    return False


def _user_is_project_member(user, project):
    if not user or not project:
        return False
    if project.project_manager_id == user.id:
        return True
    if project.business_manager_id == user.id:
        return True
    if getattr(project, 'created_by_id', None) == user.id:
        return True
    if getattr(project, 'client_leader_id', None) == user.id:
        return True
    if getattr(project, 'design_leader_id', None) == user.id:
        return True
    return project.team_members.filter(user=user).exists()


def _project_visibility_filter(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return Q(pk__in=[])
    return Q(project_manager=user) | Q(business_manager=user) | Q(team_members__user=user) | Q(created_by=user) | Q(client_leader=user) | Q(design_leader=user)


def _filter_projects_for_user(projects, user, permission_set):
    if _has_global_project_view(permission_set, user):
        return projects
    if not user or not getattr(user, 'is_authenticated', False):
        return projects.none()

    scoped_projects = projects.filter(_project_visibility_filter(user))

    if (
        getattr(user, 'user_type', 'internal') == 'internal'
        and user.department_id
        and _has_permission(permission_set, 'production_management.view_all')
    ):
        department_users = User.objects.filter(department_id=user.department_id, is_active=True)
        department_scope = (
            Q(project_manager__in=department_users) |
            Q(team_members__user__in=department_users) |
            Q(business_manager__in=department_users)
        )
        scoped_projects = scoped_projects.union(projects.filter(department_scope))

    return scoped_projects.distinct()


def _task_visible_to_user(task, user, project):
    if task.assigned_to_id == getattr(user, 'id', None):
        return True
    return _user_matches_role(user, project, task.assigned_role)


def _resolve_task_assignee(project, role):
    if not role:
        return None
    if role == 'client_lead':
        return getattr(project, 'client_leader', None)
    if role == 'design_lead':
        return getattr(project, 'design_leader', None)
    if role == 'project_manager':
        return getattr(project, 'project_manager', None)
    if role == 'business_manager':
        return getattr(project, 'business_manager', None)
    member = project.team_members.filter(role=role, is_active=True).select_related('user').first()
    return member.user if member else None


def _reassign_tasks_for_role(project, role, user):
    if not role:
        return
    qs = ProjectTask.objects.filter(project=project, assigned_role=role, status__in=ProjectTask.ACTIVE_STATUSES)
    if user:
        qs.exclude(assigned_to=user).update(assigned_to=user)
    else:
        qs.exclude(assigned_to=None).update(assigned_to=None)


def _ensure_project_task(
    project,
    task_type,
    *,
    title=None,
    description=None,
    due_time=None,
    assigned_to=None,
    assigned_role=None,
    created_by=None,
    metadata=None,
):
    definition = PROJECT_TASK_DEFINITIONS.get(task_type, {})
    assigned_role = assigned_role or definition.get('assigned_role', '')
    assigned_user = assigned_to or _resolve_task_assignee(project, assigned_role)
    target_unit = definition.get('target_unit') or ProjectTeam.ROLE_UNIT_MAP.get(assigned_role, '')

    if not due_time and definition.get('deadline_hours'):
        due_time = timezone.now() + timedelta(hours=definition['deadline_hours'])

    existing = ProjectTask.objects.filter(
        project=project,
        task_type=task_type,
        status__in=ProjectTask.ACTIVE_STATUSES,
    ).first()

    base_title = title or definition.get('title') or dict(ProjectTask.TASK_TYPE_CHOICES).get(task_type, task_type)
    base_description = description or definition.get('description', '')
    metadata_payload = metadata or definition.get('metadata', {})

    if existing:
        updates = []
        if base_title and existing.title != base_title:
            existing.title = base_title
            updates.append('title')
        if base_description and existing.description != base_description:
            existing.description = base_description
            updates.append('description')
        if assigned_role and existing.assigned_role != assigned_role:
            existing.assigned_role = assigned_role
            updates.append('assigned_role')
        if target_unit and existing.target_unit != target_unit:
            existing.target_unit = target_unit
            updates.append('target_unit')
        if assigned_user and existing.assigned_to_id != getattr(assigned_user, 'id', None):
            existing.assigned_to = assigned_user
            updates.append('assigned_to')
        if due_time and existing.due_time != due_time:
            existing.due_time = due_time
            updates.append('due_time')
        if metadata_payload and existing.metadata != metadata_payload:
            existing.metadata = metadata_payload
            updates.append('metadata')
        if updates:
            existing.save(update_fields=updates + ['updated_time'])
        return existing

    return ProjectTask.objects.create(
        project=project,
        task_type=task_type,
        title=base_title,
        description=base_description,
        status='pending',
        assigned_role=assigned_role,
        assigned_to=assigned_user,
        target_unit=target_unit or '',
        due_time=due_time,
        created_by=created_by,
        metadata=metadata_payload,
    )


def _apply_flow_task_automation(project, action, actor):
    automation = FLOW_TASK_AUTOMATIONS.get(action)
    if not automation:
        return
    for task_type in automation.get('complete', []):
        _complete_project_task(project, task_type, actor=actor)
    for create_entry in automation.get('create', []):
        if isinstance(create_entry, str):
            task_type = create_entry
            kwargs = {}
        else:
            task_type = create_entry.get('task_type')
            kwargs = {k: v for k, v in create_entry.items() if k != 'task_type'}
        if not task_type:
            continue
        _ensure_project_task(project, task_type, created_by=actor, **kwargs)


def _handle_task_followups(task, actor):
    next_tasks = TASK_COMPLETION_FOLLOWUPS.get(task.task_type) or []
    for next_task_type in next_tasks:
        _ensure_project_task(task.project, next_task_type, created_by=actor)


# 任务类型到产值事件编码的映射
TASK_TYPE_TO_OUTPUT_VALUE_EVENT = {
    'project_complete_info': None,  # 完善项目信息不直接触发产值
    'configure_team': 'configure_team',  # 配置项目团队
    'client_upload_pre_docs': 'apply_pre_materials',  # 优化前资料申请
    'internal_precheck_docs': 'review_pre_materials',  # 优化前资料复核
    'client_issue_start_notice': 'get_start_notice',  # 获取开工通知
    # 可以根据需要继续添加更多映射
}


def _complete_project_task(project, task_type, actor=None, status='completed'):
    qs = ProjectTask.objects.filter(
        project=project,
        task_type=task_type,
        status__in=ProjectTask.ACTIVE_STATUSES,
    )
    if not qs.exists():
        return
    now = timezone.now()
    for task in qs:
        if status == 'cancelled':
            task.status = 'cancelled'
            task.cancelled_time = now
            if actor:
                task.cancelled_by = actor
            task.save(update_fields=['status', 'cancelled_time', 'cancelled_by', 'updated_time'])
        else:
            task.status = 'completed'
            task.completed_time = now
            if actor:
                task.completed_by = actor
            task.save(update_fields=['status', 'completed_time', 'completed_by', 'updated_time'])
            _handle_task_followups(task, actor)
            
            # 触发产值计算（如果任务类型有对应的产值事件）
            event_code = TASK_TYPE_TO_OUTPUT_VALUE_EVENT.get(task_type)
            if event_code and project.contract_amount and project.contract_amount > 0:
                try:
                    from django.db import connection
                    # 检查产值记录表是否存在
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = 'settlement_output_value_record'
                            );
                        """)
                        table_exists = cursor.fetchone()[0]
                    
                    if table_exists:
                        responsible_user = task.assigned_to or actor or project.project_manager
                        if responsible_user:
                            calculate_output_value(project, event_code, responsible_user=responsible_user)
                            logger.info('已为项目 %s 任务 %s 计算产值，事件：%s，责任人：%s', 
                                      project.project_number, task_type, event_code, responsible_user.username)
                except Exception as output_exc:
                    logger.warning('计算产值失败（可能是模块未初始化）: project=%s, task_type=%s, event_code=%s, error=%s', 
                                 project.project_number, task_type, event_code, str(output_exc))
                    # 产值计算失败不影响任务完成流程


def _user_matches_role(user, project, role):
    if not user or not role:
        return False
    if role == 'client_lead':
        return project.client_leader_id == user.id
    if role == 'design_lead':
        return project.design_leader_id == user.id
    if role == 'project_manager':
        return project.project_manager_id == user.id
    if role == 'business_manager':
        return project.business_manager_id == user.id
    return project.team_members.filter(user=user, role=role, is_active=True).exists()


def _lookup_user_by_phone(phone):
    if not phone:
        return None
    phone_str = str(phone).strip()
    if not phone_str:
        return None
    return User.objects.filter(Q(username=phone_str) | Q(phone=phone_str)).first()


def _sync_external_members(project, client_phone=None, design_phone=None):
    client_phone = client_phone if client_phone is not None else project.client_phone
    design_phone = design_phone if design_phone is not None else project.design_phone
    client_user = _lookup_user_by_phone(client_phone)
    design_user = _lookup_user_by_phone(design_phone)

    project.client_leader = client_user
    project.design_leader = design_user

    _sync_project_team_member(project, client_user, 'client_lead')
    _sync_project_team_member(project, design_user, 'design_lead')
    _reassign_tasks_for_role(project, 'client_lead', client_user)
    _reassign_tasks_for_role(project, 'design_lead', design_user)


def _sync_project_team_member(project, user, role):
    ProjectTeam.objects.filter(project=project, role=role).exclude(user=user).delete()
    if not user:
        return

    team_member, created = ProjectTeam.objects.get_or_create(
        project=project,
        role=role,
        user=user,
        service_profession=None,
        defaults={
            'join_date': timezone.now(),
            'is_active': True,
        }
    )
    updates = []
    if not team_member.is_active:
        team_member.is_active = True
        updates.append('is_active')
    if not team_member.join_date:
        team_member.join_date = timezone.now()
        updates.append('join_date')
    if updates:
        team_member.save(update_fields=updates)


def _build_production_management_nav(permission_set, active_id=None, user=None):
    nav = []
    for item in PRODUCTION_MANAGEMENT_NAV_ITEMS:
        if item.get('require_admin') and not _is_system_admin(user):
            continue
        
        # 新建项目仅对商务经理可见（系统管理员除外）
        if item.get('id') == 'project_create':
            if not _is_system_admin(user):
                has_business_manager_role = user and user.roles.filter(code='business_manager').exists()
                if not has_business_manager_role:
                    continue
        
        if item.get('permissions') and _has_permission(permission_set, *item['permissions']):
            nav.append({
                'label': item['label'],
                'url': reverse(item['url_name']),
                'active': item['id'] == active_id,
            })
        elif not item.get('permissions') and item.get('require_admin'):
            # admin-only entry already handled above
            nav.append({
                'label': item['label'],
                'url': reverse(item['url_name']),
                'active': item['id'] == active_id,
            })
        elif not item.get('permissions'):
            nav.append({
                'label': item['label'],
                'url': reverse(item['url_name']),
                'active': item['id'] == active_id,
            })
    return nav


# 使用统一的顶部导航菜单生成函数（已在文件顶部导入）


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """构建页面上下文"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 添加生产管理左侧导航菜单
        context['module_sidebar_nav'] = _build_production_management_sidebar_nav(permission_set, request.path, request.user, active_id=active_menu_id)
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


@login_required
def production_management_home(request):
    """生产管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    from backend.core.views import _permission_granted
    if not _permission_granted('production_management.view_all', permission_codes) and \
       not _permission_granted('production_management.view_assigned', permission_codes):
        messages.error(request, '您没有权限访问生产管理')
        return redirect('home')  # 重定向到首页，避免无限重定向
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 项目统计
        accessible_ids = _project_ids_user_can_access(request.user)
        projects = Project.objects.filter(id__in=accessible_ids)
        
        total_projects = projects.count()
        active_projects = projects.filter(
            status__in=['in_progress', 'planning', 'waiting_start']
        ).count()
        this_month_projects = projects.filter(
            created_time__gte=this_month_start
        ).count()
        completed_projects = projects.filter(
            status='completed',
            updated_time__gte=this_month_start
        ).count()
        
        summary_cards.append({
            'label': '项目总数',
            'icon': '🏗️',
            'value': str(total_projects),
            'subvalue': f'进行中 {active_projects} 个 · 本月新增 {this_month_projects} 个',
            'url': reverse('production_pages:project_list'),
            'variant': 'info'
        })
        
        summary_cards.append({
            'label': '本月完成',
            'icon': '✅',
            'value': str(completed_projects),
            'subvalue': '本月完成项目',
            'url': reverse('production_pages:project_list'),
            'variant': 'success'
        })
        
        # 任务统计
        try:
            my_tasks = ProjectTask.objects.filter(
                assignee=request.user,
                status__in=['pending', 'in_progress']
            ).count()
            overdue_tasks = ProjectTask.objects.filter(
                assignee=request.user,
                status__in=['pending', 'in_progress'],
                due_time__lt=timezone.now()
            ).count()
            
            if my_tasks > 0:
                summary_cards.append({
                    'label': '我的任务',
                    'icon': '📝',
                    'value': str(my_tasks),
                    'subvalue': f'逾期 {overdue_tasks} 个',
                    'url': reverse('production_pages:project_task_dashboard'),
                    'variant': 'danger' if overdue_tasks > 0 else 'warning'
                })
        except Exception:
            pass
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    # 新建项目需要权限和商务经理角色（系统管理员除外）
    if _permission_granted('production_management.create', permission_codes):
        is_admin = _is_system_admin(request.user)
        has_business_manager_role = request.user.roles.filter(code='business_manager').exists()
        if is_admin or has_business_manager_role:
            try:
                quick_actions.append({
                    'label': '新建生产启动',
                    'icon': '➕',
                    'description': '创建新的生产项目',
                    'url': reverse('production_pages:project_create'),
                    'link_label': '创建项目 →'
                })
            except Exception:
                pass
    
    # 功能模块入口
    module_entries = []
    
    try:
        module_entries.append({
            'label': '项目列表',
            'icon': '📋',
            'description': '查看和管理所有项目',
            'url': reverse('production_pages:project_list'),
            'link_label': '进入模块 →'
        })
        
        if _permission_granted('production_management.view_all', permission_codes) or \
           _permission_granted('production_management.view_assigned', permission_codes):
            try:
                module_entries.append({
                    'label': '任务看板',
                    'icon': '📊',
                    'description': '查看项目任务看板',
                    'url': reverse('production_pages:project_task_dashboard'),
                    'link_label': '进入模块 →'
                })
            except Exception:
                pass
    except Exception:
        pass
    
    # 构建区域
    sections = []
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions,
            'layout': 'grid'
        })
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '生产管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="生产管理",
        page_icon="🏗️",
        description="从项目创建到交付完成的全流程数字化管理",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='production_home',
    )
    
    return render(request, "production_management/home.html", context)


def _build_production_management_sidebar_nav(permission_set, request_path=None, user=None, active_id=None):
    """生成生产管理模块的左侧菜单导航（统一格式）"""
    from backend.core.views import _permission_granted
    
    def _check_production_permission(permission, permission_set):
        """生产管理模块的自定义权限检查函数（简化版，仅处理基础权限）"""
        if not permission:
            return True
        return _permission_granted(permission, permission_set)
    
    # 使用统一的菜单构建函数
    menu = _build_unified_sidebar_nav(
        PRODUCTION_MANAGEMENT_SIDEBAR_MENU, 
        permission_set, 
        active_id=active_id,
        permission_check_func=_check_production_permission
    )
    
    # 后处理：移除project_create（如果用户不是系统管理员且不是商务经理）
    if user:
        for group in menu:
            if group.get('children'):
                children = group.get('children', [])
                # 过滤掉project_create（如果用户没有权限）
                filtered_children = []
                for child in children:
                    if child.get('id') == 'project_create':
                        # 检查是否是系统管理员或商务经理
                        if _is_system_admin(user) or (user.roles.filter(code='business_manager').exists()):
                            filtered_children.append(child)
                    else:
                        filtered_children.append(child)
                group['children'] = filtered_children
                # 如果分组没有子项了，从菜单中移除
                if not filtered_children:
                    menu.remove(group)
    
    return menu


def _with_nav(context, permission_set, active_id=None, user=None, request_path=None, request=None):
    """构建带导航的上下文
    
    Args:
        context: 基础上下文字典
        permission_set: 用户权限集合
        active_id: 当前激活的菜单项ID
        user: 当前用户
        request_path: 当前请求路径（可选，如果提供了request则自动获取）
        request: 当前请求对象（可选，用于自动获取request_path）
    """
    context = context or {}
    context['production_management_nav'] = _build_production_management_nav(permission_set, active_id, user)
    # 添加完整导航菜单（包含所有模块的菜单项）
    context['full_top_nav'] = _build_full_top_nav(permission_set, user)
    # 添加生产管理左侧导航菜单
    # 如果提供了request对象但没有提供request_path，则从request中获取
    if request and not request_path:
        request_path = request.path
    sidebar_nav = _build_production_management_sidebar_nav(permission_set, request_path, user, active_id=active_id)
    context['production_management_menu'] = sidebar_nav
    context['module_sidebar_nav'] = sidebar_nav  # 统一使用 module_sidebar_nav
    
    # 调试日志：记录上下文设置
    import logging
    logger = logging.getLogger(__name__)
    logger.debug('_with_nav - 设置 module_sidebar_nav: %d 个菜单项', len(sidebar_nav) if sidebar_nav else 0)
    
    return context


def _is_project_readonly(permission_set):
    return not _has_permission(permission_set, 'production_management.create', 'production_management.configure_team')


def _is_system_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles.filter(code='system_admin').exists()


def _validate_team_configuration(project):
    errors = []
    if not project.project_manager_id:
        errors.append('请指定项目负责人')
    if not ProjectTeam.objects.filter(project=project, role='business_manager', is_active=True).exists():
        errors.append('团队中必须包含商务经理')
    for profession in project.service_professions.all():
        assignments = ProjectTeam.objects.filter(project=project, service_profession=profession, is_active=True)
        has_leader = assignments.filter(role__in=['professional_leader', 'external_leader']).exists()
        has_engineer = assignments.filter(role__in=['engineer', 'external_engineer']).exists()
        if not has_leader:
            errors.append(f'{profession.name} 缺少专业负责人')
        if not has_engineer:
            errors.append(f'{profession.name} 缺少专业工程师')
    if errors:
        raise ValidationError(errors)


def _log_team_changes(project, operator, previous_snapshot, current_snapshot):
    previous = set(previous_snapshot)
    current = set(current_snapshot)
    added = current - previous
    removed = previous - current
    change_details = {'added': [], 'removed': []}

    for user_id, role, unit, is_external, profession_id in added:
        member = User.objects.filter(id=user_id).first()
        profession = ServiceProfession.objects.filter(id=profession_id).first() if profession_id else None
        ProjectTeamChangeLog.objects.create(
            project=project,
            member=member,
            role=role,
            unit=unit,
            is_external=is_external,
            service_profession=profession,
            action='added',
            operator=operator,
        )
        change_details['added'].append({
            'member': member,
            'role': role,
            'unit': unit,
            'profession': profession,
            'is_external': is_external,
        })

    for user_id, role, unit, is_external, profession_id in removed:
        member = User.objects.filter(id=user_id).first()
        profession = ServiceProfession.objects.filter(id=profession_id).first() if profession_id else None
        ProjectTeamChangeLog.objects.create(
            project=project,
            member=member,
            role=role,
            unit=unit,
            is_external=is_external,
            service_profession=profession,
            action='removed',
            operator=operator,
        )
        change_details['removed'].append({
            'member': member,
            'role': role,
            'unit': unit,
            'profession': profession,
            'is_external': is_external,
        })

    return change_details


def _summarize_changes(change_details):
    parts = []
    if change_details['added']:
        seen_members = set()
        names = []
        anonymous_count = 0
        for entry in change_details['added']:
            member = entry.get('member')
            if member and member.id:
                if member.id in seen_members:
                    continue
                seen_members.add(member.id)
                names.append(member.get_full_name() or member.username)
            else:
                anonymous_count += 1
        total_added = len(seen_members) + anonymous_count
        parts.append(
            f"新增 {total_added} 人"
            + (f"：{'、'.join(names[:3])}{'…' if len(names) > 3 else ''}" if names else '')
        )
    if change_details['removed']:
        seen_members = set()
        names = []
        anonymous_count = 0
        for entry in change_details['removed']:
            member = entry.get('member')
            if member and member.id:
                if member.id in seen_members:
                    continue
                seen_members.add(member.id)
                names.append(member.get_full_name() or member.username)
            else:
                anonymous_count += 1
        total_removed = len(seen_members) + anonymous_count
        parts.append(
            f"移除 {total_removed} 人"
            + (f"：{'、'.join(names[:3])}{'…' if len(names) > 3 else ''}" if names else '')
        )
    return '；'.join(parts)


def _create_team_notification(project, recipient, title, message, action_url=None, operator=None, context=None):
    if not recipient:
        return
    if not action_url:
        action_url = reverse('production_pages:project_detail', args=[project.id])
    ProjectTeamNotification.objects.create(
        project=project,
        recipient=recipient,
        title=title,
        message=message,
        action_url=action_url,
        operator=operator,
        context=context or {},
    )


def _notify_team_change(project, operator, change_details):
    if not change_details['added'] and not change_details['removed']:
        return ''
    summary = _summarize_changes(change_details)
    operator_name = ''
    if operator:
        operator_name = operator.get_full_name() or operator.username
    action_url = reverse('production_pages:project_detail', args=[project.id])

    for entry in change_details['added']:
        member = entry.get('member')
        if not member:
            continue
        role_label = ROLE_LABELS.get(entry.get('role'), entry.get('role'))
        unit_label = UNIT_LABELS.get(entry.get('unit'), '')
        profession = entry.get('profession')
        profession_label = f"（{profession.name}）" if profession else ''
        message = f"您被指派为《{project.name}》({project.project_number}){unit_label}的{role_label}{profession_label}。"
        if operator_name:
            message += f" 操作人：{operator_name}"
        _create_team_notification(
            project,
            member,
            '团队新增成员',
            message,
            action_url,
            operator=operator,
            context={
                'action': 'added',
                'role': role_label,
                'profession': profession.name if profession else None,
                'unit': unit_label,
            }
        )

    for entry in change_details['removed']:
        member = entry.get('member')
        if not member:
            continue
        role_label = ROLE_LABELS.get(entry.get('role'), entry.get('role'))
        unit_label = UNIT_LABELS.get(entry.get('unit'), '')
        profession = entry.get('profession')
        profession_label = f"（{profession.name}）" if profession else ''
        message = f"您已从《{project.name}》({project.project_number}){unit_label}的{role_label}{profession_label}角色中移除。"
        if operator_name:
            message += f" 操作人：{operator_name}"
        _create_team_notification(
            project,
            member,
            '团队成员调整',
            message,
            action_url,
            operator=operator,
            context={
                'action': 'removed',
                'role': role_label,
                'profession': profession.name if profession else None,
                'unit': unit_label,
            }
        )

    stakeholder_candidates = {
        project.project_manager,
        project.business_manager,
        project.created_by,
    }
    if operator:
        stakeholder_candidates.add(operator)
    stakeholder_candidates.discard(None)
    stakeholder_message = f"{project.project_number} {project.name} 团队更新：{summary}" if summary else ''
    if operator_name:
        stakeholder_message += f"（操作人：{operator_name}）"
    for stakeholder in stakeholder_candidates:
        if not stakeholder_message:
            continue
        _create_team_notification(
            project,
            stakeholder,
            '团队变更提醒',
            stakeholder_message,
            action_url,
            operator=operator,
            context={
                'action': 'summary',
                'summary': summary,
                'changed_roles': [
                    {
                        'member': entry.get('member').username if entry.get('member') else None,
                        'role': ROLE_LABELS.get(entry.get('role'), entry.get('role')),
                        'unit': UNIT_LABELS.get(entry.get('unit'), entry.get('unit')),
                        'action': 'added',
                    }
                    for entry in change_details['added']
                ] + [
                    {
                        'member': entry.get('member').username if entry.get('member') else None,
                        'role': ROLE_LABELS.get(entry.get('role'), entry.get('role')),
                        'unit': UNIT_LABELS.get(entry.get('unit'), entry.get('unit')),
                        'action': 'removed',
                    }
                    for entry in change_details['removed']
                ]
            }
        )

    logger.info('项目[%s]团队变更 by %s: %s', project.project_number, operator.username if operator else '系统', summary)
    return summary


def _compute_project_metric(project):
    milestones = list(project.milestones.all())

    service_timeline, service_completion = _build_service_timeline(project, milestones)
    if service_timeline:
        total_milestones = len(service_timeline)
        completed_milestones = len([stage for stage in service_timeline if stage["status"] == "completed"])
        progress_percent = service_completion
    else:
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.is_completed])
        progress_percent = int(completed_milestones / total_milestones * 100) if total_milestones else 0
        service_completion = progress_percent

    quality_score = 80 + (progress_percent % 15)
    risk_score = 90 - (progress_percent % 15)
    health_score = round((progress_percent * 0.7) + (quality_score * 0.2) + (risk_score * 0.1), 1)

    return {
        'project_id': project.id,
        'project_number': project.project_number,
        'project_name': project.name,
        'status': project.get_status_display(),
        'progress_percent': progress_percent,
        'milestone_total': total_milestones,
        'milestone_completed': completed_milestones,
        'quality_score': quality_score,
        'risk_score': risk_score,
        'health_score': health_score,
        'team_size': project.team_members.filter(is_active=True).count(),
        'client_company': project.client_company_name or '—',
        'design_company': project.design_company or '—',
    }

def build_project_dashboard_payload(user, permission_set, query_params):
    projects = Project.objects.select_related(
        'project_manager',
        'business_manager',
        'client',
        'client_leader',
        'design_leader',
        'responsible_department',
        'responsible_person',
        'created_by'
    ).prefetch_related(
        'service_professions',
        'milestones',
        'team_members'
    )

    has_global_view = _has_global_project_view(permission_set, user)
    projects = _filter_projects_for_user(projects, user, permission_set)

    project_id = query_params.get('project')
    service_type_id = query_params.get('service_type')
    project_manager_id = query_params.get('project_manager')
    status_list = query_params.getlist('status') if hasattr(query_params, 'getlist') else query_params.get('status', [])
    date_from = query_params.get('date_from')
    date_to = query_params.get('date_to')

    if project_id:
        projects = projects.filter(id=project_id)
    if service_type_id:
        projects = projects.filter(service_type_id=service_type_id)
    if project_manager_id:
        projects = projects.filter(project_manager_id=project_manager_id)
    if status_list:
        # status_list may be string if not QueryDict
        if isinstance(status_list, str):
            status_list = [status_list]
        projects = projects.filter(status__in=status_list)
    if date_from:
        projects = projects.filter(created_time__date__gte=date_from)
    if date_to:
        projects = projects.filter(created_time__date__lte=date_to)

    all_projects = projects.distinct()
    project_list = list(all_projects)
    project_metrics = [_compute_project_metric(p) for p in project_list]

    today = timezone.now().date()
    delayed_task_reminders = []
    for project_obj, metric in zip(project_list, project_metrics):
        for milestone in project_obj.milestones.all():
            delay_days = 0
            if milestone.planned_date and milestone.actual_date and milestone.actual_date > milestone.planned_date:
                delay_days = (milestone.actual_date - milestone.planned_date).days
            elif (
                milestone.planned_date
                and milestone.planned_date < today
                and not milestone.is_completed
            ):
                delay_days = (today - milestone.planned_date).days
            if delay_days <= 0:
                continue
            delayed_task_reminders.append({
                'project_id': project_obj.id,
                'project_name': metric['project_name'],
                'milestone_id': milestone.id,
                'name': milestone.name,
                'delay_days': delay_days,
                'url': f"{reverse('production_pages:project_detail', args=[project_obj.id])}?tab=progress&milestone={milestone.id}",
            })

    delayed_task_reminders.sort(key=lambda item: item['delay_days'], reverse=True)
    delayed_task_reminders = delayed_task_reminders[:5]

    summary = {
        'project_count': all_projects.count(),
        'active_count': all_projects.filter(status='in_progress').count(),
        'completed_count': all_projects.filter(status='completed').count(),
        'average_health_score': round(sum(m['health_score'] for m in project_metrics) / len(project_metrics), 1) if project_metrics else 0,
        'average_progress_percent': round(sum(m['progress_percent'] for m in project_metrics) / len(project_metrics), 1) if project_metrics else 0,
        'last_updated': timezone.now(),
    }

    summary['average_progress_percent'] = min(max(summary['average_progress_percent'], 0), 100)

    summary_json = summary.copy()
    summary_json['last_updated'] = summary['last_updated'].isoformat()

    milestone_completed_total = sum(m['milestone_completed'] for m in project_metrics)
    milestone_total_total = sum(m['milestone_total'] for m in project_metrics)
    milestone_in_progress = max(milestone_total_total - milestone_completed_total, 0)
    summary['milestone_completed_total'] = milestone_completed_total

    milestone_summary = {
        'labels': ['已完成', '进行中', '未开始'],
        'data': [
            milestone_completed_total,
            milestone_in_progress,
            max(len(project_metrics) * 3 - milestone_completed_total - milestone_in_progress, 0),
        ],
    }

    progress_trends = {
        'labels': [m['project_name'] for m in project_metrics],
        'progress': [m['progress_percent'] for m in project_metrics],
    }

    risk_matrix = [
        {
            'name': m['project_name'],
            'probability': min(100, 100 - m['progress_percent'] + 10),
            'impact': min(100, 100 - m['quality_score'] + 10),
        }
        for m in project_metrics
    ]

    quality_distribution_counter = {'优秀': 0, '良好': 0, '待提升': 0}
    for metric in project_metrics:
        score = metric['quality_score']
        if score >= 90:
            quality_distribution_counter['优秀'] += 1
        elif score >= 75:
            quality_distribution_counter['良好'] += 1
        else:
            quality_distribution_counter['待提升'] += 1
    quality_distribution = {
        'labels': list(quality_distribution_counter.keys()),
        'data': list(quality_distribution_counter.values()),
    }
    quality_trend = {
        'labels': [m['project_name'] for m in project_metrics],
        'quality_scores': [m['quality_score'] for m in project_metrics],
    }

    primary_project_id = project_metrics[0]['project_id'] if project_metrics else None
    detail_url = reverse('production_pages:project_detail', args=[primary_project_id]) if primary_project_id else '#'
    team_url = reverse('production_pages:project_team', args=[primary_project_id]) if primary_project_id else '#'
    notifications = [
        # {
        #     'type': 'task',
        #     'title': '存在未处理的质量意见',
        #     'time': '2小时前',
        #     'url': reverse('production_quality_pages:opinion_review'),  # 已删除生产质量模块
        # },
        {
            'type': 'risk',
            'title': '项目风险等级提升',
            'time': '昨天',
            'url': f"{detail_url}?tab=risk" if primary_project_id else '#',
        },
    ]
    quick_actions = [
        {'label': '进入项目详情', 'url': detail_url},
        {'label': '配置团队权限', 'url': team_url},
        {'label': '发起质量审核', 'url': '#'},
        {'label': '生成进展报告', 'url': '#'},
    ]

    filter_projects = Project.objects.values('id', 'name', 'project_number')

    selected_filters = {
        'project': project_id,
        'service_type': service_type_id,
        'project_manager': project_manager_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return {
        'projects': all_projects,
        'project_metrics': project_metrics,
        'summary': summary,
        'milestone_summary': milestone_summary,
        'progress_trends': progress_trends,
        'risk_matrix': risk_matrix,
        'quality_distribution': quality_distribution,
        'quality_trend': quality_trend,
        'notifications': notifications,
        'delayed_task_reminders': delayed_task_reminders,
        'quick_actions': quick_actions,
        'filter_projects': filter_projects,
        'selected_filters': selected_filters,
        'primary_metric': project_metrics[0] if project_metrics else None,
        'summary_json': summary_json,
    }


@login_required
def project_create(request):
    """新建生产启动页面（仅商务经理可访问）"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有创建项目的权限。', 'production_management.create'):
        return redirect('production_pages:production_management_home')
    
    # 检查用户是否有商务经理角色（系统管理员除外）
    if not _is_system_admin(request.user):
        has_business_manager_role = request.user.roles.filter(code='business_manager').exists()
        if not has_business_manager_role:
            messages.error(request, '只有商务经理可以创建项目。')
            return redirect('production_pages:production_management_home')

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
                design_company = (request.POST.get('design_company') or '').strip()
                design_contact_person = (request.POST.get('design_contact_person') or '').strip()
                design_phone = (request.POST.get('design_phone') or '').strip()
                design_email = (request.POST.get('design_email') or '').strip()
                
                if not is_draft:
                    # 提交时验证必填字段
                    required_pairs = [
                        (design_company, '请填写设计单位名称'),
                        (design_phone, '请填写设计方联系电话'),
                    ]
                    for value, error_msg in required_pairs:
                        if not value:
                            messages.error(request, error_msg)
                            context = build_project_create_context(request.POST)
                            return render(request, 'production_management/project_create.html', _with_nav(context, permission_set, 'project_create', request.user, request=request))
                
                # 处理负责部门和负责人
                responsible_department_id = request.POST.get('responsible_department') or None
                responsible_department_obj = None
                if responsible_department_id:
                    try:
                        responsible_department_obj = Department.objects.filter(id=int(responsible_department_id), is_active=True).first()
                    except (ValueError, TypeError):
                        pass
                
                responsible_person_id = request.POST.get('responsible_person') or None
                responsible_person_obj = None
                if responsible_person_id:
                    try:
                        responsible_person_obj = User.objects.filter(id=int(responsible_person_id), is_active=True).first()
                    except (ValueError, TypeError):
                        pass
                
                # 处理合同金额（转换为 Decimal 类型）
                project = Project.objects.create(
                    project_number=project_number,
                    name=request.POST.get('name') or '未命名项目',
                    design_company=design_company,
                    design_contact_person=design_contact_person,
                    design_phone=design_phone,
                    design_email=design_email,
                    responsible_department=responsible_department_obj,
                    responsible_person=responsible_person_obj,
                    created_by=request.user,
                    business_manager=request.user,
                    status='draft' if is_draft else 'waiting_receive'
                )

                _sync_external_members(project, None, design_phone)
                project.save(update_fields=['client_leader', 'design_leader'])

                if not is_draft:
                    _ensure_project_task(project, 'client_upload_pre_docs', created_by=request.user)
                
                # 触发产值计算：创建新项目
                if not is_draft and project.contract_amount and project.contract_amount > 0:
                    try:
                        from django.db import connection
                        # 检查产值记录表是否存在
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public' 
                                    AND table_name = 'settlement_output_value_record'
                                );
                            """)
                            table_exists = cursor.fetchone()[0]
                        
                        if table_exists:
                            from backend.apps.settlement_center.services import calculate_output_value
                            calculate_output_value(project, 'create_project', responsible_user=request.user)
                            logger.info('已为项目 %s 计算"创建新项目"产值，创建人：%s', project.project_number, request.user.username)
                    except Exception as output_exc:
                        logger.warning('计算"创建新项目"产值失败（可能是模块未初始化）: %s', str(output_exc))
                        # 产值计算失败不影响项目创建流程
                
                messages.success(request, '项目创建成功！')
                if request.POST.get('action') == 'submit':
                    messages.info(request, '项目已提交，待技术中心接收后由项目经理完善信息。')
                return redirect('production_pages:project_list')
        except Exception as e:
            messages.error(request, f'项目创建失败：{str(e)}')
            context = build_project_create_context(request.POST)
            context['production_management_nav'] = _build_production_management_nav(permission_set, 'project_create')
            return render(request, 'production_management/project_create.html', _with_nav(context, permission_set, 'project_create', request.user, request=request))

    context = build_project_create_context()
    return render(request, 'production_management/project_create.html', _with_nav(context, permission_set, 'project_create', request.user, request=request))


@login_required
def project_edit(request, project_id):
    """编辑项目（草稿或待完善）"""
    project = get_object_or_404(
        Project.objects.prefetch_related('service_professions'),
        id=project_id
    )

    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有编辑项目的权限。', 'production_management.create', 'production_management.configure_team'):
        return redirect('admin:index')
    if not _has_permission(permission_set, 'production_management.view_all') and not _user_is_project_member(request.user, project):
        messages.error(request, '您无权编辑该项目。')
        return redirect('admin:index')

    if project.status not in ['draft', 'waiting_receive', 'configuring']:
        messages.error(request, '当前状态下无法编辑该项目')
        return redirect('production_pages:project_detail', project_id=project.id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                action = request.POST.get('action', 'draft')
                is_draft = action == 'draft'

                project.name = request.POST.get('name') or project.name

                # 处理负责部门和负责人
                responsible_department_id = request.POST.get('responsible_department') or None
                responsible_department_obj = None
                if responsible_department_id:
                    try:
                        responsible_department_obj = Department.objects.filter(id=int(responsible_department_id), is_active=True).first()
                    except (ValueError, TypeError):
                        pass
                project.responsible_department = responsible_department_obj

                responsible_person_id = request.POST.get('responsible_person') or None
                responsible_person_obj = None
                if responsible_person_id:
                    try:
                        responsible_person_obj = User.objects.filter(id=int(responsible_person_id), is_active=True).first()
                    except (ValueError, TypeError):
                        pass
                project.responsible_person = responsible_person_obj

                project.design_company = request.POST.get('design_company', project.design_company)
                project.design_contact_person = request.POST.get('design_contact_person', project.design_contact_person)
                project.design_phone = request.POST.get('design_phone', project.design_phone)
                project.design_email = request.POST.get('design_email', project.design_email)

                _sync_external_members(project)

                project.status = 'draft' if is_draft else 'waiting_receive'
                project.save()

                if not is_draft:
                    _ensure_project_task(project, 'client_upload_pre_docs', created_by=request.user)

                messages.success(request, '项目信息已更新')
                if is_draft:
                    return redirect('production_pages:project_edit', project_id=project.id)
                return redirect('production_pages:project_detail', project_id=project.id)
        except Exception as exc:
            messages.error(request, f'保存失败：{exc}')
            return render(request, 'production_management/project_edit.html', build_project_edit_context(project, permission_set, request.POST, request.user))

    context = build_project_edit_context(project, permission_set, user=request.user)
    return render(request, 'production_management/project_edit.html', _with_nav(context, permission_set, 'project_list', request.user))


@login_required
def project_complete(request, project_id):
    """完善项目信息（客户/设计方/详细资料）"""
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)

    if not _require_permission(
        request,
        permission_set,
        '您没有访问项目信息完善页面的权限。',
        'production_management.view_all',
        'production_management.view_assigned',
    ):
        return redirect('admin:index')

    if project.project_manager_id != request.user.id:
        messages.error(request, '仅项目负责人可完善项目信息。')
        return redirect('production_pages:project_detail', project_id=project.id)

    read_only = False

    if request.method == 'POST':
        if read_only:
            messages.error(request, '当前权限不可修改项目。')
            return redirect('production_pages:project_complete', project_id=project.id)

        try:
            with transaction.atomic():
                project.client_company_name = (request.POST.get('client_company_name') or project.client_company_name or '').strip()
                project.client_contact_person = (request.POST.get('client_contact_person') or project.client_contact_person or '').strip()
                project.client_phone = (request.POST.get('client_phone') or project.client_phone or '').strip()
                project.client_email = (request.POST.get('client_email') or project.client_email or '').strip()
                project.client_address = (request.POST.get('client_address') or project.client_address or '').strip()

                project.design_company = (request.POST.get('design_company') or project.design_company or '').strip()
                project.design_contact_person = (request.POST.get('design_contact_person') or project.design_contact_person or '').strip()
                project.design_phone = (request.POST.get('design_phone') or project.design_phone or '').strip()
                project.design_email = (request.POST.get('design_email') or project.design_email or '').strip()

                project.project_address = (request.POST.get('project_address') or project.project_address or '').strip()

                aboveground_area = _parse_decimal_input(request.POST.get('aboveground_area'))
                underground_area = _parse_decimal_input(request.POST.get('underground_area'))
                building_area = _parse_decimal_input(request.POST.get('building_area'))

                if aboveground_area is not None:
                    project.aboveground_area = aboveground_area
                if underground_area is not None:
                    project.underground_area = underground_area
                if aboveground_area is not None or underground_area is not None:
                    total = (aboveground_area or Decimal('0')) + (underground_area or Decimal('0'))
                    project.building_area = total if total else building_area
                elif building_area is not None:
                    project.building_area = building_area

                project.building_height = _parse_decimal_input(request.POST.get('building_height')) or project.building_height
                if request.POST.get('aboveground_floors') is not None:
                    try:
                        project.aboveground_floors = int(request.POST.get('aboveground_floors') or 0)
                    except ValueError:
                        project.aboveground_floors = None
                if request.POST.get('underground_floors') is not None:
                    try:
                        project.underground_floors = int(request.POST.get('underground_floors') or 0)
                    except ValueError:
                        project.underground_floors = None

                project.structure_type = request.POST.get('structure_type') or project.structure_type
                project.client_special_requirements = request.POST.get('client_special_requirements', project.client_special_requirements or '')
                project.technical_difficulties = request.POST.get('technical_difficulties', project.technical_difficulties or '')
                project.risk_assessment = request.POST.get('risk_assessment', project.risk_assessment or '')

                _sync_external_members(project)
                project.save()
                
                # 标记"完善项目信息"任务为已完成
                _complete_project_task(project, 'project_complete_info', actor=request.user)
                
                if project.status not in ['draft']:
                    _ensure_project_task(project, 'client_upload_pre_docs', created_by=request.user)
                
                messages.success(request, '项目信息已更新。')
                return redirect('production_pages:project_detail', project_id=project.id)
        except Exception as exc:
            logger.exception('项目信息完善失败: %s', exc)
            messages.error(request, f'保存失败：{exc}')

    context = {
        'project': project,
        'read_only': read_only,
    }
    return render(
        request,
        'production_management/project_complete.html',
        _with_nav(context, permission_set, 'project_list', request.user)
    )


@login_required
def project_receive(request, project_id):
    """项目接收，指派项目经理"""
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)

    if not _require_permission(
        request,
        permission_set,
        '您没有接收项目的权限。',
        'production_management.view_all',
        'production_management.view_assigned',
        'production_management.create',
        'production_management.configure_team',
    ):
        return redirect('admin:index')

    if not _has_permission(permission_set, 'production_management.view_all') and not _user_is_project_member(request.user, project):
        messages.error(request, '您无权操作该项目。')
        return redirect('admin:index')

    read_only = _is_project_readonly(permission_set)
    # 只筛选具有项目经理角色的用户
    project_manager_candidates = User.objects.filter(
        is_active=True,
        user_type='internal',
        roles__code='project_manager'
    ).distinct().order_by('first_name', 'last_name', 'username')

    if request.method == 'POST':
        if read_only:
            messages.error(request, '当前权限不可接收项目。')
            return redirect('production_pages:project_receive', project_id=project.id)

        manager_id = request.POST.get('project_manager')
        manager = None
        if manager_id:
            # 验证选中的用户是否具有项目经理角色
            manager = User.objects.filter(
                id=manager_id,
                is_active=True,
                user_type='internal',
                roles__code='project_manager'
            ).first()
        if not manager:
            messages.error(request, '请选择项目经理（必须具有项目负责人角色）')
        else:
            try:
                with transaction.atomic():
                    project.project_manager = manager
                    if project.status in ['waiting_receive', 'draft']:
                        project.status = 'configuring'
                    project.save()
                    _reassign_tasks_for_role(project, 'project_manager', manager)

                    ProjectTeam.objects.update_or_create(
                        project=project,
                        role='project_manager',
                        defaults={
                            'user': manager,
                            'unit': 'management',
                            'service_profession': None,
                            'is_active': True,
                        }
                    )

                    # 创建任务给项目经理
                    try:
                        # 创建"完善项目信息"任务
                        _ensure_project_task(
                            project=project,
                            task_type='project_complete_info',
                            assigned_to=manager,
                            assigned_role='project_manager',
                            created_by=request.user,
                        )
                        logger.info('已为项目经理 %s 创建"完善项目信息"任务，项目：%s', manager.username, project.project_number)
                    except Exception as task_exc:
                        logger.exception('创建"完善项目信息"任务失败: %s', task_exc)
                    
                    try:
                        # 创建"配置项目团队"任务
                        _ensure_project_task(
                            project=project,
                            task_type='configure_team',
                            assigned_to=manager,
                            assigned_role='project_manager',
                            created_by=request.user,
                        )
                        logger.info('已为项目经理 %s 创建"配置项目团队"任务，项目：%s', manager.username, project.project_number)
                    except Exception as task_exc:
                        logger.exception('创建"配置项目团队"任务失败: %s', task_exc)

                    # 创建通知给项目经理
                    try:
                        operator_name = request.user.get_full_name() or request.user.username
                        project_complete_url = reverse('production_pages:project_complete', args=[project.id])
                        
                        _create_team_notification(
                            project=project,
                            recipient=manager,
                            title='项目接收通知',
                            message=f'您已被指派为《{project.name}》({project.project_number})的项目负责人。请及时完善项目信息并配置团队。',
                            action_url=project_complete_url,
                            operator=request.user,
                            context={
                                'action': 'assigned_project_manager',
                                'project_status': project.status,
                            }
                        )
                        logger.info('已为项目经理 %s 创建项目接收通知，项目：%s', manager.username, project.project_number)
                    except Exception as notif_exc:
                        # 通知创建失败不影响项目接收，但需要记录日志
                        logger.exception('创建项目接收通知失败: %s', notif_exc)

                    messages.success(request, '项目接收成功，已指派项目经理。')
                    messages.info(request, '请等待项目经理完善项目信息。')
                    return redirect('production_pages:project_list')
            except Exception as exc:
                logger.exception('项目接收失败: %s', exc)
                messages.error(request, f'项目接收失败：{exc}')

    context = {
        'project': project,
        'project_manager_candidates': project_manager_candidates,
        'business_manager': project.business_manager,
        'read_only': read_only,
    }
    return render(
        request,
        'production_management/project_receive.html',
        _with_nav(context, permission_set, 'project_list', request.user)
    )


@login_required
def project_team(request, project_id):
    """团队配置页面"""
    project = get_object_or_404(Project, id=project_id)

    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有配置项目团队的权限。', 'production_management.configure_team'):
        return redirect('admin:index')
    # 允许项目经理配置自己负责的项目，或者有 view_all 权限的用户，或者是项目成员
    is_project_manager = project.project_manager_id == request.user.id
    if not _has_permission(permission_set, 'production_management.view_all') and not is_project_manager and not _user_is_project_member(request.user, project):
        messages.error(request, '您无权配置该项目团队。')
        return redirect('admin:index')
    
    existing_snapshot = list(ProjectTeam.objects.filter(project=project, is_active=True).values_list('user_id', 'role', 'unit', 'is_external', 'service_profession_id'))

    if request.method == 'POST':
        try:
            with transaction.atomic():
                def _normalize_ids(raw_list):
                    return [int(uid) for uid in raw_list if str(uid).strip()]

                def sync_role(role_code, new_ids, profession_obj=None):
                    meta = ROLE_META[role_code]
                    if meta['per_profession'] and profession_obj is None:
                        return
                    qs = ProjectTeam.objects.filter(
                        project=project,
                        role=role_code,
                        unit=meta['unit'],
                        is_external=meta['is_external'],
                    )
                    if meta['per_profession']:
                        qs = qs.filter(service_profession=profession_obj)
                    else:
                        qs = qs.filter(service_profession__isnull=True)
                    existing_ids = set(qs.values_list('user_id', flat=True))
                    new_ids_clean = []
                    for uid in new_ids:
                        try:
                            val = int(uid)
                        except (TypeError, ValueError):
                            continue
                        if val not in new_ids_clean:
                            new_ids_clean.append(val)
                    if not meta['multiple'] and new_ids_clean:
                        new_ids_clean = new_ids_clean[:1]
                    new_ids_set = set(new_ids_clean)
                    to_add = new_ids_set - existing_ids
                    to_remove = existing_ids - new_ids_set

                    for user_id in to_add:
                        ProjectTeam.objects.create(
                            project=project,
                            user_id=user_id,
                            service_profession=profession_obj if meta['per_profession'] else None,
                            role=role_code,
                            unit=meta['unit'],
                            join_date=timezone.now()
                        )
                    if to_remove:
                        qs.filter(user_id__in=to_remove).delete()

                # 更新项目负责人
                project_manager_id = request.POST.get('project_manager')
                if project_manager_id:
                    project.project_manager_id = int(project_manager_id)
                    project.save(update_fields=['project_manager'])
                    sync_role('project_manager', [project_manager_id])
                else:
                    sync_role('project_manager', [])

                # 商务经理保持项目创建人
                if project.business_manager_id:
                    sync_role('business_manager', [project.business_manager_id])
                else:
                    sync_role('business_manager', [])

                professions = list(project.service_professions.all())

                for profession in professions:
                    profession_key = profession.code

                    leader_id = request.POST.get(f'profession_{profession_key}_leader')
                    leader_ids = [leader_id] if leader_id else []
                    sync_role('professional_leader', leader_ids, profession)

                    engineer_ids = _normalize_ids(request.POST.getlist(f'profession_{profession_key}_engineers[]'))
                    sync_role('engineer', engineer_ids, profession)

                    external_leader_id = request.POST.get(f'profession_{profession_key}_external_leader')
                    external_leader_ids = [external_leader_id] if external_leader_id else []
                    sync_role('external_leader', external_leader_ids, profession)

                    external_engineer_ids = _normalize_ids(request.POST.getlist(f'profession_{profession_key}_external_engineers[]'))
                    sync_role('external_engineer', external_engineer_ids, profession)

                # 支持团队
                assistant_ids = _normalize_ids(request.POST.getlist('assistants[]'))
                sync_role('technical_assistant', assistant_ids)

                cost_civil_ids = _normalize_ids(request.POST.getlist('cost_civil[]'))
                sync_role('cost_engineer_civil', cost_civil_ids)

                cost_installation_ids = _normalize_ids(request.POST.getlist('cost_installation[]'))
                sync_role('cost_engineer_installation', cost_installation_ids)

                cost_reviewer_civil_ids = _normalize_ids(request.POST.getlist('cost_reviewer_civil[]'))
                sync_role('cost_reviewer_civil', cost_reviewer_civil_ids)

                cost_reviewer_installation_ids = _normalize_ids(request.POST.getlist('cost_reviewer_installation[]'))
                sync_role('cost_reviewer_installation', cost_reviewer_installation_ids)

                external_cost_civil_ids = _normalize_ids(request.POST.getlist('external_cost_civil[]'))
                sync_role('external_cost_engineer_civil', external_cost_civil_ids)

                external_cost_installation_ids = _normalize_ids(request.POST.getlist('external_cost_installation[]'))
                sync_role('external_cost_engineer_installation', external_cost_installation_ids)

                external_cost_reviewer_civil_ids = _normalize_ids(request.POST.getlist('external_cost_reviewer_civil[]'))
                sync_role('external_cost_reviewer_civil', external_cost_reviewer_civil_ids)

                external_cost_reviewer_installation_ids = _normalize_ids(request.POST.getlist('external_cost_reviewer_installation[]'))
                sync_role('external_cost_reviewer_installation', external_cost_reviewer_installation_ids)

                project.status = 'waiting_start'
                project.save(update_fields=['status'])
                _validate_team_configuration(project)

                new_snapshot = list(ProjectTeam.objects.filter(project=project, is_active=True).values_list('user_id', 'role', 'unit', 'is_external', 'service_profession_id'))
                change_details = _log_team_changes(project, request.user, existing_snapshot, new_snapshot)
                change_summary = _notify_team_change(project, request.user, change_details)

                # 标记"配置项目团队"任务为已完成
                _complete_project_task(project, 'configure_team', actor=request.user)
                
                # 触发产值计算：配置项目团队
                if project.contract_amount and project.contract_amount > 0:
                    try:
                        from django.db import connection
                        # 检查产值记录表是否存在
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public' 
                                    AND table_name = 'settlement_output_value_record'
                                );
                            """)
                            table_exists = cursor.fetchone()[0]
                        
                        if table_exists:
                            from backend.apps.settlement_center.services import calculate_output_value
                            # 配置团队的责任人是项目经理
                            responsible_user = project.project_manager or request.user
                            calculate_output_value(project, 'configure_team', responsible_user=responsible_user)
                            logger.info('已为项目 %s 计算"配置项目团队"产值，责任人：%s', project.project_number, responsible_user.username)
                    except Exception as output_exc:
                        logger.warning('计算"配置项目团队"产值失败（可能是模块未初始化）: %s', str(output_exc))
                        # 产值计算失败不影响团队配置流程

                success_message = '团队配置成功！'
                if change_summary:
                    success_message += f' {change_summary}'
                messages.success(request, success_message)
                return redirect('production_pages:project_detail', project_id=project.id)
        except ValidationError as exc:
            message_body = format_html(
                '<div class="text-start"><strong>团队配置校验未通过：</strong><ul class="mb-0 ps-3">{}</ul></div>',
                format_html_join('', '<li>{}</li>', ((msg,) for msg in exc.messages))
            )
            messages.error(request, message_body)
            return redirect('production_pages:project_team', project_id=project.id)
        except Exception as e:
            messages.error(request, f'团队配置失败：{str(e)}')
    
    # 获取内部用户列表（按角色标签）
    collab_department_codes = {
        'EXTERNAL_TECH',
        'EXTERNAL_COST',
        'dept_consulting_coop_tech',
        'dept_consulting_coop_cost',
    }
    internal_department_codes = {
        'dept_internal_root',
        'dept_consulting_office',
        'dept_consulting_business',
        'dept_consulting_tech',
        'dept_consulting_cost',
    }

    internal_users = (
        User.objects.filter(user_type='internal')
        .select_related('department')
        .exclude(department__code__in=collab_department_codes)
    )
    if internal_department_codes:
        internal_users = internal_users.filter(
            Q(department__code__in=internal_department_codes) | Q(department__code__isnull=True)
        )

    project_managers = internal_users.filter(
        Q(position__icontains='项目负责人') | Q(position__icontains='项目经理')
    )
    professional_leaders = internal_users.filter(position__icontains='专业负责人')
    professional_engineers = internal_users.filter(position__icontains='专业工程师')
    technical_assistants = internal_users.filter(position__icontains='技术助理')
    cost_reviewers_civil = internal_users.filter(position__icontains='土建审核')
    cost_reviewers_installation = internal_users.filter(position__icontains='安装审核')
    cost_engineers_civil = internal_users.filter(position__icontains='土建造价')
    cost_engineers_installation = internal_users.filter(position__icontains='安装造价')

    external_collab_users = User.objects.filter(department__code__in=collab_department_codes)
    if not external_collab_users.exists():
        external_collab_users = User.objects.filter(
            department__name__icontains='合作'
        )

    external_leaders = external_collab_users.filter(position__icontains='负责人')
    external_engineers = external_collab_users.filter(position__icontains='工程师')
    external_cost_reviewers_civil = external_collab_users.filter(position__icontains='土建审核')
    external_cost_reviewers_installation = external_collab_users.filter(position__icontains='安装审核')
    external_cost_engineers_civil = external_collab_users.filter(position__icontains='土建造价')
    external_cost_engineers_installation = external_collab_users.filter(position__icontains='安装造价')

    profession_entries = []
    for profession in project.service_professions.all():
        assignments = project.team_members.filter(service_profession=profession, is_active=True)
        leader_options = _prefer_real_collaborators(_filter_candidates_by_profession(professional_leaders, profession, professional_engineers, internal_users))
        engineer_options = _prefer_real_collaborators(_filter_candidates_by_profession(professional_engineers, profession, professional_leaders, internal_users))

        external_leader_options = _prefer_real_collaborators(_filter_candidates_by_profession(external_leaders, profession, external_engineers, external_collab_users))
        external_engineer_options = _prefer_real_collaborators(_filter_candidates_by_profession(external_engineers, profession, external_leaders, external_collab_users))

        profession_entries.append({
            'profession': profession,
            'internal_leader_id': assignments.filter(role='professional_leader').values_list('user_id', flat=True).first(),
            'internal_engineer_ids': list(assignments.filter(role='engineer').values_list('user_id', flat=True)),
            'external_leader_id': assignments.filter(role='external_leader').values_list('user_id', flat=True).first(),
            'external_engineer_ids': list(assignments.filter(role='external_engineer').values_list('user_id', flat=True)),
            'leader_options': leader_options,
            'engineer_options': engineer_options,
            'external_leader_options': external_leader_options,
            'external_engineer_options': external_engineer_options,
        })

    support_assignments = project.team_members.filter(service_profession__isnull=True, is_active=True)
    selected_assistants = list(support_assignments.filter(role='technical_assistant').values_list('user_id', flat=True))
    selected_cost_reviewer_civil = list(support_assignments.filter(role='cost_reviewer_civil').values_list('user_id', flat=True))
    selected_cost_reviewer_installation = list(support_assignments.filter(role='cost_reviewer_installation').values_list('user_id', flat=True))
    selected_cost_engineer_civil = list(support_assignments.filter(role='cost_engineer_civil').values_list('user_id', flat=True))
    selected_cost_engineer_installation = list(support_assignments.filter(role='cost_engineer_installation').values_list('user_id', flat=True))
    selected_external_cost_reviewer_civil = list(support_assignments.filter(role='external_cost_reviewer_civil').values_list('user_id', flat=True))
    selected_external_cost_reviewer_installation = list(support_assignments.filter(role='external_cost_reviewer_installation').values_list('user_id', flat=True))
    selected_external_cost_engineer_civil = list(support_assignments.filter(role='external_cost_engineer_civil').values_list('user_id', flat=True))
    selected_external_cost_engineer_installation = list(support_assignments.filter(role='external_cost_engineer_installation').values_list('user_id', flat=True))

    active_members = project.team_members.filter(is_active=True).select_related('user', 'service_profession').order_by('unit', 'role')
    profession_total = len(profession_entries)
    profession_assigned = sum(1 for entry in profession_entries if entry.get('internal_leader_id'))
    engineer_total = sum(
        len(entry.get('internal_engineer_ids') or []) + len(entry.get('external_engineer_ids') or [])
        for entry in profession_entries
    )
    support_total = (
        len(selected_assistants)
        + len(selected_cost_engineer_civil)
        + len(selected_cost_engineer_installation)
        + len(selected_external_cost_engineer_civil)
        + len(selected_external_cost_engineer_installation)
    )
    stats_summary = {
        'profession_total': profession_total,
        'profession_assigned': profession_assigned,
        'engineer_total': engineer_total,
        'support_total': support_total,
        'member_total': active_members.count(),
    }
    support_counts = {
        'assistants': len(selected_assistants),
        'cost_internal': len(selected_cost_engineer_civil) + len(selected_cost_engineer_installation),
        'cost_external': len(selected_external_cost_engineer_civil) + len(selected_external_cost_engineer_installation),
        'reviewers': len(selected_cost_reviewer_civil) + len(selected_cost_reviewer_installation) + len(selected_external_cost_reviewer_civil) + len(selected_external_cost_reviewer_installation),
    }

    project_manager_display = _format_user_display(project.project_manager, '待分配')
    business_manager_display = _format_user_display(project.business_manager, '待分配')

    context = _with_nav({
        'project': project,
        'profession_entries': profession_entries,
        'project_managers': project_managers,
        'professional_leaders': professional_leaders,
        'professional_engineers': professional_engineers,
        'technical_assistants': technical_assistants,
        'cost_reviewers_civil': cost_reviewers_civil,
        'cost_reviewers_installation': cost_reviewers_installation,
        'cost_engineers_civil': cost_engineers_civil,
        'cost_engineers_installation': cost_engineers_installation,
        'external_leaders': external_leaders,
        'external_engineers': external_engineers,
        'external_cost_reviewers_civil': external_cost_reviewers_civil,
        'external_cost_reviewers_installation': external_cost_reviewers_installation,
        'external_cost_engineers_civil': external_cost_engineers_civil,
        'external_cost_engineers_installation': external_cost_engineers_installation,
        'selected_assistants': selected_assistants,
        'selected_cost_reviewer_civil': selected_cost_reviewer_civil,
        'selected_cost_reviewer_installation': selected_cost_reviewer_installation,
        'selected_cost_engineer_civil': selected_cost_engineer_civil,
        'selected_cost_engineer_installation': selected_cost_engineer_installation,
        'selected_external_cost_reviewer_civil': selected_external_cost_reviewer_civil,
        'selected_external_cost_reviewer_installation': selected_external_cost_reviewer_installation,
        'selected_external_cost_engineer_civil': selected_external_cost_engineer_civil,
        'selected_external_cost_engineer_installation': selected_external_cost_engineer_installation,
        'active_members': active_members,
        'stats_summary': stats_summary,
        'support_counts': support_counts,
        'project_manager_display': project_manager_display,
        'business_manager_display': business_manager_display,
    }, permission_set, 'project_team', request.user)
    return render(request, 'production_management/project_team.html', context)

@login_required
def project_list(request):
    """项目总览页面（原项目查询）"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有查看项目列表的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')

    # 过滤用户可访问的项目
    accessible_ids = _project_ids_user_can_access(request.user)
    projects = Project.objects.filter(id__in=accessible_ids).select_related('project_manager', 'business_manager', 'client', 'client_leader', 'design_leader', 'responsible_department', 'responsible_person', 'created_by')
    
    # 查询条件
    project_number = request.GET.get('project_number')
    project_name = request.GET.get('project_name')
    client_name = request.GET.get('client_name')
    # 服务类型：兼容单选和多选，安全处理空字符串
    raw_service_type = (request.GET.get('service_type') or '').strip()
    if raw_service_type:
        service_type_ids = [raw_service_type]
    else:
        service_type_ids = [v for v in request.GET.getlist('service_type') if (v or '').strip()]
    status_param = (request.GET.get('status') or '').strip()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if project_number:
        projects = projects.filter(project_number__icontains=project_number)
    if project_name:
        projects = projects.filter(name__icontains=project_name)
    if client_name:
        projects = projects.filter(client_company_name__icontains=client_name)
    if service_type_ids:
        # 过滤掉非数字，避免 ValueError
        valid_ids = []
        for v in service_type_ids:
            try:
                valid_ids.append(int(v))
            except (TypeError, ValueError):
                continue
        if valid_ids:
            projects = projects.filter(service_type_id__in=valid_ids)
    if date_from:
        projects = projects.filter(created_time__gte=date_from)
    if date_to:
        projects = projects.filter(created_time__lte=date_to)
    if status_param in {'draft', 'in_progress', 'completed', 'archived'}:
        projects = projects.filter(status=status_param)
    
    context = _with_nav({
        'projects': projects,
        'service_types': ServiceType.objects.order_by('order', 'id'),
        'selected_service_type_ids': service_type_ids,
        'selected_service_type_id': raw_service_type,
        'status_selected': status_param,
    }, permission_set, 'project_list', request.user, request=request)
    return render(request, 'production_management/project_list.html', context)

@login_required
def project_list_export(request):
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有导出项目列表的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')

    payload = build_project_dashboard_payload(
        request.user,
        permission_set,
        request.GET
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = '项目概览'

    headers = [
        '项目编号', '项目名称', '状态', '团队规模',
        '进度完成率 (%)', '质量评分', '风险评分', '健康指数'
    ]
    worksheet.append(headers)

    for metric in payload['project_metrics']:
        row = [
            metric['project_number'],
            metric['project_name'],
            metric['status'],
            metric['team_size'],
            metric['progress_percent'],
            metric['quality_score'],
            metric['risk_score'],
            metric['health_score'],
        ]

        worksheet.append(row)

    for column_cells in worksheet.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = max(length * 1.2, 12)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = timezone.now().strftime('project_dashboard_%Y%m%d_%H%M%S.xlsx')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related(
            'project_manager', 'business_manager', 'created_by', 'client', 'client_leader', 'design_leader', 'responsible_department', 'responsible_person'
        ).prefetch_related('service_professions', 'milestones', 'team_members__user'),
        id=project_id
    )

    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有查看项目详情的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _has_permission(permission_set, 'production_management.view_all') and not _user_is_project_member(request.user, project):
        messages.error(request, '您无权查看该项目详情。')
        return redirect('admin:index')

    team_manage_permitted = _has_permission(permission_set, 'production_management.configure_team')
    edit_permitted = _has_permission(permission_set, 'production_management.create')
    is_technical_manager = request.user.roles.filter(code='technical_manager').exists() or '技术部经理' in (request.user.position or '')

    created_by_display = _format_user_display(getattr(project, 'created_by', None), '—')
    project_manager_display = _format_user_display(project.project_manager, '待分配')
    business_manager_display = _format_user_display(project.business_manager, '待分配')

    milestones = list(project.milestones.all())
    service_timeline, service_completion = _build_service_timeline(project, milestones)
    if service_timeline:
        total_milestones = len(service_timeline)
        completed_milestones = len([stage for stage in service_timeline if stage["status"] == "completed"])
        progress_percent = service_completion
    else:
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.is_completed])
        progress_percent = int(completed_milestones / total_milestones * 100) if total_milestones else 0
        service_completion = progress_percent


    today = timezone.now().date()
    tasks = []
    base_start = project.start_date or (milestones[0].planned_date if milestones else today)
    base_end = project.end_date or (milestones[-1].planned_date if milestones else base_start)
    if base_start and base_end and base_end <= base_start:
        base_end = base_start + timedelta(days=30)
    if not base_start:
        base_start = today
    if not base_end:
        base_end = base_start + timedelta(days=30)
    total_span_days = max((base_end - base_start).days, 1)

    status_label_map = {
        'completed': '已完成',
        'in_progress': '进行中',
        'delayed': '已延迟',
    }
    status_class_map = {
        'completed': 'success',
        'in_progress': 'primary',
        'delayed': 'danger',
    }

    if project.start_date:
        previous_planned = project.start_date
    elif milestones and milestones[0].planned_date:
        previous_planned = milestones[0].planned_date - timedelta(days=7)
    else:
        previous_planned = today

    for index, milestone in enumerate(milestones):
        planned_start = previous_planned or milestone.planned_date or base_start
        planned_end = milestone.planned_date or planned_start
        if planned_end and planned_start and planned_end < planned_start:
            planned_start = planned_end
        actual_end = milestone.actual_date
        status = 'completed' if milestone.is_completed else 'in_progress'
        delay_days = 0
        if milestone.is_completed and actual_end and planned_end and actual_end > planned_end:
            status = 'delayed'
            delay_days = (actual_end - planned_end).days
        elif not milestone.is_completed and planned_end and today > planned_end:
            status = 'delayed'
            delay_days = (today - planned_end).days

        duration_days = max((planned_end - planned_start).days if planned_end and planned_start else 0, 1)
        timeline_offset = 0
        if planned_start:
            timeline_offset = max(0, (planned_start - base_start).days) / total_span_days * 100
        timeline_width = min(100, max(duration_days / total_span_days * 100, 4))

        tasks.append({
            'name': milestone.name,
            'planned_start': planned_start,
            'planned_end': planned_end,
            'actual_end': actual_end,
            'status': status,
            'status_label': status_label_map.get(status, status),
            'status_badge_class': status_class_map.get(status, 'secondary'),
            'delay_days': delay_days if delay_days > 0 else 0,
            'timeline_offset': round(timeline_offset, 2),
            'timeline_width': round(timeline_width, 2),
        })
        previous_planned = planned_end or previous_planned

    tasks_summary = {
        'completed': len([t for t in tasks if t['status'] == 'completed']),
        'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
        'delayed': len([t for t in tasks if t['status'] == 'delayed']),
    }
    total_tasks = sum(tasks_summary.values()) or 1
    tasks_summary['completion_rate'] = round(tasks_summary['completed'] / total_tasks * 100, 1)

    delayed_tasks = [task for task in tasks if task['status'] == 'delayed'][:5]
    upcoming_milestones = [
        {
            'name': milestone.name,
            'date': milestone.planned_date,
            'days_remaining': (milestone.planned_date - today).days if milestone.planned_date else None,
        }
        for milestone in milestones
        if not milestone.is_completed and milestone.planned_date and milestone.planned_date >= today
    ][:5]

    team_members = project.team_members.filter(is_active=True).select_related('user', 'service_profession')
    role_labels = dict(ProjectTeam.ROLE_CHOICES)
    team_summary = {}
    for member in team_members:
        unit_label = UNIT_LABELS.get(member.unit, '')
        role_label = role_labels.get(member.role, member.role)
        key = f"{member.unit}_{member.role}"
        display_label = f"{unit_label}-{role_label}" if unit_label else role_label
        team_summary.setdefault(key, {
            'label': display_label,
            'unit': unit_label,
            'members': [],
        })
        team_summary[key]['members'].append({
            'name': member.user.get_full_name() or member.user.username,
            'profession': member.service_profession.name if member.service_profession else '—',
        })

    professional_leaders = [entry for key, entry in team_summary.items() if 'professional_leader' in key]
    professional_leader_names = [m['name'] for entry in professional_leaders for m in entry['members']]

    risk_level_label = '低'
    risk_level_class = 'success'
    high_risk_items = []
    overdue_milestones = [m for m in milestones if not m.is_completed and m.planned_date and m.planned_date < today]
    if overdue_milestones:
        risk_level_label = '中'
        risk_level_class = 'warning'
    if len(overdue_milestones) > 3:
        risk_level_label = '高'
        risk_level_class = 'danger'

    for milestone in overdue_milestones[:5]:
        high_risk_items.append({
            'title': milestone.name,
            'category': '里程碑延迟',
            'level': '高' if risk_level_label == '高' else '中',
            'owner': project_manager_display,
            'days': (today - milestone.planned_date).days,
        })

    recent_documents = list(project.documents.select_related('uploaded_by').order_by('-uploaded_time')[:5])
    deliverables_required = Project.DELIVERABLES_MAP.get(project.service_type.code if project.service_type else '', [])
    deliverables_progress = []
    for item in deliverables_required:
        matched_doc = next((doc for doc in recent_documents if item in doc.name), None)
        deliverables_progress.append({
            'name': item,
            'completed': matched_doc is not None,
            'document': matched_doc,
        })

    activity_feed = []
    for milestone in milestones[:5]:
        if milestone.actual_date:
            activity_feed.append({
                'title': f"里程碑完成 · {milestone.name}",
                'time': milestone.actual_date.strftime('%Y-%m-%d'),
                'description': milestone.description or '里程碑已完成',
            })
    for doc in recent_documents:
        activity_feed.append({
            'title': f"文档上传 · {doc.name}",
            'time': doc.uploaded_time.strftime('%Y-%m-%d'),
            'description': doc.get_document_type_display(),
        })
    activity_feed = sorted(activity_feed, key=lambda x: x['time'], reverse=True)[:8]

    metrics = {
        'progress': {
            'percent': progress_percent,
            'completed': completed_milestones,
            'total': total_milestones,
            'summary': tasks_summary,
            'tasks': tasks,
            'delayed_tasks': delayed_tasks,
            'upcoming': upcoming_milestones,
            'milestones': [
                {
                    'name': stage['name'],
                    'date': stage['planned_start'].isoformat() if stage.get('planned_start') else '待定',
                    'is_completed': stage['status'] == 'completed',
                }
                for stage in service_timeline[:5]
            ],
        },
        'health': {
            'score': min(max(round(progress_percent, 1), 0), 100),
            'level_label': '良好' if progress_percent > 70 else '关注',
            'level_class': 'success' if progress_percent > 70 else 'warning',
        },
        'risk': {
            'level_label': risk_level_label,
            'level_class': risk_level_class,
            'high_count': len(high_risk_items),
            'items': high_risk_items,
        },
        'timeline': {
            'stages': service_timeline,
            'completion_rate': service_completion,
        },
        'team': {
            'professional_leaders': professional_leader_names,
            'summary': team_summary,
        },
        'activity': activity_feed,
    }

    launch_status_choices = dict(Project.LAUNCH_STATUS)
    launch_status_order = [code for code, _ in Project.LAUNCH_STATUS]
    current_launch_index = launch_status_order.index(project.launch_status) if project.launch_status in launch_status_order else -1
    status_timestamps = {
        'handover_pending': project.handover_submitted_time,
        'awaiting_drawings': project.handover_submitted_time,
        'precheck_in_progress': None,
        'changes_requested': project.drawing_precheck_completed_time,
        'ready_to_start': project.drawing_precheck_completed_time,
        'started': project.start_notice_sent_time,
    }

    launch_timeline = []
    for idx, status_code in enumerate(launch_status_order):
        launch_timeline.append({
            'code': status_code,
            'label': launch_status_choices.get(status_code, status_code),
            'is_current': idx == current_launch_index,
            'is_completed': idx < current_launch_index,
            'timestamp': status_timestamps.get(status_code),
        })

    drawing_status_class_map = {
        'submitted': 'secondary',
        'in_review': 'info',
        'changes_requested': 'warning',
        'approved': 'success',
        'cancelled': 'secondary',
    }
    review_result_class_map = {
        'pending': 'secondary',
        'approved': 'success',
        'changes_requested': 'warning',
    }

    drawing_submissions_queryset = project.drawing_submissions.select_related(
        'submitter', 'latest_review'
    ).prefetch_related(
        'files', 'reviews', 'reviews__reviewer'
    ).order_by('-submitted_time')

    drawing_submissions_payload = []
    for submission in drawing_submissions_queryset:
        files_payload = [
            {
                'id': file.id,
                'name': file.name,
                'category_label': file.get_category_display(),
                'url': file.file.url if file.file else '',
                'uploaded_time': file.uploaded_time,
            }
            for file in submission.files.all()
        ]
        reviews_payload = [
            {
                'id': review.id,
                'result': review.result,
                'result_label': review.get_result_display(),
                'result_class': review_result_class_map.get(review.result, 'secondary'),
                'comment': review.comment,
                'reviewer_name': _format_user_display(review.reviewer, '—'),
                'reviewed_time': review.reviewed_time,
            }
            for review in submission.reviews.all()
        ]
        latest_review_payload = None
        if submission.latest_review_id:
            latest_review = submission.latest_review
            latest_review_payload = {
                'result': latest_review.result,
                'result_label': latest_review.get_result_display(),
                'result_class': review_result_class_map.get(latest_review.result, 'secondary'),
                'reviewer_name': _format_user_display(latest_review.reviewer, '—'),
                'reviewed_time': latest_review.reviewed_time,
            }
        drawing_submissions_payload.append({
            'id': submission.id,
            'title': submission.title,
            'version': submission.version,
            'description': submission.description,
            'status': submission.status,
            'status_label': submission.get_status_display(),
            'status_class': drawing_status_class_map.get(submission.status, 'secondary'),
            'submitter_name': _format_user_display(submission.submitter, '—'),
            'submitter_role': submission.submitter_role or '',
            'submitted_time': submission.submitted_time,
            'review_deadline': submission.review_deadline,
            'latest_review': latest_review_payload,
            'files': files_payload,
            'reviews': reviews_payload,
            'client_notified': submission.client_notified,
            'client_notification_channel': submission.client_notification_channel,
            'client_notified_time': submission.client_notified_time,
        })

    start_notices_queryset = project.start_notices.select_related(
        'created_by', 'recipient_user', 'submission'
    ).order_by('-created_time')

    start_notice_status_class_map = {
        'pending': 'secondary',
        'sent': 'primary',
        'failed': 'danger',
        'acknowledged': 'success',
    }
    start_notices_payload = [
        {
            'id': notice.id,
            'subject': notice.subject,
            'message': notice.message,
            'channel': notice.get_channel_display(),
            'status': notice.status,
            'status_class': start_notice_status_class_map.get(notice.status, 'secondary'),
            'status_label': notice.get_status_display(),
            'created_time': notice.created_time,
            'sent_time': notice.sent_time,
            'acknowledged_time': notice.acknowledged_time,
            'failure_reason': notice.failure_reason,
            'created_by': _format_user_display(notice.created_by, '—'),
            'recipient_name': notice.recipient_name or _format_user_display(notice.recipient_user, '—'),
            'recipient_phone': notice.recipient_phone,
            'recipient_email': notice.recipient_email,
            'submission_id': notice.submission_id,
            'submission_title': notice.submission.title if notice.submission else '',
        }
        for notice in start_notices_queryset
    ]
    flow_step_labels = dict(Project.FLOW_STEPS)
    flow_step_order = [code for code, _ in Project.FLOW_STEPS]
    current_flow_index = flow_step_order.index(project.flow_step) if project.flow_step in flow_step_order else -1
    flow_steps_payload = []
    for idx_step, (code, label) in enumerate(Project.FLOW_STEPS):
        flow_steps_payload.append({
            'code': code,
            'label': label,
            'status': 'completed' if idx_step < current_flow_index else ('current' if idx_step == current_flow_index else 'upcoming'),
        })
    next_flow_label = None
    if 0 <= current_flow_index < len(flow_step_order) - 1:
        next_flow_label = flow_step_labels.get(flow_step_order[current_flow_index + 1])
    flow_logs_payload = [
        {
            'id': log.id,
            'action': log.action,
            'action_label': dict(ProjectFlowLog.ACTION_CHOICES).get(log.action, log.action),
            'from_label': flow_step_labels.get(log.from_step, log.from_step or '—'),
            'to_label': flow_step_labels.get(log.to_step, log.to_step or '—'),
            'notes': log.notes,
            'operator': _format_user_display(log.actor, '系统'),
            'time': log.created_time,
        }
        for log in project.flow_logs.select_related('actor').order_by('-created_time')[:8]
    ]
    can_operate_flow = (
        _has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
        or project.project_manager_id == request.user.id
        or project.business_manager_id == request.user.id
        or _user_is_project_member(request.user, project)
    )
    available_flow_actions = []
    if can_operate_flow:
        for key, config in PROJECT_FLOW_ACTIONS.items():
            if project.flow_step in config.get('from', []):
                available_flow_actions.append({'key': key, 'label': config.get('label', key)})


    is_project_manager = project.project_manager_id == request.user.id
    is_business_manager = project.business_manager_id == request.user.id

    can_submit_drawings = _has_permission(
        permission_set,
        'production_management.create',
        'production_management.configure_team',
        'production_management.view_all'
    ) or is_project_manager or is_business_manager or _user_is_project_member(request.user, project)

    can_review_drawings = _has_permission(
        permission_set,
        'production_management.configure_team',
        'production_management.view_all'
    ) or is_project_manager

    can_manage_start_notice = _has_permission(
        permission_set,
        'production_management.configure_team',
        'production_management.view_all'
    ) or is_project_manager
    is_project_manager = project.project_manager_id == request.user.id
    can_client_upload_pre_docs = (
        _user_matches_role(request.user, project, 'client_lead') or
        _user_matches_role(request.user, project, 'client_engineer') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    can_submit_design_reply = (
        _user_matches_role(request.user, project, 'design_lead') or
        _user_matches_role(request.user, project, 'design_engineer') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    can_manage_meeting_log = (
        _has_permission(permission_set, 'production_management.configure_team') or
        is_project_manager or
        is_business_manager
    )
    can_design_upload = can_submit_design_reply
    can_internal_verify = (
        _has_permission(permission_set, 'production_management.configure_team') or
        is_project_manager or
        _user_matches_role(request.user, project, 'professional_leader') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    can_client_confirm_outcome = (
        _user_matches_role(request.user, project, 'client_lead') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    show_risk_section = (
        getattr(request.user, 'user_type', 'internal') == 'internal'
        or _has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
    )

    active_tasks_queryset = project.tasks.filter(
        status__in=ProjectTask.ACTIVE_STATUSES
    ).select_related('assigned_to').order_by('due_time', 'created_time')
    task_payload = []
    for task in active_tasks_queryset:
        assigned_user = task.assigned_to
        is_mine = bool(
            (assigned_user and assigned_user.id == request.user.id)
            or _user_matches_role(request.user, project, task.assigned_role)
        )
        task_payload.append({
            'id': task.id,
            'task_type': task.task_type,
            'task_type_label': task.get_task_type_display(),
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'status_label': task.get_status_display(),
            'due_time': task.due_time,
            'assigned_role': task.assigned_role,
            'assigned_role_label': ROLE_LABELS.get(task.assigned_role, task.assigned_role),
            'assigned_to_name': _format_user_display(assigned_user, '待绑定') if assigned_user else ('待绑定' if task.assigned_role else '—'),
            'assigned_to_id': assigned_user.id if assigned_user else None,
            'is_mine': is_mine,
        })

    task_status_counts = {status: 0 for status, _ in ProjectTask.STATUS_CHOICES}
    for entry in project.tasks.values('status').annotate(total=Count('id')):
        task_status_counts[entry['status']] = entry['total']

    context = _with_nav({
        'project': project,
        'metrics': metrics,
        'created_by_display': created_by_display,
        'project_manager_display': project_manager_display,
        'business_manager_display': business_manager_display,
        'team_manage_permitted': team_manage_permitted,
        'edit_permitted': edit_permitted,
        'read_only': _is_project_readonly(permission_set),
        'recent_documents': recent_documents,
        'deliverables_progress': deliverables_progress,
        'launch': {
            'status_code': project.launch_status,
            'status_label': launch_status_choices.get(project.launch_status, '未定义'),
            'timeline': launch_timeline,
            'status_choices': launch_status_choices,
        },
        'drawing_submissions': drawing_submissions_payload,
        'drawing_status_class_map': drawing_status_class_map,
        'review_result_class_map': review_result_class_map,
        'start_notices': start_notices_payload,
        'start_notice_status_class_map': start_notice_status_class_map,
        'drawing_permissions': {
            'can_submit': can_submit_drawings,
            'can_review': can_review_drawings,
            'can_manage_notice': can_manage_start_notice,
        },
        'quick_links': {
            'client_upload_pre_docs': can_client_upload_pre_docs,
            'complete_info': is_project_manager,
            'design_reply': can_submit_design_reply,
            'meeting_log': can_manage_meeting_log,
            'design_upload': can_design_upload,
            'internal_verify': can_internal_verify,
            'client_confirm': can_client_confirm_outcome,
        },
        'client_upload': {
            'can_submit': can_client_upload_pre_docs,
            'should_prompt': can_client_upload_pre_docs and project.launch_status in {'handover_pending', 'awaiting_drawings'},
        },
        'task_panel': {
            'active': task_payload,
            'mine': [task for task in task_payload if task['is_mine']],
            'status_counts': task_status_counts,
        },
        'flow': {
            'current_code': project.flow_step,
            'current_label': flow_step_labels.get(project.flow_step, project.flow_step),
            'steps': flow_steps_payload,
            'deadline': project.flow_deadline,
            'started_time': project.flow_step_started_time,
            'next_label': next_flow_label,
            'logs': flow_logs_payload,
            'can_operate': can_operate_flow,
            'available_actions': available_flow_actions,
            'action_url': reverse('production_pages:project_flow_action', args=[project.id]),
        },
        'client_contact': {
            'name': project.client_contact_person,
            'phone': project.client_phone,
            'email': project.client_email,
        },
        'show_risk_section': show_risk_section,
        'drawing_file_categories': [
            {'value': value, 'label': label}
            for value, label in ProjectDrawingFile.FILE_CATEGORIES
        ],
        'review_result_choices': [
            {'value': value, 'label': label}
            for value, label in ProjectDrawingReview.RESULT_CHOICES
        ],
        'start_notice_channels': [
            {'value': value, 'label': label}
            for value, label in ProjectStartNotice.CHANNEL_CHOICES
        ],
        'approved_drawing_submissions': [
            {'id': submission['id'], 'title': submission['title']}
            for submission in drawing_submissions_payload
            if submission['status'] == 'approved'
        ],
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_detail.html', context)


@login_required
@require_http_methods(['POST'])
def project_flow_action(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
            or project.project_manager_id == request.user.id
            or project.business_manager_id == request.user.id
            or _user_is_project_member(request.user, project)):
        return JsonResponse({'success': False, 'message': '您没有权限执行该操作。'}, status=403)

    action = request.POST.get('action')
    config = PROJECT_FLOW_ACTIONS.get(action)
    if not config:
        return JsonResponse({'success': False, 'message': '不支持的操作类型。'}, status=400)

    allowed_from = config.get('from', [])
    if project.flow_step not in allowed_from:
        return JsonResponse({'success': False, 'message': '当前步骤不允许执行该操作。'}, status=400)

    now = timezone.now()
    payload = dict(project.flow_payload or {})
    timestamp_key = config.get('payload_timestamp_key')
    if timestamp_key:
        payload[timestamp_key] = now.isoformat()

    deadline = None
    if config.get('deadline_hours'):
        deadline = now + timedelta(hours=config['deadline_hours'])

    notes = (request.POST.get('note') or '').strip()
    project.advance_flow(
        config.get('to', project.flow_step),
        deadline=deadline,
        payload=payload,
        actor=request.user,
        notes=notes or config.get('label', ''),
    )
    project.refresh_from_db(fields=['flow_step', 'flow_deadline', 'flow_step_started_time'])
    _apply_flow_task_automation(project, action, request.user)

    return JsonResponse({
        'success': True,
        'step': {
            'code': project.flow_step,
            'label': dict(Project.FLOW_STEPS).get(project.flow_step, project.flow_step),
        },
        'deadline': project.flow_deadline.isoformat() if project.flow_deadline else None,
        'started_time': project.flow_step_started_time.isoformat() if project.flow_step_started_time else None,
    })


@login_required
@require_http_methods(['POST'])
def project_task_action(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    permission_set = get_user_permission_codes(request.user)
    if not (
        task.assigned_to_id == request.user.id
        or _user_matches_role(request.user, project, task.assigned_role)
        or _has_permission(permission_set, 'production_management.view_all')
    ):
        messages.error(request, '您没有权限更新该任务。')
        return redirect(reverse('production_pages:project_detail', args=[project.id]))

    action = request.POST.get('action', 'complete')
    now = timezone.now()
    if action == 'complete':
        if task.status not in ProjectTask.ACTIVE_STATUSES:
            messages.info(request, '任务已完成，无需重复操作。')
        else:
            task.status = 'completed'
            task.completed_time = now
            task.completed_by = request.user
            task.save(update_fields=['status', 'completed_time', 'completed_by', 'updated_time'])
            _handle_task_followups(task, request.user)
            messages.success(request, '任务已标记完成。')
    elif action == 'cancel' and _has_permission(permission_set, 'production_management.configure_team'):
        task.status = 'cancelled'
        task.cancelled_time = now
        task.cancelled_by = request.user
        task.save(update_fields=['status', 'cancelled_time', 'cancelled_by', 'updated_time'])
        messages.success(request, '任务已取消。')
    else:
        messages.error(request, '不支持的任务操作。')

    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}#section-flow")


@login_required
def project_task_dashboard(request):
    permission_set = get_user_permission_codes(request.user)
    projects_queryset = Project.objects.select_related('project_manager', 'business_manager', 'client', 'client_leader', 'design_leader', 'responsible_department', 'responsible_person', 'created_by')
    projects = _filter_projects_for_user(projects_queryset, request.user, permission_set)

    tasks_queryset = ProjectTask.objects.select_related(
        'project',
        'project__project_manager',
        'assigned_to',
    ).order_by('due_time', 'created_time')

    user_active_tasks = []
    for task in tasks_queryset:
        if task.status not in ProjectTask.ACTIVE_STATUSES:
            continue
        if not task.project:
            continue
        if _task_visible_to_user(task, request.user, task.project):
            user_active_tasks.append(task)

    recent_completed = ProjectTask.objects.filter(
        status='completed',
        completed_by=request.user,
    ).select_related('project').order_by('-completed_time')[:6]

    def _serialize_task(task):
        project = task.project
        return {
            'id': task.id,
            'title': task.title,
            'project_name': project.name if project else '关联项目',
            'project_number': project.project_number if project else '',
            'status': task.status,
            'status_label': task.get_status_display(),
            'due_time': task.due_time,
            'completed_time': task.completed_time,
            'assigned_role_label': ROLE_LABELS.get(task.assigned_role, task.assigned_role),
            'action_url': reverse('project:project_task_action', args=[project.id, task.id]) if project else '#',
            'project_url': reverse('production_pages:project_detail', args=[project.id]) if project else '#',
            'description': task.description,
        }

    task_sections = {
        'client_side': [],
        'design_side': [],
        'internal': [],
    }
    for task in user_active_tasks:
        payload = _serialize_task(task)
        unit = task.target_unit or ProjectTeam.ROLE_UNIT_MAP.get(task.assigned_role, '')
        if unit == 'client_side':
            task_sections['client_side'].append(payload)
        elif unit == 'design_side':
            task_sections['design_side'].append(payload)
        else:
            task_sections['internal'].append(payload)

    completed_payload = [_serialize_task(task) for task in recent_completed]

    counts = {
        'total': len(user_active_tasks),
        'client': len(task_sections['client_side']),
        'design': len(task_sections['design_side']),
        'internal': len(task_sections['internal']),
    }

    context = _with_nav({
        'task_sections': task_sections,
        'completed_tasks': completed_payload,
        'task_counts': counts,
        'projects': projects.order_by('-updated_time')[:6],
        'is_external_user': getattr(request.user, 'user_type', 'internal') != 'internal',
    }, permission_set, 'project_tasks', request.user)
    return render(request, 'production_management/task_dashboard.html', context)


@login_required
def project_design_reply(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问设计方回复的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_submit = (
        _user_matches_role(request.user, project, 'design_lead') or
        _user_matches_role(request.user, project, 'design_engineer') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    replies = ProjectDesignReply.objects.filter(project=project).select_related('submitted_by')
    # available_opinions = list(project.opinions.order_by('-created_at')[:200])  # 已删除生产质量模块
    available_opinions = []  # 已删除生产质量模块

    if request.method == 'POST':
        if not can_submit:
            messages.error(request, '您没有提交回复的权限。')
            return redirect('production_pages:project_design_reply', project_id=project.id)
        opinion_id = request.POST.get('opinion_id')
        # opinion = None  # 已删除生产质量模块
        # if opinion_id:
        #     opinion = project.opinions.filter(id=opinion_id).first()
        # if not opinion:
        #     messages.error(request, '请选择需要回复的具体意见。')
        #     return redirect('production_pages:project_design_reply', project_id=project.id)
        issue_title = (request.POST.get('issue_title') or '').strip()
        status = request.POST.get('status') or 'agree'
        response_detail = (request.POST.get('response_detail') or '').strip()
        if not issue_title:
            messages.error(request, '请填写事项 / 问题。')
            return redirect('production_pages:project_design_reply', project_id=project.id)
        reply = ProjectDesignReply.objects.create(
            project=project,
            opinion_id=int(opinion_id) if opinion_id and opinion_id.isdigit() else None,
            issue_title=issue_title,
            status=status if status in dict(ProjectDesignReply.REPLY_STATUS_CHOICES) else 'agree',
            response_detail=response_detail,
            submitted_by=request.user,
        )
        _complete_project_task(project, 'design_reply_opinions', actor=request.user)
        _ensure_project_task(project, 'client_confirm_meeting', created_by=request.user)
        messages.success(request, '回复已提交。')
        return redirect('production_pages:project_design_reply', project_id=project.id)

    context = _with_nav({
        'project': project,
        'replies': replies,
        'status_choices': ProjectDesignReply.REPLY_STATUS_CHOICES,
        'can_submit': can_submit,
        'opinions': available_opinions,
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_design_reply.html', context)


@login_required
def project_meeting_log(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问会议记录的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_manage = (
        _has_permission(permission_set, 'production_management.configure_team') or
        project.project_manager_id == request.user.id or
        project.business_manager_id == request.user.id
    )

    records = ProjectMeetingRecord.objects.filter(project=project).select_related('created_by')
    # available_opinions = list(project.opinions.order_by('-created_at')[:200])  # 已删除生产质量模块
    available_opinions = []  # 已删除生产质量模块

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'meeting')
        if not can_manage:
            messages.error(request, '您没有记录会议的权限。')
            return redirect('production_pages:project_meeting_log', project_id=project.id)
        if form_type == 'decision':
            meeting_id = request.POST.get('meeting_id')
            opinion_id = request.POST.get('opinion_id')
            decision_value = request.POST.get('decision') or 'pending'
            meeting = ProjectMeetingRecord.objects.filter(project=project, id=meeting_id).first()
            # opinion = project.opinions.filter(id=opinion_id).first()  # 已删除生产质量模块
            if not meeting or not opinion_id:
                messages.error(request, '请选择有效的会议与意见条目。')
                return redirect('production_pages:project_meeting_log', project_id=project.id)
            client_comment = (request.POST.get('decision_client_comment') or '').strip()
            design_comment = (request.POST.get('decision_design_comment') or '').strip()
            consultant_comment = (request.POST.get('decision_consultant_comment') or '').strip()
            decision_obj, created = ProjectMeetingDecision.objects.update_or_create(
                meeting=meeting,
                opinion_id=int(opinion_id) if opinion_id and opinion_id.isdigit() else None,
                defaults={
                    'decision': decision_value if decision_value in dict(ProjectMeetingDecision.DECISION_CHOICES) else 'pending',
                    'client_comment': client_comment,
                    'design_comment': design_comment,
                    'consultant_comment': consultant_comment,
                }
            )
            if decision_obj.decision in {'agree', 'partial'}:
                _ensure_project_task(project, 'design_upload_revisions', created_by=request.user)
            elif decision_obj.decision == 'reject':
                _ensure_project_task(project, 'design_reply_opinions', created_by=request.user)
            messages.success(request, '已记录该意见的会议结论。')
            return redirect('production_pages:project_meeting_log', project_id=project.id)
        else:
            topic = (request.POST.get('topic') or '').strip()
            meeting_date = request.POST.get('meeting_date') or timezone.now().date()
            client_decision = (request.POST.get('client_decision') or '').strip()
            design_decision = (request.POST.get('design_decision') or '').strip()
            consultant_decision = (request.POST.get('consultant_decision') or '').strip()
            conclusions = (request.POST.get('conclusions') or '').strip()
            if not topic:
                messages.error(request, '请填写会议主题。')
                return redirect('production_pages:project_meeting_log', project_id=project.id)
            try:
                meeting_date_value = datetime.datetime.fromisoformat(str(meeting_date)).date()
            except ValueError:
                meeting_date_value = timezone.now().date()
            ProjectMeetingRecord.objects.create(
                project=project,
                meeting_date=meeting_date_value,
                topic=topic,
                client_decision=client_decision,
                design_decision=design_decision,
                consultant_decision=consultant_decision,
                conclusions=conclusions,
                created_by=request.user,
            )
            _complete_project_task(project, 'client_confirm_meeting', actor=request.user)
            _complete_project_task(project, 'organize_tripartite_meeting', actor=request.user)
            _ensure_project_task(project, 'design_upload_revisions', created_by=request.user)
            messages.success(request, '会议记录已保存。')
            return redirect('production_pages:project_meeting_log', project_id=project.id)

    context = _with_nav({
        'project': project,
        'records': records,
        'can_manage': can_manage,
        'today': timezone.now().date(),
        'opinions': available_opinions,
        'decision_choices': ProjectMeetingDecision.DECISION_CHOICES,
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_meeting_log.html', context)


@login_required
def project_client_pre_docs(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问资料上传页面的权限。', 'production_management.view_assigned', 'production_management.view_all'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_submit = (
        _user_matches_role(request.user, project, 'client_lead') or
        _user_matches_role(request.user, project, 'client_engineer') or
        _has_permission(permission_set, 'production_management.view_all')
    )

    drawing_status_class_map = {
        'submitted': 'secondary',
        'in_review': 'info',
        'changes_requested': 'warning',
        'approved': 'success',
        'cancelled': 'secondary',
    }
    review_result_class_map = {
        'pending': 'secondary',
        'approved': 'success',
        'changes_requested': 'warning',
    }

    submissions_queryset = project.drawing_submissions.select_related('submitter', 'latest_review').prefetch_related('files').order_by('-submitted_time')[:12]
    submissions = []
    for submission in submissions_queryset:
        submissions.append({
            'id': submission.id,
            'title': submission.title,
            'version': submission.version,
            'status': submission.status,
            'status_label': submission.get_status_display(),
            'status_class': drawing_status_class_map.get(submission.status, 'secondary'),
            'submitted_time': submission.submitted_time,
            'submitter': _format_user_display(submission.submitter, '—'),
            'latest_review': {
                'label': submission.latest_review.get_result_display() if submission.latest_review else '待审核',
                'class': review_result_class_map.get(submission.latest_review.result if submission.latest_review else 'pending', 'secondary'),
                'time': submission.latest_review.reviewed_time if getattr(submission.latest_review, 'reviewed_time', None) else None,
            } if submission.latest_review else None,
            'files': [
                {
                    'id': file.id,
                    'name': file.name,
                    'url': file.file.url if file.file else '',
                    'category_label': file.get_category_display(),
                }
                for file in submission.files.all()
            ],
        })

    relevant_task_types = ['client_upload_pre_docs', 'client_resubmit_pre_docs', 'internal_precheck_docs']
    status_label_map = dict(ProjectTask.STATUS_CHOICES)
    task_type_label_map = dict(ProjectTask.TASK_TYPE_CHOICES)
    client_tasks = [{
        'id': task.id,
        'title': task.title or task_type_label_map.get(task.task_type, task.task_type),
        'status': task.status,
        'status_label': status_label_map.get(task.status, task.status),
        'created_time': task.created_time,
        'due_time': task.due_time,
        'assigned_to': _format_user_display(task.assigned_to, task.assigned_role),
        'task_type_label': task_type_label_map.get(task.task_type, task.task_type),
    } for task in project.tasks.filter(task_type__in=relevant_task_types).order_by('-created_time')[:6]]

    context = _with_nav({
        'project': project,
        'can_submit': can_submit,
        'submissions': submissions,
        'client_tasks': client_tasks,
        'upload_action_url': reverse('production_pages:project_drawing_submit', args=[project.id]),
        'drawing_file_categories': [
            {'value': value, 'label': label}
            for value, label in ProjectDrawingFile.FILE_CATEGORIES
        ],
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_client_pre_docs.html', context)


@login_required
def project_design_upload(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问改图上传页面的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_submit = (
        _user_matches_role(request.user, project, 'design_lead') or
        _user_matches_role(request.user, project, 'design_engineer') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    design_documents = project.documents.filter(document_type='design').order_by('-uploaded_time')[:10]

    if request.method == 'POST':
        if not can_submit:
            messages.error(request, '您没有上传改图的权限。')
            return redirect('production_pages:project_design_upload', project_id=project.id)
        files = request.FILES.getlist('files')
        note = (request.POST.get('note') or '').strip()
        if not files and not note:
            messages.error(request, '请上传附件或填写改图说明。')
            return redirect('production_pages:project_design_upload', project_id=project.id)
        try:
            with transaction.atomic():
                for uploaded in files:
                    ProjectDocument.objects.create(
                        project=project,
                        name=uploaded.name,
                        document_type='design',
                        file=uploaded,
                        description=note,
                        uploaded_by=request.user,
                    )
                ProjectFlowLog.objects.create(
                    project=project,
                    action='note',
                    actor=request.user,
                    notes=f'设计方上传改图：{note or "已上传附件"}',
                    metadata={'category': 'design_upload'},
                )
            _complete_project_task(project, 'design_upload_revisions', actor=request.user)
            _ensure_project_task(project, 'internal_verify_revisions', created_by=request.user)
            messages.success(request, '改图信息已提交，等待我方核图。')
            return redirect('production_pages:project_design_upload', project_id=project.id)
        except Exception as exc:
            logger.exception('设计方上传改图失败: %s', exc)
            messages.error(request, f'上传失败：{exc}')

    context = _with_nav({
        'project': project,
        'design_documents': design_documents,
        'can_submit': can_submit,
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_design_upload.html', context)


@login_required
def project_internal_verify(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问核图页面的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_verify = (
        _has_permission(permission_set, 'production_management.configure_team') or
        project.project_manager_id == request.user.id or
        _user_matches_role(request.user, project, 'professional_leader') or
        _has_permission(permission_set, 'production_management.view_all')
    )
    design_documents = project.documents.filter(document_type='design').order_by('-uploaded_time')[:10]

    if request.method == 'POST':
        if not can_verify:
            messages.error(request, '您没有执行核图的权限。')
            return redirect('production_pages:project_internal_verify', project_id=project.id)
        result = request.POST.get('result') or 'approved'
        note = (request.POST.get('note') or '').strip()
        ProjectFlowLog.objects.create(
            project=project,
            action='note',
            actor=request.user,
            notes=f'核图处理：{dict([("approved","全部修改"),("changes","需修改")]).get(result, "核图")} {note}',
            metadata={'category': 'internal_verify', 'result': result},
        )
        if result == 'approved':
            _complete_project_task(project, 'internal_verify_revisions', actor=request.user)
            _ensure_project_task(project, 'client_confirm_outcome', created_by=request.user)
            messages.success(request, '核图已完成，等待甲方确认。')
        else:
            _ensure_project_task(project, 'design_upload_revisions', created_by=request.user)
            messages.warning(request, '已退回设计方补充改图。')
        return redirect('production_pages:project_internal_verify', project_id=project.id)

    context = _with_nav({
        'project': project,
        'design_documents': design_documents,
        'can_verify': can_verify,
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_internal_verify.html', context)


@login_required
def project_client_confirm_outcome(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问成果确认页面的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    if not _user_is_project_member(request.user, project):
        messages.error(request, '您无权访问该项目。')
        return redirect('admin:index')

    can_confirm = (
        _user_matches_role(request.user, project, 'client_lead') or
        _has_permission(permission_set, 'production_management.view_all')
    )

    if request.method == 'POST':
        if not can_confirm:
            messages.error(request, '您没有确认成果的权限。')
            return redirect('production_pages:project_client_confirm_outcome', project_id=project.id)
        result = request.POST.get('result') or 'accepted'
        comment = (request.POST.get('comment') or '').strip()
        ProjectFlowLog.objects.create(
            project=project,
            action='note',
            actor=request.user,
            notes=f'甲方成果确认：{dict([("accepted","确认通过"),("changes","需修改")]).get(result, "确认")} {comment}',
            metadata={'category': 'client_confirm', 'result': result},
        )
        if result == 'accepted':
            _complete_project_task(project, 'client_confirm_outcome', actor=request.user)
            project.status = 'completed'
            if not project.actual_end_date:
                project.actual_end_date = timezone.now().date()
            project.save(update_fields=['status', 'actual_end_date'])
            messages.success(request, '已确认成果，项目进入收尾。')
        else:
            _ensure_project_task(project, 'internal_verify_revisions', created_by=request.user)
            messages.warning(request, '已退回我方继续核图/整改。')
        return redirect('production_pages:project_client_confirm_outcome', project_id=project.id)

    context = _with_nav({
        'project': project,
        'can_confirm': can_confirm,
    }, permission_set, 'project_list', request.user)
    return render(request, 'production_management/project_client_confirm_outcome.html', context)


@login_required
@require_http_methods(['POST'])
def project_drawing_submit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.create', 'production_management.configure_team', 'production_management.view_all')
            or _user_is_project_member(request.user, project)
            or project.project_manager_id == request.user.id
            or project.business_manager_id == request.user.id):
        messages.error(request, '您没有提交图纸的权限。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    title = (request.POST.get('title') or '').strip()
    if not title:
        messages.error(request, '请填写图纸提交标题。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    version = (request.POST.get('version') or '').strip()
    description = (request.POST.get('description') or '').strip()
    submitter_role = (request.POST.get('submitter_role') or '').strip() or getattr(request.user, 'position', '')
    review_deadline_str = request.POST.get('review_deadline')
    review_deadline = None
    if review_deadline_str:
        try:
            review_deadline = datetime.datetime.fromisoformat(review_deadline_str)
        except ValueError:
            messages.error(request, '预审截止时间格式不正确，请使用有效的日期时间。')
            return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    files = request.FILES.getlist('files')
    file_category = request.POST.get('file_category') or 'general'

    with transaction.atomic():
        submission = ProjectDrawingSubmission.objects.create(
            project=project,
            title=title,
            version=version,
            description=description,
            submitter=request.user,
            submitter_role=submitter_role,
            review_deadline=review_deadline,
            metadata={'source': 'manual_form'},
        )
        for uploaded in files:
            ProjectDrawingFile.objects.create(
                submission=submission,
                name=uploaded.name,
                category=file_category if file_category in dict(ProjectDrawingFile.FILE_CATEGORIES) else 'general',
                file=uploaded,
                uploaded_by=request.user,
                metadata={'source': 'manual_form'},
            )
        project.launch_status = 'precheck_in_progress'
        project.launch_status_updated_time = timezone.now()
        if not project.handover_submitted_time:
            project.handover_submitted_time = project.launch_status_updated_time
        project.save(update_fields=['launch_status', 'launch_status_updated_time', 'handover_submitted_time'])

    _complete_project_task(project, 'client_upload_pre_docs', actor=request.user)
    _complete_project_task(project, 'client_resubmit_pre_docs', actor=request.user)
    _ensure_project_task(
        project,
        'internal_precheck_docs',
        created_by=request.user,
        assigned_to=project.project_manager or request.user,
    )

    messages.success(request, '图纸提交已创建，预审流程开始。')
    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")


@login_required
@require_http_methods(['POST'])
def project_drawing_review(request, project_id, submission_id):
    project = get_object_or_404(Project, id=project_id)
    submission = get_object_or_404(ProjectDrawingSubmission, id=submission_id, project=project)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
            or project.project_manager_id == request.user.id
            or _user_is_project_member(request.user, project)):
        messages.error(request, '您没有执行预审的权限。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    result = request.POST.get('result')
    allowed_results = {value for value, _ in ProjectDrawingReview.RESULT_CHOICES}
    if result not in allowed_results:
        messages.error(request, '请选择有效的预审结果。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    comment = (request.POST.get('comment') or '').strip()
    now = timezone.now()

    with transaction.atomic():
        review = ProjectDrawingReview.objects.create(
            submission=submission,
            reviewer=request.user,
            result=result,
            comment=comment,
            metadata={'source': 'manual_form'},
        )
        submission.latest_review = review
        submission_updated_fields = ['latest_review']
        project_updated_fields = ['launch_status', 'launch_status_updated_time']
        submission.status = 'in_review'
        project.launch_status = 'precheck_in_progress'

        if result == 'approved':
            submission.status = 'approved'
            project.launch_status = 'ready_to_start'
            project.drawing_precheck_completed_time = now
            project_updated_fields.append('drawing_precheck_completed_time')
        elif result == 'changes_requested':
            submission.status = 'changes_requested'
            project.launch_status = 'changes_requested'

        submission_updated_fields.append('status')
        submission.save(update_fields=submission_updated_fields)
        project.launch_status_updated_time = now
        project.save(update_fields=project_updated_fields)

    _complete_project_task(project, 'internal_precheck_docs', actor=request.user)
    if result == 'approved':
        _ensure_project_task(project, 'client_issue_start_notice', created_by=request.user)
    elif result == 'changes_requested':
        _ensure_project_task(project, 'client_resubmit_pre_docs', created_by=request.user)

    messages.success(request, f'预审处理完成：{dict(ProjectDrawingReview.RESULT_CHOICES).get(result, result)}。')
    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")


@login_required
@require_http_methods(['POST'])
def project_drawing_action(request, project_id, submission_id):
    project = get_object_or_404(Project, id=project_id)
    submission = get_object_or_404(ProjectDrawingSubmission, id=submission_id, project=project)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
            or project.project_manager_id == request.user.id
            or project.business_manager_id == request.user.id
            or _user_is_project_member(request.user, project)):
        messages.error(request, '您没有执行该操作的权限。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    action = request.POST.get('action')
    now = timezone.now()

    if action == 'start_review':
        with transaction.atomic():
            submission.status = 'in_review'
            submission.save(update_fields=['status'])
            project.launch_status = 'precheck_in_progress'
            project.launch_status_updated_time = now
            project.save(update_fields=['launch_status', 'launch_status_updated_time'])
        messages.success(request, '已标记为预审中。')
    elif action == 'mark_notified':
        channel = request.POST.get('channel') or 'system'
        with transaction.atomic():
            submission.client_notified = True
            submission.client_notified_time = now
            submission.client_notification_channel = channel
            submission.save(update_fields=['client_notified', 'client_notified_time', 'client_notification_channel'])
        messages.success(request, '已记录甲方通知。')
    else:
        messages.error(request, '不支持的操作类型。')

    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")


@login_required
@require_http_methods(['POST'])
def project_start_notice_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
            or project.project_manager_id == request.user.id):
        messages.error(request, '您没有创建开工通知的权限。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    subject = (request.POST.get('subject') or '').strip()
    message_content = (request.POST.get('message') or '').strip()
    if not subject or not message_content:
        messages.error(request, '请填写完整的通知主题和内容。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    channel = request.POST.get('channel') or 'system'
    submission_id = request.POST.get('submission_id')
    submission = None
    if submission_id:
        try:
            submission = ProjectDrawingSubmission.objects.get(id=int(submission_id), project=project)
        except (ProjectDrawingSubmission.DoesNotExist, ValueError):
            submission = None

    recipient_user = None
    recipient_user_id = request.POST.get('recipient_user')
    if recipient_user_id:
        try:
            recipient_user = User.objects.get(id=int(recipient_user_id))
        except (User.DoesNotExist, ValueError):
            recipient_user = None

    notice = ProjectStartNotice.objects.create(
        project=project,
        submission=submission,
        subject=subject,
        message=message_content,
        channel=channel if channel in dict(ProjectStartNotice.CHANNEL_CHOICES) else 'system',
        recipient_user=recipient_user,
        recipient_name=(request.POST.get('recipient_name') or '').strip(),
        recipient_phone=(request.POST.get('recipient_phone') or '').strip(),
        recipient_email=(request.POST.get('recipient_email') or '').strip(),
        created_by=request.user,
        metadata={'source': 'manual_form'},
    )

    messages.success(request, '开工通知已草拟，可在下方列表中发送。')
    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")


@login_required
@require_http_methods(['POST'])
def project_start_notice_action(request, project_id, notice_id):
    project = get_object_or_404(Project, id=project_id)
    notice = get_object_or_404(ProjectStartNotice, id=notice_id, project=project)
    permission_set = get_user_permission_codes(request.user)
    if not (_has_permission(permission_set, 'production_management.configure_team', 'production_management.view_all')
            or project.project_manager_id == request.user.id):
        messages.error(request, '您没有更新开工通知的权限。')
        return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")

    action = request.POST.get('action')
    now = timezone.now()

    if action == 'send':
        with transaction.atomic():
            notice.status = 'sent'
            notice.sent_time = now
            notice.save(update_fields=['status', 'sent_time'])
            project.launch_status = 'ready_to_start'
            project.start_notice_sent_time = now
            project.launch_status_updated_time = now
            project.save(update_fields=['launch_status', 'start_notice_sent_time', 'launch_status_updated_time'])
            if notice.submission_id:
                submission = notice.submission
                submission.client_notified = True
                submission.client_notified_time = now
                submission.client_notification_channel = notice.channel
                submission.save(update_fields=['client_notified', 'client_notified_time', 'client_notification_channel'])
        messages.success(request, '开工通知已发送。')
        _complete_project_task(project, 'client_issue_start_notice', actor=request.user)
        _ensure_project_task(project, 'internal_compile_opinions', created_by=request.user)
    elif action == 'acknowledge':
        with transaction.atomic():
            notice.status = 'acknowledged'
            notice.acknowledged_time = now
            notice.save(update_fields=['status', 'acknowledged_time'])
            project.launch_status = 'started'
            project.launch_status_updated_time = now
            if not project.actual_start_date:
                project.actual_start_date = now.date()
                project.save(update_fields=['launch_status', 'launch_status_updated_time', 'actual_start_date'])
            else:
                project.save(update_fields=['launch_status', 'launch_status_updated_time'])
        messages.success(request, '已确认开工。')
        _complete_project_task(project, 'client_issue_start_notice', actor=request.user)
        _ensure_project_task(project, 'internal_compile_opinions', created_by=request.user)
    elif action == 'fail':
        failure_reason = (request.POST.get('failure_reason') or '').strip()
        with transaction.atomic():
            notice.status = 'failed'
            notice.failure_reason = failure_reason
            notice.save(update_fields=['status', 'failure_reason'])
            project.launch_status = 'ready_to_start'
            project.launch_status_updated_time = now
            project.save(update_fields=['launch_status', 'launch_status_updated_time'])
        messages.warning(request, '已标记为发送失败，请检查原因后重新发送。')
        _ensure_project_task(project, 'client_issue_start_notice', created_by=request.user)
    else:
        messages.error(request, '不支持的操作类型。')

    return redirect(f"{reverse('production_pages:project_detail', args=[project.id])}?tab=launch")



@login_required
def project_archive(request, project_id):
    """项目归档管理页面"""
    project = get_object_or_404(Project, id=project_id)
    
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.archive'):
        messages.error(request, '您没有归档项目的权限。')
        return redirect('admin:index')

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
            return redirect('production_pages:project_list')
        except Exception as e:
            messages.error(request, f'归档失败：{str(e)}')
    
    archives = ProjectArchive.objects.filter(project=project).order_by('-archive_version')
    
    return render(request, 'production_management/project_archive.html', _with_nav({
        'project': project,
        'archives': archives,
    }, permission_set, 'project_list', request.user))

def _project_ids_user_can_access(user):
    if user.is_superuser:
        return set(Project.objects.values_list('id', flat=True))
    owned = set(
        Project.objects.filter(
            Q(project_manager=user) | Q(business_manager=user) | Q(created_by=user)
        ).values_list('id', flat=True)
    )
    team_related = set(
        ProjectTeam.objects.filter(user=user, is_active=True).values_list('project_id', flat=True)
    )
    return owned | team_related

def _format_user_display(user, default="未指定"):
    if not user:
        return default
    return user.get_full_name() or user.username or default

def _filter_candidates_by_profession(primary_qs, profession, fallback_qs=None, global_qs=None, allow_fallback=True):
    keywords = list(PROFESSION_KEYWORDS.get(profession.code, []))
    if profession.name:
        keywords.append(profession.name)
    condition = Q()
    for keyword in keywords:
        keyword = (keyword or '').strip()
        if keyword:
            condition |= Q(position__icontains=keyword)

    sources = [primary_qs]
    if allow_fallback:
        sources.extend([fallback_qs, global_qs])

    for source in filter(None, sources):
        filtered = source.filter(condition) if condition else source
        if filtered.exists():
            return filtered

    if allow_fallback:
        for source in filter(None, [primary_qs, fallback_qs, global_qs]):
            if source.exists():
                return source

    return primary_qs.none()

def _prefer_real_collaborators(candidates):
    if candidates is None:
        return []
    iterable = list(candidates) if not isinstance(candidates, list) else candidates
    real = [u for u in iterable if not str(getattr(u, 'username', '')).startswith('external_')]
    return real or iterable

def _parse_decimal_input(value):
    try:
        return Decimal(value)
    except (ValueError, TypeError):
        return None

@login_required
def project_import_admin(request):
    """管理员批量导入项目"""
    permission_set = get_user_permission_codes(request.user)
    if not _is_system_admin(request.user):
        messages.error(request, '仅系统管理员可以执行项目导入。')
        return redirect('admin:index')

    if request.GET.get('download') == 'template':
        service_type_sample_obj = ServiceType.objects.order_by('id').first()
        design_stage_sample_label = Project.DESIGN_STAGES[0][1] if Project.DESIGN_STAGES else ''
        status_label_map = dict(Project.PROJECT_STATUS)
        status_sample_label = status_label_map.get('waiting_receive', '待接收')
        columns = [
            '项目编号（可留空自动生成）',
            '项目名称',
            '服务类型（可填编码或名称）',
            '项目业态',
            '图纸阶段（可填编码或名称）',
            '商务经理手机号',
            '项目经理手机号',
            '项目状态（可填编码或名称）',
        ]
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="project_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(columns)
        writer.writerow([
            '',
            '锦城天府综合体一期',
            service_type_sample_obj.name if service_type_sample_obj else '',
            '住宅',
            design_stage_sample_label,
            '13800000005',
            '13800000008',
            status_sample_label,
        ])
        return response

    context = {
        'service_types': ServiceType.objects.order_by('order', 'id'),
        'design_stages': Project.DESIGN_STAGES,
        'business_types': BusinessType.objects.filter(is_active=True).order_by('order', 'id'),
        'status_choices': Project.PROJECT_STATUS,
        'import_results': None,
    }

    if request.method == 'POST':
        upload = request.FILES.get('import_file')
        if not upload:
            messages.error(request, '请上传 CSV 文件。')
        else:
            filename = upload.name.lower()
            if not filename.endswith('.csv'):
                messages.error(request, '仅支持 CSV 文件。')
            elif upload.size > 5 * 1024 * 1024:
                messages.error(request, '文件过大，请控制在 5MB 以内。')
            else:
                try:
                    upload.seek(0)
                except Exception:
                    pass
                raw_bytes = upload.read()
                decoded_text = None
                detected_encoding = None
                for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
                    try:
                        decoded_text = raw_bytes.decode(enc)
                        detected_encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                if decoded_text is None:
                    messages.error(request, 'CSV 文件解析失败，请确认编码为 UTF-8 或 GBK。')
                else:
                    text_io = io.StringIO(decoded_text)
                    reader = csv.DictReader(text_io)
                    field_aliases = {
                        'project_number': {'项目编号（可留空自动生成）', '项目编号', 'project_number'},
                        'name': {'项目名称', 'name'},
                        'service_type': {'服务类型（可填编码或名称）', '服务类型编码', 'service_type_code'},
                        'business_type': {'项目业态', 'business_type'},
                        'design_stage': {'图纸阶段（可填编码或名称）', '图纸阶段编码', 'design_stage'},
                        'business_manager_phone': {'商务经理手机号', 'business_manager_phone'},
                        'project_manager_phone': {'项目经理手机号', 'project_manager_phone'},
                        'status': {'项目状态（可填编码或名称）', '项目状态编码', 'status'},
                    }
                    required_fields = {
                        'name',
                        'service_type',
                        'business_type',
                        'design_stage',
                        'business_manager_phone',
                        'status',
                    }

                    missing_labels = []
                    headers = set(reader.fieldnames or [])
                    for field in required_fields:
                        if not any(alias in headers for alias in field_aliases[field]):
                            missing_labels.append(next(iter(field_aliases[field])))
                    if missing_labels:
                        messages.error(request, f'CSV 缺少必要字段：{", ".join(missing_labels)}。')
                    else:
                        def get_value(row, field):
                            for alias in field_aliases[field]:
                                if alias in row and row[alias] is not None:
                                    return str(row.get(alias, '')).strip()
                            return ''

                        service_type_lookup = {
                            st.code: st for st in ServiceType.objects.all()
                        }
                        service_type_name_lookup = {
                            (st.name or '').strip(): st for st in ServiceType.objects.all()
                        }
                        business_type_lookup = {
                            bt.code: bt for bt in BusinessType.objects.filter(is_active=True)
                        }
                        business_type_name_lookup = {
                            (bt.name or '').strip(): bt for bt in BusinessType.objects.filter(is_active=True)
                        }
                        status_codes = {code for code, _ in Project.PROJECT_STATUS}
                        design_stage_codes = {code for code, _ in Project.DESIGN_STAGES}
                        design_stage_label_map = {
                            (label or '').strip(): code for code, label in Project.DESIGN_STAGES
                        }
                        status_label_map = {
                            (label or '').strip(): code for code, label in Project.PROJECT_STATUS
                        }
                        results = []
                        success_count = 0
                        failure_count = 0

                        for row_index, row in enumerate(reader, start=2):
                            row_result = {'row': row_index, 'status': 'success', 'message': ''}
                            try:
                                with transaction.atomic():
                                    project_name = get_value(row, 'name')
                                    if not project_name:
                                        raise ValueError('项目名称不能为空')

                                    service_type_key = get_value(row, 'service_type')
                                    service_type = service_type_lookup.get(service_type_key)
                                    if not service_type:
                                        service_type = service_type_name_lookup.get(service_type_key)
                                    if not service_type:
                                        raise ValueError(f'服务类型取值无效：{service_type_key}')

                                    business_type_key = get_value(row, 'business_type')
                                    business_type = business_type_lookup.get(business_type_key)
                                    if not business_type:
                                        business_type = business_type_name_lookup.get(business_type_key)
                                    if not business_type:
                                        raise ValueError(f'项目业态取值无效：{business_type_key}')
                                    design_stage_raw = get_value(row, 'design_stage')
                                    design_stage = design_stage_raw
                                    if design_stage and design_stage not in design_stage_codes:
                                        design_stage = design_stage_label_map.get(design_stage_raw)
                                    if design_stage and design_stage not in design_stage_codes:
                                        raise ValueError(f'图纸阶段取值无效：{design_stage_raw}')

                                    business_manager_phone = get_value(row, 'business_manager_phone')
                                    if not business_manager_phone:
                                        raise ValueError('商务经理手机号不能为空')
                                    business_manager = User.objects.filter(username=business_manager_phone).first()
                                    if not business_manager:
                                        raise ValueError(f'未找到对应的商务经理手机号：{business_manager_phone}')

                                    project_manager_phone = get_value(row, 'project_manager_phone')
                                    project_manager = None
                                    if project_manager_phone:
                                        project_manager = User.objects.filter(username=project_manager_phone).first()
                                        if not project_manager:
                                            raise ValueError(f'未找到对应的项目经理手机号：{project_manager_phone}')

                                    status_raw = get_value(row, 'status') or 'waiting_receive'
                                    status_code = status_raw
                                    if status_code not in status_codes:
                                        status_code = status_label_map.get(status_raw)
                                    if status_code not in status_codes:
                                        raise ValueError(f'项目状态取值无效：{status_raw}')

                                    project_number = get_value(row, 'project_number')
                                    if project_number and Project.objects.filter(project_number=project_number).exists():
                                        raise ValueError(f'项目编号重复：{project_number}')

                                    project = Project(
                                        project_number=project_number or None,
                                        name=project_name,
                                        service_type=service_type,
                                        business_type=business_type,
                                        design_stage=design_stage,
                                        business_manager=business_manager,
                                        project_manager=project_manager if status_code != 'waiting_receive' else None,
                                        status=status_code,
                                        created_by=request.user,
                                    )
                                    project.save()

                                    ProjectTeam.objects.update_or_create(
                                        project=project,
                                        role='business_manager',
                                        defaults={
                                            'user': business_manager,
                                            'unit': 'business',
                                            'service_profession': None,
                                            'is_external': False,
                                            'is_active': True,
                                        }
                                    )

                                    if project_manager:
                                        ProjectTeam.objects.update_or_create(
                                            project=project,
                                            role='project_manager',
                                            defaults={
                                                'user': project_manager,
                                                'unit': 'management',
                                                'service_profession': None,
                                                'is_external': False,
                                                'is_active': True,
                                            }
                                        )

                                    success_count += 1
                                    row_result['message'] = '导入成功'
                            except Exception as exc:
                                failure_count += 1
                                row_result['status'] = 'failed'
                                row_result['message'] = str(exc)
                            results.append(row_result)

                        context['import_results'] = {
                            'total': success_count + failure_count,
                            'success': success_count,
                            'failed': failure_count,
                            'rows': results,
                        }
                        if success_count:
                            messages.success(request, f'成功导入 {success_count} 条项目。')
                        if failure_count:
                            messages.warning(request, f'{failure_count} 条记录导入失败，请查看结果列表。')

    return render(
        request,
        'production_management/project_import.html',
        _with_nav(context, permission_set, 'project_list', request.user)
    )


def _build_service_timeline(project, milestone_list):
    service_code = getattr(project.service_type, "code", "") if project.service_type else ""
    template = SERVICE_TIMELINE_TEMPLATES.get(service_code, [])
    if not template and milestone_list:
        template = [milestone.name for milestone in milestone_list]
    lookup = {milestone.name: milestone for milestone in milestone_list}
    stages = []
    completed = 0
    current_index = None
    for index, name in enumerate(template):
        milestone = lookup.get(name)
        status = "completed" if milestone and milestone.is_completed else "pending"
        if status == "completed":
            completed += 1
        elif current_index is None:
            current_index = index
        stages.append(
            {
                "name": name,
                "status": status,
                "planned_start": getattr(milestone, "planned_date", None),
                "planned_end": getattr(milestone, "planned_date", None),
                "actual_start": getattr(milestone, "actual_start", None),
                "actual_end": getattr(milestone, "actual_date", None),
            }
        )
    if stages:
        if current_index is None:
            current_index = len(stages) - 1
        if stages[current_index]["status"] != "completed":
            stages[current_index]["status"] = "current"
    completion_rate = int(round(completed / len(stages) * 100)) if stages else 0
    return stages, completion_rate


@login_required
def production_management(request):
    """生产管理主页面"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有查看生产管理的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('admin:index')
    
    # 获取用户可访问的项目
    accessible_ids = _project_ids_user_can_access(request.user)
    projects = Project.objects.filter(id__in=accessible_ids).select_related(
        'project_manager', 'business_manager', 'client', 'client_leader', 'design_leader', 'responsible_department', 'responsible_person', 'created_by'
    ).prefetch_related('service_professions', 'team_members__user')
    
    # 查询条件
    project_number = request.GET.get('project_number', '').strip()
    project_name = request.GET.get('project_name', '').strip()
    status_filter = request.GET.get('status', '').strip()
    flow_step_filter = request.GET.get('flow_step', '').strip()
    
    if project_number:
        projects = projects.filter(project_number__icontains=project_number)
    if project_name:
        projects = projects.filter(name__icontains=project_name)
    if status_filter:
        projects = projects.filter(status=status_filter)
    if flow_step_filter:
        projects = projects.filter(current_flow_step=flow_step_filter)
    
    # 只显示已开工或进行中的项目
    production_projects = projects.filter(
        status__in=['in_progress', 'waiting_start', 'configuring']
    ).order_by('-updated_time')
    
    # 统计信息
    total_projects = production_projects.count()
    in_progress_count = production_projects.filter(status='in_progress').count()
    waiting_start_count = production_projects.filter(status='waiting_start').count()
    configuring_count = production_projects.filter(status='configuring').count()
    
    # 意见统计（如果 Opinion 模型可用）
    opinion_stats = {}
    if Opinion:
        try:
            opinion_projects = Opinion.objects.filter(
                project_id__in=accessible_ids
            ).values('project_id', 'status').annotate(count=Count('id'))
            
            for stat in opinion_projects:
                project_id = stat['project_id']
                if project_id not in opinion_stats:
                    opinion_stats[project_id] = {}
                opinion_stats[project_id][stat['status']] = stat['count']
        except Exception as e:
            logger.warning(f'获取意见统计失败: {e}')
    
    # 任务统计
    task_stats = {}
    try:
        active_tasks = ProjectTask.objects.filter(
            project_id__in=accessible_ids,
            status__in=ProjectTask.ACTIVE_STATUSES
        ).values('project_id').annotate(count=Count('id'))
        
        for stat in active_tasks:
            task_stats[stat['project_id']] = stat['count']
    except Exception as e:
        logger.warning(f'获取任务统计失败: {e}')
    
    # 为每个项目添加统计信息
    project_list = []
    for project in production_projects[:50]:  # 限制显示数量
        project_data = {
            'project': project,
            'opinion_count': sum(opinion_stats.get(project.id, {}).values()) if project.id in opinion_stats else 0,
            'opinion_stats': opinion_stats.get(project.id, {}),
            'task_count': task_stats.get(project.id, 0),
        }
        project_list.append(project_data)
    
    # 流程步骤统计
    flow_step_stats = {}
    for project in production_projects:
        step = project.current_flow_step or 'unknown'
        flow_step_stats[step] = flow_step_stats.get(step, 0) + 1
    
    context = _with_nav({
        'page_title': '生产管理',
        'projects': project_list,
        'total_projects': total_projects,
        'in_progress_count': in_progress_count,
        'waiting_start_count': waiting_start_count,
        'configuring_count': configuring_count,
        'flow_step_stats': flow_step_stats,
        'status_filter': status_filter,
        'flow_step_filter': flow_step_filter,
        'project_number': project_number,
        'project_name': project_name,
        'FLOW_STEPS': Project.FLOW_STEPS,
        'PROJECT_STATUS': Project.PROJECT_STATUS,
    }, permission_set, 'production_management', request.user)
    
    return render(request, 'production_management/production_management.html', context)


@login_required
def ai_advisor(request):
    """设计优化AI顾问系统"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问AI顾问系统的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('production_pages:production_management_home')
    
    # 获取统计信息（可以从数据库查询）
    # 这里先用模拟数据，后续可以改为从数据库查询
    stats = {
        'total_cases': 1247,
        'total_savings': 12473.0,  # 万元
    }
    
    # 获取所有服务类型
    service_types = ServiceType.objects.order_by('order', 'id')
    
    # 获取所有专业类型，按服务类型和专业排序
    professions = ServiceProfession.objects.select_related('service_type').order_by('service_type__order', 'order', 'id')
    
    # 构建服务类型与专业的映射关系（用于前端联动）
    import json
    profession_map = {}
    for profession in professions:
        service_type_id = str(profession.service_type.id)
        if service_type_id not in profession_map:
            profession_map[service_type_id] = []
        profession_map[service_type_id].append({
            'code': profession.code,
            'name': profession.name,
            'id': profession.id
        })
    
    # 将profession_map转换为JSON字符串，供前端使用
    profession_map_json = json.dumps(profession_map, ensure_ascii=False)
    
    context = _with_nav({
        'stats': stats,
        'service_types': service_types,
        'professions': professions,
        'profession_map_json': profession_map_json,
    }, permission_set, 'ai_advisor', request.user, request=request)
    
    return render(request, 'production_management/ai_advisor.html', context)


@login_required
def pre_optimization_materials_list(request):
    """优化前资料列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有访问优化前资料列表的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('production_pages:production_management_home')
    
    # 获取查询参数
    project_id = request.GET.get('project_id')
    parse_status = request.GET.get('parse_status')
    search = request.GET.get('search', '').strip()
    
    # 构建查询
    queryset = PreOptimizationMaterial.objects.select_related('project', 'uploaded_by').all()
    
    # 权限过滤
    if not _has_permission(permission_set, 'production_management.view_all'):
        # 只能查看自己参与的项目
        user_projects = Project.objects.filter(
            Q(team_members__user=request.user) | Q(project_manager=request.user)
        ).distinct()
        queryset = queryset.filter(project__in=user_projects)
    
    # 项目过滤
    if project_id:
        try:
            queryset = queryset.filter(project_id=int(project_id))
        except ValueError:
            pass
    
    # 解析状态过滤
    if parse_status:
        queryset = queryset.filter(parse_status=parse_status)
    
    # 搜索过滤
    if search:
        queryset = queryset.filter(
            Q(file_name__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(project__name__icontains=search) |
            Q(design_unit__icontains=search)
        )
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)
    
    # 获取所有项目（用于筛选）
    if _has_permission(permission_set, 'production_management.view_all'):
        all_projects = Project.objects.all().order_by('-created_time')[:100]
    else:
        all_projects = Project.objects.filter(
            Q(team_members__user=request.user) | Q(project_manager=request.user)
        ).distinct().order_by('-created_time')[:100]
    
    context = _with_nav({
        'page_title': '优化前资料',
        'page_description': '管理优化前资料，支持CAD文件自动解析',
        'materials': page_obj,
        'all_projects': all_projects,
        'selected_project_id': project_id,
        'selected_parse_status': parse_status,
        'search': search,
        'parse_status_choices': PreOptimizationMaterial.PARSE_STATUS_CHOICES,
    }, permission_set, 'pre_optimization_materials', request.user, request=request)
    
    return render(request, 'production_management/pre_optimization_materials_list.html', context)


def _update_parse_progress(material_id, progress, message=''):
    """更新解析进度的辅助函数（支持后台线程）"""
    try:
        from .models import PreOptimizationMaterial
        # 重新从数据库获取对象，避免后台线程中的连接问题
        material = PreOptimizationMaterial.objects.get(id=material_id)
        material.parse_progress = progress
        material.parse_progress_message = message
        material.save(update_fields=['parse_progress', 'parse_progress_message'])
        print(f"[CAD解析进度更新] Material ID: {material_id}, Progress: {progress}%, Message: {message}", flush=True)
    except PreOptimizationMaterial.DoesNotExist:
        print(f"[CAD解析进度更新] 警告: Material ID {material_id} 不存在，无法更新进度。", flush=True)
    except Exception as e:
        print(f"[CAD解析进度更新] 更新进度时发生错误: {e}", flush=True)
        logger.error(f"更新解析进度失败: {str(e)}", exc_info=True)


@login_required
def pre_optimization_materials_create(request):
    """创建优化前资料"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有创建优化前资料的权限。', 'production_management.create', 'production_management.view_all'):
        return redirect('production_pages:pre_optimization_materials')
    
    # 获取可选项目列表（排除已归档和已取消的项目）
    if _has_permission(permission_set, 'production_management.view_all'):
        available_projects = Project.objects.exclude(
            status__in=['archived', 'cancelled', 'completed']
        ).order_by('-created_time')
    else:
        available_projects = Project.objects.filter(
            Q(team_members__user=request.user) | Q(project_manager=request.user)
        ).exclude(
            status__in=['archived', 'cancelled', 'completed']
        ).distinct().order_by('-created_time')
    
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        cad_file = request.FILES.get('cad_file')
        description = request.POST.get('description', '').strip()
        
        # 验证
        if not project_id:
            messages.error(request, '请选择项目。')
            return redirect('production_pages:pre_optimization_materials_create')
        
        if not cad_file:
            messages.error(request, '请上传CAD文件。')
            return redirect('production_pages:pre_optimization_materials_create')
        
        # 验证文件类型
        file_ext = os.path.splitext(cad_file.name)[1].lower()
        if file_ext not in ['.dwg', '.dxf', '.pdf']:
            messages.error(request, '不支持的文件格式，仅支持DWG、DXF、PDF格式。')
            return redirect('production_pages:pre_optimization_materials_create')
        
        # 验证文件大小（限制100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if cad_file.size > max_size:
            messages.error(request, f'文件大小不能超过100MB，当前文件大小: {cad_file.size / 1024 / 1024:.2f}MB')
            return redirect('production_pages:pre_optimization_materials_create')
        
        try:
            project = Project.objects.get(id=project_id)
            
            # 创建记录
            material = PreOptimizationMaterial.objects.create(
                project=project,
                cad_file=cad_file,
                file_name=cad_file.name,
                file_size=cad_file.size,
                file_type=file_ext[1:],  # 去掉点号
                description=description,
                uploaded_by=request.user,
                parse_status='pending',
            )
            
            # 异步解析CAD文件
            try:
                from .services.cad_parser_service import CADParserService
                import threading
                
                def parse_cad():
                    import sys
                    import os
                    import django
                    from django.db import connection
                    from django.core.wsgi import get_wsgi_application
                    import logging
                    thread_logger = logging.getLogger(__name__)
                    
                    material_id = material.id  # 保存 ID，避免在后台线程中使用对象
                    
                    try:
                        # 在后台线程中初始化 Django（如果需要）
                        if not django.apps.apps.ready:
                            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
                            django.setup()
                        
                        thread_logger.info(f"[CAD解析任务] 线程已启动，文件ID: {material_id}")
                        
                        # 关闭当前线程的数据库连接，创建新连接
                        connection.close()
                        
                        thread_logger.info(f"[CAD解析任务] 开始解析任务，文件ID: {material_id}")
                        
                        # 重新获取 material 对象（在后台线程中）
                        from .models import PreOptimizationMaterial
                        material = PreOptimizationMaterial.objects.get(id=material_id)
                        
                        thread_logger.info(f"[CAD解析任务] 文件路径: {material.cad_file.path}")
                        
                        material.parse_status = 'processing'
                        material.parse_progress = 0
                        material.parse_progress_message = '准备开始解析...'
                        material.save()
                        thread_logger.info(f"[CAD解析任务] 状态已更新为 processing")
                        
                        thread_logger.info(f"[CAD解析任务] 创建 CADParserService 实例")
                        _update_parse_progress(material_id, 10, '初始化解析服务...')
                        parser = CADParserService()
                        thread_logger.info(f"[CAD解析任务] CADParserService 创建成功，cad2image_available: {parser.cad2image_available}")
                        
                        thread_logger.info(f"[CAD解析任务] 调用 parse_for_pre_optimization")
                        _update_parse_progress(material_id, 20, '开始解析CAD文件...')
                        
                        def progress_callback(progress, message):
                            _update_parse_progress(material_id, progress, message)
                        
                        result = parser.parse_for_pre_optimization(material.cad_file.path, progress_callback=progress_callback)
                        thread_logger.info(f"[CAD解析任务] 解析完成，结果: success={result.get('success')}")
                        
                        # 重新获取 material 对象（可能已被其他进程修改）
                        material = PreOptimizationMaterial.objects.get(id=material_id)
                        
                        if result.get('success'):
                            # 提取基本信息
                            basic_info = result.get('basic_info', {})
                            material.design_unit = basic_info.get('design_unit', '')
                            material.drawing_version = basic_info.get('drawing_version', '')
                            material.general_description = basic_info.get('general_description', '')
                            
                            # 提取技术经济指标
                            material.technical_economic_indicators = result.get('technical_economic_indicators', {})
                            
                            # 提取图纸目录
                            material.drawing_catalog = result.get('drawing_catalog', {})
                            
                            # 保存完整解析结果
                            material.cad_parse_result = result
                            
                            material.parse_status = 'success'
                            material.parse_progress = 100
                            material.parse_progress_message = '解析完成！'
                            material.parsed_time = timezone.now()
                            material.parse_error = ''
                            thread_logger.info(f"[CAD解析任务] 解析成功，保存结果")
                        else:
                            material.parse_status = 'failed'
                            material.parse_error = result.get('error', '解析失败')
                            material.parse_progress_message = '解析失败！'
                            thread_logger.error(f"[CAD解析任务] 解析失败: {result.get('error', '未知错误')}")
                        
                        material.save()
                        thread_logger.info(f"[CAD解析任务] 最终状态已保存")
                    except Exception as e:
                        import traceback
                        error_msg = f"CAD解析失败: {str(e)}"
                        thread_logger.error(f"[CAD解析任务] 异常: {error_msg}")
                        thread_logger.error(f"[CAD解析任务] 异常堆栈: {traceback.format_exc()}")
                        thread_logger.error(f"CAD解析失败: {str(e)}", exc_info=True)
                        
                        # 尝试更新状态
                        try:
                            from .models import PreOptimizationMaterial
                            material = PreOptimizationMaterial.objects.get(id=material_id)
                            material.parse_status = 'failed'
                            material.parse_error = str(e)
                            material.parse_progress_message = '解析过程中发生错误！'
                            material.save()
                            thread_logger.info(f"[CAD解析任务] 错误状态已保存")
                        except Exception as save_error:
                            thread_logger.error(f"[CAD解析任务] 保存错误状态失败: {save_error}")
                
                # 在后台线程中执行解析
                logger.info(f"[CAD解析] 准备启动后台线程，Material ID: {material.id}")
                
                # 立即更新状态为 processing（在主线程中，确保用户立即看到状态变化）
                try:
                    material.parse_status = 'processing'
                    material.parse_progress = 0
                    material.parse_progress_message = '准备开始解析...'
                    material.save(update_fields=['parse_status', 'parse_progress', 'parse_progress_message'])
                    logger.info(f"[CAD解析] 主线程中状态已更新为 processing")
                except Exception as e:
                    logger.error(f"[CAD解析] 主线程中更新状态失败: {e}", exc_info=True)
                
                # 启动后台线程
                thread = threading.Thread(target=parse_cad, name=f"CADParse-{material.id}")
                thread.daemon = True
                thread.start()
                logger.info(f"[CAD解析] 后台线程已启动，线程名: {thread.name}, 是否存活: {thread.is_alive()}, 线程ID: {thread.ident}")
                
                # 等待一小段时间，确保线程开始执行
                import time
                time.sleep(0.1)
                logger.info(f"[CAD解析] 线程启动后检查，是否存活: {thread.is_alive()}")
                
                messages.success(request, '优化前资料创建成功，CAD文件正在后台解析中，请稍后查看详情。')
            except Exception as e:
                logger.error(f"启动CAD解析失败: {str(e)}", exc_info=True)
                messages.warning(request, '优化前资料创建成功，但CAD解析启动失败，您可以稍后手动重新解析。')
            
            return redirect('production_pages:pre_optimization_materials_detail', material_id=material.id)
            
        except Project.DoesNotExist:
            messages.error(request, '项目不存在。')
            return redirect('production_pages:pre_optimization_materials_create')
        except Exception as e:
            logger.error(f"创建优化前资料失败: {str(e)}", exc_info=True)
            messages.error(request, f'创建失败: {str(e)}')
            return redirect('production_pages:pre_optimization_materials_create')
    
    context = _with_nav({
        'page_title': '创建优化前资料',
        'page_description': '上传CAD文件，系统将自动解析提取设计信息',
        'available_projects': available_projects,
    }, permission_set, 'pre_optimization_materials', request.user, request=request)
    
    return render(request, 'production_management/pre_optimization_materials_create.html', context)


@login_required
def pre_optimization_materials_detail(request, material_id):
    """优化前资料详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有查看优化前资料详情的权限。', 'production_management.view_all', 'production_management.view_assigned'):
        return redirect('production_pages:pre_optimization_materials')
    
    material = get_object_or_404(
        PreOptimizationMaterial.objects.select_related('project', 'uploaded_by'),
        id=material_id
    )
    
    # 权限检查
    if not _has_permission(permission_set, 'production_management.view_all'):
        if not _user_is_project_member(request.user, material.project):
            messages.error(request, '您无权访问该资料。')
            return redirect('production_pages:pre_optimization_materials')
    
    context = _with_nav({
        'page_title': f'优化前资料详情 - {material.file_name}',
        'page_description': '查看CAD解析结果和详细信息',
        'material': material,
    }, permission_set, 'pre_optimization_materials', request.user, request=request)
    
    return render(request, 'production_management/pre_optimization_materials_detail.html', context)


@login_required
def pre_optimization_materials_progress(request, material_id):
    """获取优化前资料解析进度（API）"""
    from django.http import JsonResponse
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all'):
        material = get_object_or_404(PreOptimizationMaterial, id=material_id)
        if not _user_is_project_member(request.user, material.project):
            return JsonResponse({'error': '无权访问'}, status=403)
    
    material = get_object_or_404(PreOptimizationMaterial, id=material_id)
    
    return JsonResponse({
        'status': material.parse_status,
        'progress': material.parse_progress,
        'message': material.parse_progress_message or '',
        'error': material.parse_error or '',
        'is_finished': material.parse_status in ['success', 'failed'],
    })


@login_required
def pre_optimization_materials_reparse(request, material_id):
    """重新解析优化前资料"""
    permission_set = get_user_permission_codes(request.user)
    if not _require_permission(request, permission_set, '您没有重新解析优化前资料的权限。', 'production_management.create', 'production_management.view_all'):
        return redirect('production_pages:pre_optimization_materials')
    
    material = get_object_or_404(PreOptimizationMaterial, id=material_id)
    
    # 权限检查
    if not _has_permission(permission_set, 'production_management.view_all'):
        if not _user_is_project_member(request.user, material.project):
            messages.error(request, '您无权操作该资料。')
            return redirect('production_pages:pre_optimization_materials')
    
    if request.method == 'POST':
        try:
            from .services.cad_parser_service import CADParserService
            import threading
            
            def parse_cad():
                import sys
                import os
                import django
                from django.db import connection
                from django.core.wsgi import get_wsgi_application
                
                material_id = material.id  # 保存 ID，避免在后台线程中使用对象
                
                try:
                    # 在后台线程中初始化 Django（如果需要）
                    if not django.apps.apps.ready:
                        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
                        django.setup()
                    
                    print(f"[CAD解析任务] 重新解析线程已启动，文件ID: {material_id}", flush=True)
                    sys.stdout.flush()
                    
                    # 关闭当前线程的数据库连接，创建新连接
                    connection.close()
                    
                    print(f"[CAD解析任务] 开始重新解析任务，文件ID: {material_id}", flush=True)
                    sys.stdout.flush()
                    
                    # 重新获取 material 对象（在后台线程中）
                    from .models import PreOptimizationMaterial
                    material = PreOptimizationMaterial.objects.get(id=material_id)
                    
                    print(f"[CAD解析任务] 文件路径: {material.cad_file.path}", flush=True)
                    sys.stdout.flush()
                    
                    material.parse_status = 'processing'
                    material.parse_progress = 0
                    material.parse_progress_message = '准备开始解析...'
                    material.save()
                    print(f"[CAD解析任务] 状态已更新为 processing", flush=True)
                    sys.stdout.flush()
                    
                    print(f"[CAD解析任务] 创建 CADParserService 实例", flush=True)
                    sys.stdout.flush()
                    _update_parse_progress(material_id, 10, '初始化解析服务...')
                    parser = CADParserService()
                    print(f"[CAD解析任务] CADParserService 创建成功，cad2image_available: {parser.cad2image_available}", flush=True)
                    sys.stdout.flush()
                    
                    print(f"[CAD解析任务] 调用 parse_for_pre_optimization", flush=True)
                    sys.stdout.flush()
                    _update_parse_progress(material_id, 20, '开始解析CAD文件...')
                    
                    def progress_callback(progress, message):
                        _update_parse_progress(material_id, progress, message)
                    
                    result = parser.parse_for_pre_optimization(material.cad_file.path, progress_callback=progress_callback)
                    print(f"[CAD解析任务] 解析完成，结果: success={result.get('success')}", flush=True)
                    sys.stdout.flush()
                    
                    if result.get('success'):
                        # 提取基本信息
                        basic_info = result.get('basic_info', {})
                        material.design_unit = basic_info.get('design_unit', '')
                        material.drawing_version = basic_info.get('drawing_version', '')
                        material.general_description = basic_info.get('general_description', '')
                        
                        # 提取技术经济指标
                        material.technical_economic_indicators = result.get('technical_economic_indicators', {})
                        
                        # 提取图纸目录
                        material.drawing_catalog = result.get('drawing_catalog', {})
                        
                        # 保存完整解析结果
                        material.cad_parse_result = result
                        
                        material.parse_status = 'success'
                        material.parse_progress = 100
                        material.parse_progress_message = '解析完成！'
                        material.parsed_time = timezone.now()
                        material.parse_error = ''
                    else:
                        material.parse_status = 'failed'
                        material.parse_error = result.get('error', '解析失败')
                    
                    material.save()
                except Exception as e:
                    import traceback
                    error_msg = f"CAD重新解析失败: {str(e)}"
                    print(f"[CAD解析任务] 异常: {error_msg}", flush=True)
                    print(f"[CAD解析任务] 异常堆栈: {traceback.format_exc()}", flush=True)
                    sys.stdout.flush()
                    logger.error(f"CAD重新解析失败: {str(e)}", exc_info=True)
                    material.parse_status = 'failed'
                    material.parse_error = str(e)
                    material.save()
            
            # 在后台线程中执行解析
            logger.info(f"[CAD解析] 准备启动重新解析后台线程，Material ID: {material.id}")
            
            # 立即更新状态为 processing（在主线程中，确保用户立即看到状态变化）
            try:
                material.parse_status = 'processing'
                material.parse_progress = 0
                material.parse_progress_message = '准备开始解析...'
                material.save(update_fields=['parse_status', 'parse_progress', 'parse_progress_message'])
                logger.info(f"[CAD解析] 主线程中重新解析状态已更新为 processing")
            except Exception as e:
                logger.error(f"[CAD解析] 主线程中更新重新解析状态失败: {e}", exc_info=True)
            
            # 启动后台线程
            thread = threading.Thread(target=parse_cad, name=f"CADReparse-{material.id}")
            thread.daemon = True
            thread.start()
            logger.info(f"[CAD解析] 重新解析后台线程已启动，线程名: {thread.name}, 是否存活: {thread.is_alive()}, 线程ID: {thread.ident}")
            
            # 等待一小段时间，确保线程开始执行
            import time
            time.sleep(0.1)
            logger.info(f"[CAD解析] 重新解析线程启动后检查，是否存活: {thread.is_alive()}")
            
            messages.success(request, '已开始重新解析CAD文件，请稍后刷新页面查看结果。')
        except Exception as e:
            logger.error(f"启动CAD重新解析失败: {str(e)}", exc_info=True)
            messages.error(request, f'重新解析失败: {str(e)}')
    
    return redirect('production_pages:pre_optimization_materials_detail', material_id=material.id)

