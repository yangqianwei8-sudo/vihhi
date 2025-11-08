from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.system_management.models import Department, DataDictionary
from backend.apps.customer_success.models import Client, ClientContact
from backend.apps.project_center.models import Project, ProjectTeam, PaymentPlan
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = '初始化演示数据'
    
    def handle(self, *args, **options):
        self.stdout.write('开始初始化演示数据...')
        
        # 创建部门
        tech_dept, created = Department.objects.get_or_create(
            name='技术部',
            code='TECH',
            defaults={'description': '技术研发和项目执行部门'}
        )
        
        business_dept, created = Department.objects.get_or_create(
            name='商务部', 
            code='BUSINESS',
            defaults={'description': '商务洽谈和客户管理'}
        )
        
        # 创建测试用户
        admin_user = User.objects.get(username='admin')  # 使用已存在的admin用户
        
        demo_user, created = User.objects.get_or_create(
            username='demo_manager',
            defaults={
                'email': 'manager@weihai.com',
                'first_name': '张',
                'last_name': '经理',
                'department': tech_dept,
                'position': '项目经理'
            }
        )
        if created:
            demo_user.set_password('demo123456')
            demo_user.save()
        
        # 创建数据字典
        dict_data = [
            # 项目相关
            {'code': 'SERVICE_DESIGN_OPT', 'name': '设计优化', 'value': 'design_optimization', 'dict_type': 'project'},
            {'code': 'SERVICE_DETAIL_REVIEW', 'name': '精细化审图', 'value': 'detailed_review', 'dict_type': 'project'},
            {'code': 'SERVICE_FULL_PROCESS', 'name': '全过程设计咨询', 'value': 'full_process_consulting', 'dict_type': 'project'},
            
            # 业态类型
            {'code': 'BUSINESS_RESIDENTIAL', 'name': '住宅', 'value': 'residential', 'dict_type': 'project'},
            {'code': 'BUSINESS_COMMERCIAL', 'name': '商业', 'value': 'commercial', 'dict_type': 'project'},
            {'code': 'BUSINESS_OFFICE', 'name': '办公', 'value': 'office', 'dict_type': 'project'},
            
            # 设计阶段
            {'code': 'STAGE_SCHEMATIC', 'name': '方案设计', 'value': 'schematic', 'dict_type': 'project'},
            {'code': 'STAGE_PRELIMINARY', 'name': '初步设计', 'value': 'preliminary', 'dict_type': 'project'},
            {'code': 'STAGE_CONSTRUCTION', 'name': '施工图设计', 'value': 'construction', 'dict_type': 'project'},
        ]
        
        for item in dict_data:
            DataDictionary.objects.get_or_create(
                code=item['code'],
                defaults=item
            )
        
        # 创建示例客户
        client, created = Client.objects.get_or_create(
            code='C2024001',
            defaults={
                'name': '成都示范建筑有限公司',
                'short_name': '示范建筑',
                'client_level': 'vip',
                'credit_level': 'excellent', 
                'industry': '房地产开发',
                'address': '成都市高新区天府大道100号',
                'phone': '028-87654321',
                'email': 'contact@demo-arch.com',
                'description': '重要合作伙伴，长期客户',
                'created_by': admin_user
            }
        )
        
        # 创建客户联系人
        if created:
            ClientContact.objects.create(
                client=client,
                name='李总监',
                position='技术总监',
                department='技术部',
                phone='13800138000',
                email='li@demo-arch.com',
                is_primary=True,
                notes='主要技术对接人'
            )
        
        # 创建示例项目
        project, created = Project.objects.get_or_create(
            project_number='WH202411001',
            defaults={
                'name': '示范商业综合体设计优化项目',
                'description': '位于高新区核心地段的商业综合体项目，包含购物中心、写字楼和酒店',
                'service_type': 'design_optimization',
                'business_type': 'commercial',
                'design_stage': 'schematic',
                'client': client,
                'design_company': '示范建筑设计院',
                'client_contact': '李总监',
                'client_phone': '13800138000',
                'project_manager': demo_user,
                'created_by': admin_user,
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timedelta(days=90),
                'contract_amount': 500000.00,
                'estimated_cost': 350000.00,
                'status': 'in_progress'
            }
        )
        
        # 创建项目团队
        if created:
            ProjectTeam.objects.create(
                project=project,
                user=demo_user,
                role='project_manager',
                join_date=timezone.now().date(),
                responsibility='全面负责项目管理和客户沟通'
            )
            
            ProjectTeam.objects.create(
                project=project,
                user=admin_user,
                role='technical_director', 
                join_date=timezone.now().date(),
                responsibility='技术指导和方案审核'
            )
        
        # 创建回款计划
        if created:
            PaymentPlan.objects.create(
                project=project,
                phase_name='合同签订',
                phase_description='项目启动，合同签订后首付款',
                planned_amount=150000.00,
                planned_date=timezone.now().date() + timedelta(days=7),
                status='pending'
            )
            
            PaymentPlan.objects.create(
                project=project,
                phase_name='中期汇报',
                phase_description='方案中期汇报通过后付款',
                planned_amount=200000.00, 
                planned_date=timezone.now().date() + timedelta(days=45),
                status='pending'
            )
            
            PaymentPlan.objects.create(
                project=project,
                phase_name='项目完成',
                phase_description='项目最终成果交付后尾款',
                planned_amount=150000.00,
                planned_date=timezone.now().date() + timedelta(days=90),
                status='pending'
            )
        
        self.stdout.write(
            self.style.SUCCESS('演示数据初始化完成！')
        )
        self.stdout.write('可以访问以下链接查看效果：')
        self.stdout.write('  - 首页: http://localhost:8000/')
        self.stdout.write('  - 管理后台: http://localhost:8000/admin/')
        self.stdout.write('  - API接口: http://localhost:8000/api/')
        self.stdout.write('  - 项目列表: http://localhost:8000/api/project/projects/')
