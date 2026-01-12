"""
创建工作计划测试数据
使用方法: python manage.py create_test_plans
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.apps import apps

# 使用 get_user_model() 避免直接导入 User
User = get_user_model()
Plan = apps.get_model('plan_management', 'Plan')
# 尝试获取 Company，如果 org 应用未安装则使用 None
try:
    Company = apps.get_model('org', 'Company')
except LookupError:
    Company = None


class Command(BaseCommand):
    help = '创建三条工作计划测试数据'

    def handle(self, *args, **options):
        # 获取负责人用户
        try:
            user = User.objects.get(username='13880399996')
            self.stdout.write(f'负责人: {user.username}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('用户 13880399996 不存在'))
            return

        # 获取用户的公司信息
        try:
            profile = user.profile
            company = profile.company
            org_dept = profile.department
            self.stdout.write(f'公司: {company.name if company else "未设置"}')
            self.stdout.write(f'部门: {org_dept.name if org_dept else "未设置"}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'获取用户信息失败: {e}'))
            if Company:
                company = Company.objects.first()
                org_dept = None
                if company:
                    self.stdout.write(f'使用默认公司: {company.name}')
            else:
                company = None
                org_dept = None
                self.stdout.write(self.style.WARNING('org 应用未安装，无法设置公司信息'))

        # 创建三条测试计划
        test_plans = [
            {
                'name': 'Q1季度销售目标达成计划',
                'plan_type': 'department',
                'plan_period': 'quarterly',
                'status': 'in_progress',
                'content': '完成Q1季度销售目标，包括客户拓展、合同签署、回款跟进等工作。重点推进新客户开发，维护现有客户关系，确保合同按时签署和回款。',
                'plan_objective': 'Q1季度销售额达到500万元，新签合同10个，回款率达到80%以上。',
                'start_time': timezone.now() - timedelta(days=5),
                'end_time': timezone.now() + timedelta(days=85),
                'progress': 30,
            },
            {
                'name': '产品功能优化迭代计划',
                'plan_type': 'project',
                'plan_period': 'monthly',
                'status': 'in_progress',
                'content': '对现有产品进行功能优化和迭代，提升用户体验和系统性能。包括前端界面优化、后端性能调优、数据库查询优化等工作。',
                'plan_objective': '完成核心功能优化，提升系统响应速度30%，用户满意度达到90%以上。',
                'start_time': timezone.now() - timedelta(days=10),
                'end_time': timezone.now() + timedelta(days=20),
                'progress': 45,
            },
            {
                'name': '团队能力提升培训计划',
                'plan_type': 'department',
                'plan_period': 'monthly',
                'status': 'pending_approval',
                'content': '组织团队参加专业技能培训，提升团队整体能力和协作效率。包括技术培训、管理培训、沟通技巧培训等。',
                'plan_objective': '完成全员培训，通过率100%，提升团队专业技能水平，增强团队协作能力。',
                'start_time': timezone.now() + timedelta(days=5),
                'end_time': timezone.now() + timedelta(days=35),
                'progress': 0,
            },
        ]

        created_plans = []
        for i, plan_data in enumerate(test_plans, 1):
            plan = Plan()
            plan.plan_number = plan.generate_plan_number()
            plan.name = plan_data['name']
            plan.plan_type = plan_data['plan_type']
            plan.plan_period = plan_data['plan_period']
            plan.status = plan_data['status']
            plan.content = plan_data['content']
            plan.plan_objective = plan_data['plan_objective']
            plan.start_time = plan_data['start_time']
            plan.end_time = plan_data['end_time']
            plan.duration_days = plan.calculate_duration_days()
            plan.responsible_person = user
            plan.created_by = user
            plan.company = company
            plan.org_department = org_dept
            plan.progress = plan_data['progress']
            
            plan.save()
            created_plans.append(plan)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ 创建计划 {i}: {plan.plan_number} - {plan.name}'
                )
            )
            self.stdout.write(f'   状态: {plan.get_status_display()}')
            self.stdout.write(f'   类型: {plan.get_plan_type_display()}')
            self.stdout.write(f'   周期: {plan.get_plan_period_display()}')
            self.stdout.write(f'   进度: {plan.progress}%')

        self.stdout.write(
            self.style.SUCCESS(f'\n总共创建了 {len(created_plans)} 条工作计划测试数据')
        )

