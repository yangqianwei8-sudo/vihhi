# Legacy 视图函数依赖：从 plan_list 到 get_parent_plan_options
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .common import (
    login_required as _login_required_from_common,
    get_user_permission_codes,
    _permission_granted,
    Plan,
    StrategicGoal,
    GoalAdjustment,
    PlanAdjustment,
    PlanDecision,
    PlanIssue,
    PlanProgressRecord,
    PlanStatusLog,
    GoalProgressRecord,
    GoalStatusLog,
    StrategicGoalForm,
    GoalProgressUpdateForm,
    GoalAdjustmentForm,
    PlanForm,
    PlanProgressUpdateForm,
    PlanIssueForm,
    PlanAdjustmentForm,
    PlanItemFormSet,
    User,
    Department,
    logger,
)
from .menu import (
    _context,
    _build_plan_management_sidebar_nav,
    _filter_plans_by_permission,
    get_plan_qs_for_user,
    get_plan_or_404,
    get_pending_decision_or_404,
    get_goal_qs_for_user,
)
from .helpers import (
    _form_errors_plain,
    _validate_plan_fields,
    calculate_child_goals_summary,
    calculate_child_plans_summary,
    calculate_goal_progress_status,
    calculate_plan_progress_status,
)

login_required = _login_required_from_common
