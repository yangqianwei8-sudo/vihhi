"""
计划管理模块工具函数
"""
from datetime import timedelta
from django.utils import timezone


def user_can_create_company_plan(user):
    """
    只有总经理（general_manager 角色）或超级用户才能编制公司级工作计划。
    
    Returns:
        bool: 若用户可创建/编制公司级计划则返回 True，否则 False。
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    if not hasattr(user, 'roles'):
        return False
    return user.roles.filter(code='general_manager').exists()


class UserProfileNotFoundError(Exception):
    """
    用户 Profile 缺失异常
    
    当尝试访问 user.profile 但 Profile 模型不存在或未关联时抛出此异常。
    这用于公司隔离逻辑，确保 Profile 缺失时能够明确失败、可定位问题。
    
    Attributes:
        user: 缺少 Profile 的用户对象
        message: 错误消息
    """
    def __init__(self, user, message=None):
        self.user = user
        if message is None:
            message = (
                f"用户 {user.username} (ID: {user.id}) 缺少 Profile 对象，"
                f"无法获取公司信息进行数据隔离。请检查用户是否已正确配置 Profile 关系。"
            )
        super().__init__(message)


def apply_company_scope(qs, user, company_field="company"):
    """
    应用公司数据隔离 - P0-2 版本（使用 user.company_id）
    
    ⚠️ P0-2: 公司信息来源已改为 user.company_id（User.company 外键）
    
    策略说明：
    - 使用 user.company_id（直接字段，链路最短）
    - 如果 user.company_id 为 None：记录警告但不过滤（避免列表永远为空）
    - 超管不过滤（可查看所有公司数据）
    
    Args:
        qs: QuerySet
        user: User 对象
        company_field: 公司字段名，默认为 "company"
    
    Returns:
        过滤后的 QuerySet（如果无法确定 company_id，返回未过滤查询集）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if user.is_superuser:
        return qs
    
    # P0-2: 直接使用 user.company_id
    company_id = user.company_id
    
    if company_id is None:
        logger.warning(
            "apply_company_scope: 用户 company_id 为 None，跳过公司隔离过滤 - "
            "user_id=%s, username=%s, 返回未过滤查询集",
            user.id, user.username
        )
        return qs
    
    logger.info(
        "apply_company_scope: 使用 user.company_id - "
        "user_id=%s, username=%s, company_id=%s",
        user.id, user.username, company_id
    )
    
    # 应用公司过滤
    return qs.filter(**{f"{company_field}_id": company_id})


def apply_goal_company_scope(qs, user):
    """
    StrategicGoal 公司隔离（模型无 company 字段，按 responsible_department.company_id）。
    普通用户仅能见：responsible_department__company_id=user.company_id；
    responsible_department 为空的记录不可见。超管不过滤。
    """
    if user.is_superuser:
        return qs
    company_id = getattr(user, 'company_id', None)
    if company_id is None:
        import logging
        logging.getLogger(__name__).warning(
            "apply_goal_company_scope: user.company_id 为空，跳过过滤 user_id=%s", user.id
        )
        return qs
    return qs.filter(responsible_department__company_id=company_id)


def apply_mine_participating_range(
    qs,
    request,
    *,
    mine_field=None,              # e.g. "responsible_person"
    participating_m2m_field=None, # e.g. "participants"
    created_time_field="created_time",  # or "created_at"
    range_param="range",
    mine_param="mine",
    participating_param="participating",
):
    """
    应用"我负责/我参与/时间范围"筛选
    
    Args:
        qs: QuerySet
        request: HttpRequest 对象
        mine_field: 负责人字段名，如 "responsible_person"
        participating_m2m_field: 参与人员 M2M 字段名，如 "participants"
        created_time_field: 创建时间字段名，默认为 "created_time"
        range_param: URL 参数名，默认为 "range"
        mine_param: URL 参数名，默认为 "mine"
        participating_param: URL 参数名，默认为 "participating"
    
    Returns:
        过滤后的 QuerySet
    """
    user = request.user

    if mine_field and request.GET.get(mine_param) == "1":
        qs = qs.filter(**{mine_field: user})

    if participating_m2m_field and request.GET.get(participating_param) == "1":
        qs = qs.filter(**{participating_m2m_field: user})

    r = request.GET.get(range_param)
    if r in ("week", "month"):
        now = timezone.localtime(timezone.now())
        if r == "week":
            # 本周：从本周一 00:00 开始
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # 本月：从本月 1号 00:00 开始
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        qs = qs.filter(**{f"{created_time_field}__gte": start})

    return qs

