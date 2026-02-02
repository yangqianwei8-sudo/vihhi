# 客户管理首页
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

from .common import (
    login_required,
    get_user_permission_codes,
    _permission_granted,
    _build_full_top_nav,
    Client,
    ClientContact,
    CustomerRelationship,
    VisitPlan,
    BusinessOpportunity,
    opportunity_can_view,
    logger,
)
from .menu import _build_customer_management_sidebar_nav


@login_required
def customer_management_home(request):
    """客户管理首页"""
    summary_cards = []
    sections = []
    try:
        permission_set = get_user_permission_codes(request.user)
        user = request.user
        is_admin = getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)
        summary_cards = []

        try:
            from datetime import timedelta
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            this_month_start = today.replace(day=1)
            last_30_days_start = today - timedelta(days=30)

            if is_admin or _permission_granted('customer_management.client.view', permission_set):
                total_clients = Client.objects.count()
                clients_yesterday = Client.objects.filter(created_time__date__lte=yesterday).count()
                clients_last_week = Client.objects.filter(created_time__date__lte=last_week).count()
                change_vs_yesterday = total_clients - clients_yesterday
                change_vs_last_week = total_clients - clients_last_week
                hint_parts = []
                if change_vs_yesterday != 0:
                    arrow = '↑' if change_vs_yesterday > 0 else '↓'
                    hint_parts.append(f'较昨日{arrow}{abs(change_vs_yesterday)}')
                if change_vs_last_week != 0:
                    arrow = '↑' if change_vs_last_week > 0 else '↓'
                    hint_parts.append(f'较上周{arrow}{abs(change_vs_last_week)}')
                hint_text = ' · '.join(hint_parts) if hint_parts else '所有客户数量'
                try:
                    summary_cards.append({
                        'label': '客户总数',
                        'value': total_clients,
                        'hint': hint_text,
                        'url': reverse('business_pages:customer_list'),
                        'change_vs_yesterday': change_vs_yesterday,
                        'change_vs_last_week': change_vs_last_week,
                    })
                except NoReverseMatch:
                    summary_cards.append({
                        'label': '客户总数',
                        'value': total_clients,
                        'hint': hint_text,
                        'change_vs_yesterday': change_vs_yesterday,
                        'change_vs_last_week': change_vs_last_week,
                    })

            if is_admin or _permission_granted('customer_management.client.view', permission_set):
                new_clients_today = Client.objects.filter(created_time__date=today).count()
                new_clients_month = Client.objects.filter(created_time__gte=this_month_start).count()
                try:
                    summary_cards.append({
                        'label': '新增客户数',
                        'value': new_clients_month,
                        'hint': f'今日新增 {new_clients_today} 个',
                        'url': reverse('business_pages:customer_list'),
                    })
                except NoReverseMatch:
                    summary_cards.append({
                        'label': '新增客户数',
                        'value': new_clients_month,
                        'hint': f'今日新增 {new_clients_today} 个',
                    })

            if is_admin or _permission_granted('customer_management.client.view', permission_set):
                active_client_ids = set()
                try:
                    recent_relationships = CustomerRelationship.objects.filter(
                        created_time__gte=last_30_days_start
                    ).values_list('client_id', flat=True).distinct()
                    active_client_ids.update(recent_relationships)
                except Exception:
                    pass
                try:
                    recent_visits = VisitPlan.objects.filter(
                        created_time__gte=last_30_days_start
                    ).values_list('client_id', flat=True).distinct()
                    active_client_ids.update(recent_visits)
                except Exception:
                    pass
                try:
                    recent_opportunities = BusinessOpportunity.objects.filter(
                        is_active=True, created_time__gte=last_30_days_start
                    ).values_list('client_id', flat=True).distinct()
                    active_client_ids.update(recent_opportunities)
                except Exception:
                    pass
                active_clients_count = len(active_client_ids)
                try:
                    summary_cards.append({
                        'label': '联系人总数',
                        'value': active_clients_count,
                        'hint': '最近30天有交互记录的客户数量',
                        'url': reverse('business_pages:customer_list'),
                    })
                except NoReverseMatch:
                    summary_cards.append({
                        'label': '联系人总数',
                        'value': active_clients_count,
                        'hint': '最近30天有交互记录的客户数量',
                    })

            if is_admin or _permission_granted('customer_management.client.view', permission_set):
                new_contacts_today = ClientContact.objects.filter(created_time__date=today).count()
                new_contacts_month = ClientContact.objects.filter(created_time__gte=this_month_start).count()
                try:
                    summary_cards.append({
                        'label': '新增联系人数',
                        'value': new_contacts_month,
                        'hint': f'今日新增 {new_contacts_today} 个',
                        'url': reverse('business_pages:contact_list'),
                    })
                except NoReverseMatch:
                    summary_cards.append({
                        'label': '新增联系人数',
                        'value': new_contacts_month,
                        'hint': f'今日新增 {new_contacts_today} 个',
                    })
        except Exception as e:
            logger.exception('获取统计数据失败: %s', str(e))

        sections = []
        quick_actions = []
        if is_admin or _permission_granted('customer_management.client.create', permission_set):
            try:
                quick_actions.append({
                    'label': '创建新客户',
                    'icon': '➕',
                    'description': '添加新客户信息',
                    'url': reverse('business_pages:customer_create'),
                    'link_label': '创建客户 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('customer_management.client.create', permission_set):
            try:
                quick_actions.append({
                    'label': '创建联系人',
                    'icon': '👤',
                    'description': '添加客户联系人',
                    'url': reverse('business_pages:contact_create'),
                    'link_label': '创建联系人 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('customer_management.relationship.create', permission_set):
            try:
                quick_actions.append({
                    'label': '新建联系人拜访',
                    'icon': '📅',
                    'description': '创建新的拜访记录',
                    'url': reverse('business_pages:visit_plan_create'),
                    'link_label': '创建拜访 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('customer_management.relationship.upgrade', permission_set):
            try:
                quick_actions.append({
                    'label': '新建人员关系升级',
                    'icon': '⬆️',
                    'description': '记录人员关系升级',
                    'url': reverse('business_pages:customer_relationship_upgrade_create'),
                    'link_label': '创建升级 →'
                })
            except NoReverseMatch:
                pass
        if quick_actions:
            sections.append({
                'title': '快速操作',
                'description': '常用的快速操作入口',
                'items': quick_actions
            })

        modules = []
        if is_admin or _permission_granted('customer_management.client.view', permission_set):
            try:
                modules.append({
                    'label': '客户信息管理',
                    'icon': '👥',
                    'description': '管理客户基本信息，查看客户列表和详情',
                    'url': reverse('business_pages:customer_list'),
                    'link_label': '进入模块 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('customer_management.client.view', permission_set):
            try:
                modules.append({
                    'label': '人员信息管理',
                    'icon': '👤',
                    'description': '管理客户联系人信息，维护人员关系',
                    'url': reverse('business_pages:contact_list'),
                    'link_label': '进入模块 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or opportunity_can_view(permission_set):
            try:
                modules.append({
                    'label': '商机管理',
                    'icon': '💼',
                    'description': '管理商机信息，跟踪商机进展',
                    'url': reverse('opportunity_pages:opportunity_management'),
                    'link_label': '进入模块 →'
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('contract_management.contract.view', permission_set):
            try:
                modules.append({
                    'label': '合同管理',
                    'icon': '📄',
                    'description': '管理合同信息，跟踪合同状态',
                    'url': reverse('contract_pages:contract_management_list'),
                    'link_label': '进入模块 →'
                })
            except NoReverseMatch:
                pass
        if modules:
            sections.append({
                'title': '功能模块',
                'description': '客户管理的各个功能模块入口',
                'items': modules
            })

        recent_notices = []
        try:
            if is_admin or _permission_granted('customer_management.relationship.view', permission_set):
                try:
                    recent_feedbacks = CustomerRelationship.objects.filter(
                        content__isnull=False
                    ).exclude(content='').select_related('client', 'created_by', 'followup_person').order_by('-followup_time')[:5]
                    for feedback in recent_feedbacks:
                        feedback_preview = feedback.content[:50] + '...' if len(feedback.content) > 50 else feedback.content
                        recent_notices.append({
                            'type': 'info',
                            'icon': '💬',
                            'title': f'最新反馈 - {feedback.client.name if feedback.client else "未知客户"}',
                            'content': feedback_preview,
                            'date': feedback.followup_time.date() if hasattr(feedback.followup_time, "date") else feedback.followup_time,
                            'author': feedback.created_by.username if feedback.created_by else '',
                        })
                except Exception as e:
                    logger.warning('获取最新反馈失败: %s', str(e))
        except Exception as e:
            logger.exception('获取最近动态失败: %s', str(e))

        core_cards = []
        for card in summary_cards:
            core_cards.append({
                'label': card.get('label', ''),
                'icon': card.get('icon', '📊'),
                'value': str(card.get('value', 0)),
                'subvalue': card.get('hint', ''),
                'url': card.get('url', '#'),
            })

        top_actions = []
        if is_admin or _permission_granted('customer_management.client.create', permission_set):
            try:
                top_actions.append({
                    'label': '创建客户',
                    'icon': '➕',
                    'url': reverse('customer_pages:customer_create'),
                })
            except NoReverseMatch:
                pass
        if is_admin or _permission_granted('customer_management.client.create', permission_set):
            try:
                top_actions.append({
                    'label': '创建联系人',
                    'icon': '👤',
                    'url': reverse('customer_pages:contact_create'),
                })
            except NoReverseMatch:
                pass

        risk_warnings = []
        overdue_customers_count = 0
        stale_customers_count = 0
        todo_items = []
        pending_approval_count = 0
        upcoming_deadline_count = 0

        my_work = {}
        try:
            my_customers = Client.objects.filter(business_manager=request.user).select_related('business_manager')[:5]
            my_work['my_customers'] = [
                {
                    'name': c.name,
                    'status': c.get_status_display() if hasattr(c, 'get_status_display') else '正常',
                    'url': reverse('customer_pages:customer_detail', args=[c.id]),
                }
                for c in my_customers
            ]
            my_work['my_customers_count'] = Client.objects.filter(business_manager=request.user).count()
        except Exception:
            pass

        recent_activities = {}
        try:
            recent_customers = Client.objects.select_related('created_by', 'business_manager').order_by('-created_time')[:5]
            recent_activities['recent_customers'] = [{
                'title': c.name,
                'creator': c.created_by.get_full_name() or c.created_by.username if c.created_by else '系统',
                'time': c.created_time,
                'url': reverse('customer_pages:customer_detail', args=[c.id])
            } for c in recent_customers]
        except Exception:
            recent_activities['recent_customers'] = []
        try:
            recent_contacts = ClientContact.objects.select_related('client', 'created_by').order_by('-created_time')[:5]
            recent_activities['recent_contacts'] = [{
                'title': f'{c.name} - {c.client.name if c.client else "未知客户"}',
                'creator': c.created_by.get_full_name() or c.created_by.username if c.created_by else '系统',
                'time': c.created_time,
                'url': reverse('customer_pages:contact_detail', args=[c.id])
            } for c in recent_contacts]
        except Exception:
            recent_activities['recent_contacts'] = []

        context = {
            'page_title': '客户管理',
            'page_icon': '👥',
            'description': '客户管理首页，管理客户信息、联系人、商机等业务数据。',
            'core_cards': core_cards,
            'top_actions': top_actions,
            'risk_warnings': risk_warnings,
            'todo_items': todo_items,
            'my_work': my_work,
            'recent_activities': recent_activities,
            'overdue_customers_count': overdue_customers_count,
            'stale_customers_count': stale_customers_count,
            'pending_approval_count': pending_approval_count,
            'upcoming_deadline_count': upcoming_deadline_count,
            'todo_summary_url': reverse('customer_pages:customer_list'),
            'summary_cards': summary_cards,
            'sections': sections,
            'recent_notices': recent_notices[:10],
            'sidebar_module_title': '客户管理',
            'sidebar_module_subtitle': 'Customer Management',
        }
        if request and request.user.is_authenticated:
            permission_set = get_user_permission_codes(request.user)
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            active_id = 'customer_home'
            context['sidebar_nav'] = _build_customer_management_sidebar_nav(permission_set, request.path, active_id=active_id)
            context['sidebar_title'] = '客户管理'
            context['sidebar_subtitle'] = 'Customer Management'
        else:
            context['full_top_nav'] = []
            context['sidebar_nav'] = []
        return render(request, "customer_management/customer_management_home.html", context)
    except Exception as e:
        logger.exception('customer_management_home 视图函数执行失败: %s', str(e))
        messages.error(request, f'页面加载失败: {str(e)}')
        try:
            context = {
                'page_title': '客户管理',
                'page_icon': '👥',
                'description': '客户管理首页',
                'summary_cards': summary_cards,
                'sections': sections,
                'sidebar_module_title': '客户管理',
                'sidebar_module_subtitle': 'Customer Management',
            }
            if request and request.user.is_authenticated:
                permission_set = get_user_permission_codes(request.user)
                context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
                active_id = 'customer_home'
                context['sidebar_nav'] = _build_customer_management_sidebar_nav(permission_set, request.path, active_id=active_id)
                context['sidebar_title'] = '客户管理'
                context['sidebar_subtitle'] = 'Customer Management'
            else:
                context['full_top_nav'] = []
                context['sidebar_nav'] = []
            return render(request, "customer_management/customer_management_home.html", context)
        except Exception as inner_e:
            logger.exception('渲染错误页面也失败: %s', str(inner_e))
            return redirect('home')


def _get_opportunities_safely(queryset, permission_set, user):
    """安全获取商机列表，处理新字段可能不存在的情况"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'business_opportunity' AND column_name = 'opportunity_type'
            """)
            has_new_fields = cursor.fetchone() is not None
    except Exception:
        has_new_fields = False
    if has_new_fields:
        return queryset
    try:
        return queryset.defer('opportunity_type', 'service_type')
    except Exception:
        return queryset.values('id', 'name', 'client_id', 'client__name', 'business_manager_id')
