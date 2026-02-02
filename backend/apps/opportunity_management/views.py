# 商机管理API视图
# 从customer_management迁移而来
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_funnel_analysis_api(request):
    """
    销售漏斗分析API
    
    请求参数:
    - start_date: 开始日期(YYYY-MM-DD,可选)
    - end_date: 结束日期(YYYY-MM-DD,可选)
    - business_manager_id: 商务经理ID(可选)
    
    返回:
    {
        "stages": [
            {
                "stage": str,  # 阶段代码
                "stage_label": str,  # 阶段名称
                "count": int,  # 商机数量
                "amount": float,  # 预计金额(元)
                "weighted_amount": float,  # 加权金额(元)
                "conversion_rate": float  # 转化率(%,相对于上一阶段)
            }
        ],
        "total_opportunities": int,
        "total_amount": float,
        "total_weighted_amount": float,
        "overall_conversion_rate": float  # 整体转化率(从初步接触到赢单)
    }
    """
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.apps.opportunity_management.perm_check import opportunity_can_view_all
    
    # 获取筛选参数
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取商机查询集
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related(
        'client', 'business_manager'
    ).exclude(status__in=['won', 'lost', 'cancelled'])
    
    # 权限过滤
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    # 时间范围筛选
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            opportunities = opportunities.filter(created_time__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            opportunities = opportunities.filter(created_time__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 商务经理筛选
    if business_manager_id:
        opportunities = opportunities.filter(business_manager_id=business_manager_id)
    
    # 按状态统计
    status_stats = opportunities.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('estimated_amount'),
        weighted_amount=Sum('weighted_amount')
    ).order_by('status')
    
    # 构建漏斗数据
    status_order = ['potential', 'initial_contact', 'requirement_confirmed', 'quotation', 'negotiation']
    status_labels = dict(BusinessOpportunity.STATUS_CHOICES)
    
    stages = []
    prev_count = None
    
    for status_code in status_order:
        status_stat = next((s for s in status_stats if s['status'] == status_code), None)
        if status_stat:
            count = status_stat['count']
            amount = float(status_stat['total_amount'] or 0)
            weighted_amount = float(status_stat['weighted_amount'] or 0)
            
            # 计算转化率
            conversion_rate = None
            if prev_count and prev_count > 0:
                conversion_rate = round((count / prev_count) * 100, 2)
            
            stages.append({
                'stage': status_code,
                'stage_label': status_labels.get(status_code, status_code),
                'count': count,
                'amount': amount,
                'weighted_amount': weighted_amount,
                'conversion_rate': conversion_rate,
            })
            prev_count = count
        else:
            stages.append({
                'stage': status_code,
                'stage_label': status_labels.get(status_code, status_code),
                'count': 0,
                'amount': 0,
                'weighted_amount': 0,
                'conversion_rate': None,
            })
            prev_count = 0
    
    # 计算整体统计
    total_opportunities = opportunities.count()
    total_amount = float(opportunities.aggregate(total=Sum('estimated_amount'))['total'] or 0)
    total_weighted_amount = float(opportunities.aggregate(total=Sum('weighted_amount'))['total'] or 0)
    
    # 计算整体转化率
    initial_contact_count = next((d['count'] for d in stages if d['stage'] == 'initial_contact'), 0)
    won_queryset = BusinessOpportunity.objects.filter(is_active=True, status='won')
    if not opportunity_can_view_all(permission_set):
        won_queryset = won_queryset.filter(business_manager=request.user)
    won_count = won_queryset.count()
    overall_conversion_rate = None
    if initial_contact_count > 0:
        overall_conversion_rate = round((won_count / initial_contact_count) * 100, 2)
    
    return Response({
        'stages': stages,
        'total_opportunities': total_opportunities,
        'total_amount': total_amount,
        'total_weighted_amount': total_weighted_amount,
        'overall_conversion_rate': overall_conversion_rate,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_sales_forecast_api(request):
    """
    销售预测API
    
    请求参数:
    - month: 预测月份(YYYY-MM,可选,默认为当前月份)
    
    返回:
    {
        "month": str,  # 预测月份
        "active_opportunities": int,  # 活跃商机数
        "weighted_amount": float,  # 加权金额(元)
        "historical_conversion_rate": float,  # 历史转化率(%)
        "forecast": {
            "optimistic": float,  # 乐观预测(元)
            "neutral": float,  # 中性预测(元)
            "conservative": float  # 保守预测(元)
        },
        "target_gap": {
            "monthly_target": float,  # 月度目标(元)
            "gap": float,  # 目标差距(元)
            "suggestions": [str]  # 建议措施
        }
    }
    """
    from calendar import monthrange
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.apps.opportunity_management.perm_check import opportunity_can_view, opportunity_can_view_all, opportunity_can_access_detail
    
    # 获取预测月份
    forecast_month = request.GET.get('month', '')
    if not forecast_month:
        today = timezone.now().date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    try:
        year, month = map(int, forecast_month.split('-'))
        start_date = datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = datetime(year, month, days_in_month).date()
    except (ValueError, IndexError):
        today = timezone.now().date()
        start_date = datetime(today.year, today.month, 1).date()
        days_in_month = monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, days_in_month).date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取活跃商机
    active_opportunities = BusinessOpportunity.objects.filter(is_active=True).exclude(
        status__in=['won', 'lost', 'cancelled']
    )
    
    # 权限过滤
    if not opportunity_can_view_all(permission_set):
        active_opportunities = active_opportunities.filter(business_manager=request.user)
    
    # 计算本月预计签约的商机
    month_opportunities = active_opportunities.filter(
        expected_sign_date__gte=start_date,
        expected_sign_date__lte=end_date
    )
    
    # 统计基础数据
    total_active = active_opportunities.count()
    total_weighted_amount = float(active_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    month_weighted_amount = float(month_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    
    # 计算历史转化率
    historical_queryset = BusinessOpportunity.objects.filter(is_active=True,
        status__in=['initial_contact', 'requirement_confirmed', 'quotation', 'negotiation', 'won']
    )
    if not opportunity_can_view_all(permission_set):
        historical_queryset = historical_queryset.filter(business_manager=request.user)
    
    historical_initial = historical_queryset.count()
    historical_won = historical_queryset.filter(status='won').count()
    
    historical_conversion_rate = 35.0  # 默认值
    if historical_initial > 0:
        historical_conversion_rate = (historical_won / historical_initial) * 100
    
    # 计算预测值
    optimistic_forecast = month_weighted_amount * (historical_conversion_rate / 100) * 1.2
    neutral_forecast = month_weighted_amount * (historical_conversion_rate / 100)
    conservative_forecast = month_weighted_amount * (historical_conversion_rate / 100) * 0.8
    
    # 目标差距分析
    monthly_target = total_weighted_amount * 0.6
    target_gap = monthly_target - neutral_forecast
    
    # 生成建议
    suggestions = []
    if target_gap > 0:
        suggestions.append('预测金额低于月度目标,建议加大商机开拓力度')
        suggestions.append('建议提升在途商机的转化率')
        suggestions.append('建议重点关注高价值商机,加快推进速度')
    else:
        suggestions.append('预测金额达到月度目标,继续保持')
        suggestions.append('建议持续跟进在途商机,确保按时签约')
    
    return Response({
        'month': forecast_month,
        'active_opportunities': total_active,
        'weighted_amount': total_weighted_amount,
        'historical_conversion_rate': historical_conversion_rate,
        'forecast': {
            'optimistic': optimistic_forecast,
            'neutral': neutral_forecast,
            'conservative': conservative_forecast
        },
        'target_gap': {
            'monthly_target': monthly_target,
            'gap': target_gap,
            'suggestions': suggestions
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_health_score_api(request, opportunity_id):
    """
    商机健康度评分API
    
    返回:
    {
        "health_score": int,  # 健康度评分(0-100)
        "health_level": str,  # 健康度等级(high/medium/low)
        "dimensions": {
            "followup_timeliness": {
                "score": int,
                "weight": float,
                "label": str
            },
            "information_completeness": {...},
            "client_interaction": {...},
            "stage_progress": {...}
        },
        "suggestions": [str]  # 改进建议
    }
    """
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.apps.opportunity_management.perm_check import opportunity_can_view, opportunity_can_view_all, opportunity_can_access_detail
    
    opportunity = BusinessOpportunity.objects.select_related('client').prefetch_related('followups').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = opportunity_can_access_detail(request.user, opportunity, permission_set)
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 更新健康度评分
    opportunity.save(update_health=True)
    
    # 获取详细分析
    analysis = opportunity.get_health_analysis()
    
    return Response({
        'health_score': opportunity.health_score,
        'health_level': analysis['health_level'],
        'dimensions': analysis['dimensions'],
        'suggestions': analysis['suggestions'],
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_quality_score_api(request, opportunity_id):
    """
    商机质量评分API
    
    返回:
    {
        "quality_score": int,  # 质量评分(0-100)
        "quality_level": str,  # 质量等级(A/B/C/D)
        "dimensions": {
            "client_qualification": {
                "score": int,
                "weight": float,
                "details": {...}
            },
            "project_reliability": {...},
            "competition_environment": {...}
        },
        "suggestions": [str]  # 改进建议
    }
    """
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.customer_management.models import ClientProject
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.apps.opportunity_management.perm_check import opportunity_can_view, opportunity_can_view_all, opportunity_can_access_detail
    
    opportunity = BusinessOpportunity.objects.select_related('client').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = opportunity_can_access_detail(request.user, opportunity, permission_set)
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 1. 客户资质评分(权重35%)
    client = opportunity.client
    client_qualification_score = 0
    client_details = {}
    
    # 客户信用
    if client.credit_level == 'excellent':
        credit_score = 30
    elif client.credit_level == 'good':
        credit_score = 20
    elif client.credit_level == 'normal':
        credit_score = 10
    else:
        credit_score = 5
    client_qualification_score += credit_score
    client_details['credit_level'] = {'score': credit_score, 'value': client.get_credit_level_display()}
    
    # 合作历史
    project_count = ClientProject.objects.filter(client=client).count()
    if project_count >= 3:
        history_score = 30
    elif project_count >= 1:
        history_score = 15
    else:
        history_score = 0
    client_qualification_score += history_score
    client_details['cooperation_history'] = {'score': history_score, 'value': f'{project_count}个项目'}
    
    # 法律风险
    if client.legal_risk_level == 'low':
        risk_score = 30
    elif client.legal_risk_level in ['medium_low', 'medium']:
        risk_score = 15
    elif client.legal_risk_level in ['medium_high', 'high']:
        risk_score = 0
    else:
        risk_score = 10
    client_qualification_score += risk_score
    client_details['legal_risk'] = {'score': risk_score, 'value': client.get_legal_risk_level_display()}
    
    # 客户资质总分(最高120分,按比例缩放到100分)
    client_qualification_score = min(client_qualification_score, 120) * (100 / 120)
    
    # 2. 项目靠谱程度评分(权重40%)
    project_reliability_score = 0
    project_details = {}
    
    # 项目阶段
    if opportunity.drawing_stage:
        drawing_stage_name = opportunity.drawing_stage.name
        if '施工图' in drawing_stage_name or '已立项' in drawing_stage_name:
            stage_score = 30
        elif '方案' in drawing_stage_name or '初步设计' in drawing_stage_name:
            stage_score = 20
        else:
            stage_score = 10
    else:
        stage_score = 5
    project_reliability_score += stage_score
    project_details['drawing_stage'] = {'score': stage_score, 'value': opportunity.drawing_stage.name if opportunity.drawing_stage else '未设置'}
    
    # 预算确认
    if opportunity.estimated_amount and opportunity.estimated_amount > 0:
        if opportunity.estimated_amount >= 100:
            budget_score = 30
        else:
            budget_score = 20
    else:
        budget_score = 10
    project_reliability_score += budget_score
    project_details['budget_confirmed'] = {'score': budget_score, 'value': f'预计金额:{opportunity.estimated_amount or 0}万元'}
    
    # 时间紧迫性
    if opportunity.urgency == 'very_urgent':
        urgency_score = 30
    elif opportunity.urgency == 'urgent':
        urgency_score = 20
    else:
        urgency_score = 10
    project_reliability_score += urgency_score
    project_details['urgency'] = {'score': urgency_score, 'value': opportunity.get_urgency_display()}
    
    # 项目信息完整度
    info_fields = ['project_name', 'project_address', 'project_type', 'building_area']
    filled_fields = sum(1 for field in info_fields if getattr(opportunity, field, None))
    completeness_score = (filled_fields / len(info_fields)) * 30
    project_reliability_score += completeness_score
    project_details['info_completeness'] = {'score': completeness_score, 'value': f'{filled_fields}/{len(info_fields)}个字段已填'}
    
    # 项目靠谱程度总分(最高120分,按比例缩放到100分)
    project_reliability_score = min(project_reliability_score, 120) * (100 / 120)
    
    # 3. 竞争环境评分(权重25%)
    competition_score = 0
    competition_details = {}
    
    # 竞争激烈度(简化版,基于商机状态判断)
    if opportunity.status in ['quotation', 'negotiation']:
        competition_score = 20  # 进入报价和谈判阶段,说明有一定竞争
    else:
        competition_score = 30  # 早期阶段,竞争较小
    competition_details['competition_intensity'] = {'score': competition_score, 'value': '基于商机阶段判断'}
    
    # 我方优势(简化版,基于健康度判断)
    if opportunity.health_score >= 80:
        advantage_score = 30
    elif opportunity.health_score >= 60:
        advantage_score = 20
    else:
        advantage_score = 10
    competition_score += advantage_score
    competition_details['our_advantage'] = {'score': advantage_score, 'value': f'健康度:{opportunity.health_score}分'}
    
    # 价格敏感度(简化版,基于客户等级判断)
    if client.client_level == 'vip':
        price_sensitivity_score = 30  # VIP客户价格敏感度低
    elif client.client_level == 'key':
        price_sensitivity_score = 20
    else:
        price_sensitivity_score = 10
    competition_score += price_sensitivity_score
    competition_details['price_sensitivity'] = {'score': price_sensitivity_score, 'value': client.get_client_level_display()}
    
    # 竞争环境总分(最高90分,按比例缩放到100分)
    competition_score = min(competition_score, 90) * (100 / 90)
    
    # 计算总质量评分
    quality_score = (
        client_qualification_score * 0.35 +
        project_reliability_score * 0.40 +
        competition_score * 0.25
    )
    
    # 确定质量等级
    if quality_score >= 80:
        quality_level = 'A'
    elif quality_score >= 60:
        quality_level = 'B'
    elif quality_score >= 40:
        quality_level = 'C'
    else:
        quality_level = 'D'
    
    # 生成建议
    suggestions = []
    if quality_score >= 80:
        suggestions.append('商机质量优秀,建议重点投入,优先跟进')
    elif quality_score >= 60:
        suggestions.append('商机质量良好,建议正常跟进,保持节奏')
    elif quality_score >= 40:
        suggestions.append('商机质量一般,建议观察维护,适度投入')
    else:
        suggestions.append('商机质量较低,建议低优先级,资源有限时暂停')
    
    if client_qualification_score < 60:
        suggestions.append('客户资质有待提升,建议加强客户关系维护')
    if project_reliability_score < 60:
        suggestions.append('项目信息不完整,建议完善项目信息')
    
    return Response({
        'quality_score': round(quality_score, 2),
        'quality_level': quality_level,
        'dimensions': {
            'client_qualification': {
                'score': round(client_qualification_score, 2),
                'weight': 0.35,
                'details': client_details
            },
            'project_reliability': {
                'score': round(project_reliability_score, 2),
                'weight': 0.40,
                'details': project_details
            },
            'competition_environment': {
                'score': round(competition_score, 2),
                'weight': 0.25,
                'details': competition_details
            }
        },
        'suggestions': suggestions
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_action_suggestions_api(request, opportunity_id):
    """
    智能行动建议API(基于结构化数据)
    
    返回:
    {
        "suggestions": [
            {
                "type": str,  # 建议类型(stage_overdue/info_incomplete/followup_overdue)
                "priority": str,  # 优先级(high/medium/low)
                "action": str,  # 建议行动
                "reason": str  # 原因说明
            }
        ]
    }
    """
    from backend.apps.opportunity_management.models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.apps.opportunity_management.perm_check import opportunity_can_view, opportunity_can_view_all, opportunity_can_access_detail
    
    opportunity = BusinessOpportunity.objects.prefetch_related('followups').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = opportunity_can_access_detail(request.user, opportunity, permission_set)
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    suggestions = []
    
    # 1. 检查阶段超期
    days_since_created = (timezone.now().date() - opportunity.created_time.date()).days
    
    # 各阶段的平均周期(天)
    average_durations = {
        'potential': 7,
        'initial_contact': 10,
        'requirement_confirmed': 15,
        'quotation': 20,
        'negotiation': 30,
    }
    
    average_duration = average_durations.get(opportunity.status, 15)
    if days_since_created > average_duration * 1.5:
        suggestions.append({
            'type': 'stage_overdue',
            'priority': 'high',
            'action': '立即提交方案' if opportunity.status == 'requirement_confirmed' else '加快跟进频率',
            'reason': f'当前阶段已停留{days_since_created}天,超过平均周期{average_duration}天'
        })
    
    # 2. 检查必填字段完整性
    required_fields = ['project_name', 'estimated_amount', 'expected_sign_date']
    missing_fields = [f for f in required_fields if not getattr(opportunity, f, None)]
    
    if missing_fields:
        suggestions.append({
            'type': 'info_incomplete',
            'priority': 'medium',
            'action': '完善必填信息',
            'reason': f'缺少必填字段:{", ".join(missing_fields)}'
        })
    
    # 3. 检查跟进及时性
    last_followup = opportunity.followups.order_by('-follow_date').first()
    if last_followup and last_followup.next_follow_date:
        days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
        if days_overdue > 0:
            suggestions.append({
                'type': 'followup_overdue',
                'priority': 'high',
                'action': '立即安排跟进',
                'reason': f'已超过预计跟进时间{days_overdue}天'
            })
    elif not last_followup:
        days_since_created = (timezone.now().date() - opportunity.created_time.date()).days
        if days_since_created > 3:
            suggestions.append({
                'type': 'followup_missing',
                'priority': 'high',
                'action': '尽快建立首次联系',
                'reason': f'商机创建已{days_since_created}天,尚未有跟进记录'
            })
    
    return Response({
        'suggestions': suggestions
    }, status=status.HTTP_200_OK)
