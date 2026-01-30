"""
为姜松琴创建 2026 年 2 月个人月度行动计划（与田霞同结构，目标值按 120万/300万=0.4 缩放）。
使用方法: python manage.py create_jiang_monthly_plans
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = '为姜松琴创建 2026 年 2 月 4 条个人月度行动计划（关联 GOAL-20260129-0009，目标值按 0.4 缩放）'

    def handle(self, *args, **options):
        from backend.apps.plan_management.models import Plan, StrategicGoal
        from backend.apps.system_management.models import OurCompany, Department

        # 1. 查找姜松琴（姓名可能存 first_name+last_name 或 first_name）
        jiang = User.objects.filter(
            Q(first_name__contains='姜松琴') |
            Q(last_name__contains='姜松琴') |
            Q(first_name='姜', last_name='松琴') |
            Q(first_name='姜松琴')
        ).first()
        if not jiang:
            # 尝试通过 get_full_name 包含
            for u in User.objects.all()[:500]:
                if u.get_full_name() and '姜松琴' in (u.get_full_name() or ''):
                    jiang = u
                    break
        if not jiang:
            self.stdout.write(self.style.ERROR('未找到用户“姜松琴”，请确认系统中存在该用户（first_name/last_name 或姓名包含姜松琴）'))
            return

        self.stdout.write(f'负责人: {jiang.username} ({jiang.get_full_name() or jiang.username})')

        # 2. 关联战略目标
        goal = StrategicGoal.objects.filter(goal_number='GOAL-20260129-0009').first()
        if not goal:
            self.stdout.write(self.style.ERROR('未找到战略目标 GOAL-20260129-0009，请先创建该目标'))
            return
        self.stdout.write(f'关联目标: {goal.goal_number} - {goal.name}')

        # 3. 公司、部门
        company = getattr(goal, 'company', None)
        if not company:
            company = OurCompany.objects.filter(is_active=True).order_by('order', 'id').first()
        dept = getattr(jiang, 'department', None)
        if not dept and hasattr(jiang, 'profile') and getattr(jiang.profile, 'department', None):
            dept = jiang.profile.department
        self.stdout.write(f'公司: {getattr(company, "company_name", None) or getattr(company, "name", "未设置")}')
        self.stdout.write(f'部门: {dept.name if dept else "未设置"}')

        # 4. 2026 年 2 月时间范围
        start_time = timezone.make_aware(datetime(2026, 2, 1, 0, 0, 0))
        end_time = timezone.make_aware(datetime(2026, 2, 28, 23, 59, 59))

        # 5. 四条月计划（与田霞同结构，金额/数量按 0.4 缩放；百分比、份数等不变）
        plans_data = [
            {
                'name': '2月销售收入达成与项目签约冲刺计划',
                'plan_objective': '推进至少 2 个重点意向项目至签约，力争月度销售收入 8 万元；签约≥1 单（≥6 万），另 1 单进入审批。',
                'content': '梳理当前重点意向项目，明确 2 个以上可推进至签约的项目；制定签约节奏与审批跟进表；协调内外部资源推动合同审批与签署；力争本月完成至少 1 单签约（单笔≥6 万元），另 1 单进入审批流程；月度销售收入目标 8 万元。',
                'acceptance_criteria': '月度销售收入达成 8 万元；签约≥1 单且单笔金额≥6 万元；另 1 单已提交审批或进入审批流程；重点意向项目清单与推进记录完整。',
            },
            {
                'name': '新客户线索拓展与春节关系维护计划',
                'plan_objective': '新增≥2 条合格线索，春节祝福 100% 送达，节后重点客户拜访 100%。',
                'content': '通过行业活动、老客户转介绍、线上推广等渠道拓展新线索，本月新增不少于 2 条合格线索并录入系统；春节前完成重点客户及合作方名单梳理，发送春节祝福（短信/微信/邮件），确保 100% 送达；节后第一周内完成重点客户拜访计划并执行，拜访完成率 100%。',
                'acceptance_criteria': '新增合格线索≥2 条且已录入系统；春节祝福送达率 100%（有记录）；节后重点客户拜访计划已制定且执行率 100%。',
            },
            {
                'name': '战略客户新年计划深度沟通计划',
                'plan_objective': '与 1–2 家战略客户完成年度合作规划会议，产出纪要并明确≥1 个可跟进项目。',
                'content': '选定 1–2 家战略客户，预约并召开新年/年度合作规划会议；会议中沟通双方年度目标、项目计划与需求，形成会议纪要；基于会议结论明确至少 1 个可跟进项目或合作意向，并列入后续跟进清单。',
                'acceptance_criteria': '完成 1–2 家战略客户的年度合作规划会议；会议纪要不缺失；至少 1 个可跟进项目或合作意向已明确并列入跟进清单。',
            },
            {
                'name': '销售案例复盘与行业学习计划',
                'plan_objective': '完成 1 份≥1000 字案例复盘、1 页“行业趋势与价值主张”要点文档。',
                'content': '选取近期成单或丢单案例进行复盘，形成不少于 1000 字的案例复盘文档（含背景、过程、得失、改进措施）；整理行业动态与公司价值主张，输出 1 页“行业趋势与价值主张”要点文档，用于对外沟通与内部学习。',
                'acceptance_criteria': '案例复盘文档≥1000 字且结构完整；“行业趋势与价值主张”要点文档 1 页已输出并可复用。',
            },
        ]

        created = []
        for data in plans_data:
            plan = Plan(
                name=data['name'],
                level='personal',
                plan_period='monthly',
                status='draft',
                related_goal=goal,
                plan_objective=data['plan_objective'],
                content=data['content'],
                acceptance_criteria=data['acceptance_criteria'],
                start_time=start_time,
                end_time=end_time,
                owner=jiang,
                responsible_person=jiang,
                created_by=jiang,
                company=company,
                org_department=dept,
                responsible_department=dept,
            )
            plan.save()
            created.append(plan)
            self.stdout.write(self.style.SUCCESS(f'  ✓ 创建计划: {plan.plan_number} - {plan.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n已为姜松琴创建 {len(created)} 条 2026 年 2 月月度行动计划'))
