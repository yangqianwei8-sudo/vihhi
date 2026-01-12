"""
计划管理模块工具函数
"""
from datetime import timedelta
from django.utils import timezone


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
    应用公司数据隔离 - 改进版（P0-1b）
    
    ⚠️ P0-1b: 公司信息来源优先级策略（已实现）
    
    系统中公司信息的真实来源（按优先级排序，仅列出已实现的策略）：
    1. user.profile.company_id (UserProfile.company, ForeignKey 到 org.Company) - 主要来源
    2. user.profile.department.company_id (通过 org.Department.company 推导) - 备用推导方式
    
    策略说明：
    - 优先使用 user.profile.company_id（主要来源，记录 info 日志）
    - 如果 profile.company_id 为 None，尝试从 profile.department.company_id 推导（备用策略，记录 warning 日志）
    - 如果无法确定 company_id：返回 qs.none() + error 日志（禁止 silent fallback，确保问题可定位）
    - 如果 user.profile 不存在：返回 qs.none() + error 日志（不抛异常，避免页面不可用）
    
    Args:
        qs: QuerySet
        user: User 对象
        company_field: 公司字段名，默认为 "company"
    
    Returns:
        过滤后的 QuerySet（如果无法确定 company_id，返回 qs.none()）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if user.is_superuser:
        return qs
    
    company_id = None
    
    # ✅ 兜底修复：尝试获取 profile，如果不存在则记录警告但不过滤（避免列表永远为空）
    try:
        profile = user.profile
    except AttributeError:
        # user.profile 属性不存在（可能是 Profile 模型未定义或未关联）
        logger.warning(
            "apply_company_scope: 用户缺少 profile 属性，跳过公司隔离过滤 - "
            "user_id=%s, username=%s, 返回未过滤查询集",
            user.id, user.username
        )
        return qs
    
    if profile is None:
        # profile 关系存在但为 None（OneToOne 关系未设置）
        logger.warning(
            "apply_company_scope: 用户 profile 关系为 None，跳过公司隔离过滤 - "
            "user_id=%s, username=%s, 返回未过滤查询集",
            user.id, user.username
        )
        return qs
    
    # ⚠️ P0-1b: 策略1 - 优先使用 profile.company_id（主要来源）
    try:
        company_id = profile.company_id
        if company_id is not None:
            logger.info(
                "apply_company_scope: 使用 profile.company_id (主要来源) - "
                "user_id=%s, username=%s, company_id=%s",
                user.id, user.username, company_id
            )
    except AttributeError:
        # profile 对象存在但缺少 company 属性
        logger.warning(
            "apply_company_scope: Profile 对象缺少 company 属性，跳过公司隔离过滤 - "
            "user_id=%s, username=%s, 返回未过滤查询集",
            user.id, user.username
        )
        return qs
    
    # ⚠️ P0-1b: 策略2 - 如果 profile.company_id 为 None，尝试从 department 推导（备用策略）
    if company_id is None:
        try:
            if hasattr(profile, 'department') and profile.department:
                dept = profile.department
                if hasattr(dept, 'company_id') and dept.company_id:
                    company_id = dept.company_id
                    logger.warning(
                        "apply_company_scope: 使用 department.company_id (备用推导) - "
                        "user_id=%s, username=%s, company_id=%s, department_id=%s",
                        user.id, user.username, company_id, dept.id
                    )
        except Exception as e:
            logger.debug(
                "apply_company_scope: 尝试通过 department 推导公司失败 - "
                "user_id=%s, username=%s, error=%s",
                user.id, user.username, str(e)
            )
    
    # ✅ 兜底修复：如果无法确定 company_id，记录警告但不过滤（避免列表永远为空）
    if company_id is None:
        logger.warning(
            "apply_company_scope: 无法确定用户公司信息，跳过公司隔离过滤 - "
            "user_id=%s, username=%s, profile.company_id=None, "
            "profile.department.company_id=None, 返回未过滤查询集",
            user.id, user.username
        )
        return qs
    
    # ✅ 只在 company_id 有值时才过滤
    return qs.filter(**{f"{company_field}_id": company_id}) if company_id else qs


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

