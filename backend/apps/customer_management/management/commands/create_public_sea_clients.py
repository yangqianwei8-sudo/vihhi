from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.customer_management.models import Client, ClientType, ClientGrade
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = '创建10个客户公海示例数据（用于测试）'
    
    def handle(self, *args, **options):
        self.stdout.write('开始创建客户公海示例数据...')
        
        # 获取第一个用户作为创建人
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('错误：系统中没有用户，请先创建用户'))
            return
        
        # 确保有客户类型（必填字段）
        client_type, _ = ClientType.objects.get_or_create(
            code='other',
            defaults={
                'name': '其他',
                'display_order': 99,
                'is_active': True,
                'description': '其他类型客户'
            }
        )
        
        # 测试数据模板 - 10个不同的公司
        company_data = [
            {
                'name': '北京建工集团有限公司',
                'credit_code': '91110000123456789X',
                'contact_name': '张总',
                'contact_position': '总经理',
                'phone': '010-12345678',
                'industry': '房地产开发',
                'region': '北京',
            },
            {
                'name': '上海建筑设计研究院',
                'credit_code': '91310000234567890Y',
                'contact_name': '李经理',
                'contact_position': '技术总监',
                'phone': '021-23456789',
                'industry': '建筑设计',
                'region': '上海',
            },
            {
                'name': '深圳科技发展有限公司',
                'credit_code': '91440300345678901Z',
                'contact_name': '王主任',
                'contact_position': '市场总监',
                'phone': '0755-34567890',
                'industry': '科技服务',
                'region': '深圳',
            },
            {
                'name': '广州城市建设集团',
                'credit_code': '91440100456789012A',
                'contact_name': '刘部长',
                'contact_position': '运营总监',
                'phone': '020-45678901',
                'industry': '工程施工',
                'region': '广州',
            },
            {
                'name': '杭州智能科技有限公司',
                'credit_code': '91330100567890123B',
                'contact_name': '陈总监',
                'contact_position': '项目经理',
                'phone': '0571-56789012',
                'industry': '科技服务',
                'region': '杭州',
            },
            {
                'name': '成都房地产开发有限公司',
                'credit_code': '91510100678901234C',
                'contact_name': '杨主管',
                'contact_position': '部门经理',
                'phone': '028-67890123',
                'industry': '房地产开发',
                'region': '成都',
            },
            {
                'name': '武汉工程咨询有限公司',
                'credit_code': '91420100789012345D',
                'contact_name': '赵经理',
                'contact_position': '业务主管',
                'phone': '027-78901234',
                'industry': '工程咨询',
                'region': '武汉',
            },
            {
                'name': '西安建筑装饰工程公司',
                'credit_code': '91610100890123456E',
                'contact_name': '孙主任',
                'contact_position': '技术经理',
                'phone': '029-89012345',
                'industry': '工程施工',
                'region': '西安',
            },
            {
                'name': '南京规划设计院',
                'credit_code': '91320100901234567F',
                'contact_name': '周部长',
                'contact_position': '商务经理',
                'phone': '025-90123456',
                'industry': '规划设计',
                'region': '南京',
            },
            {
                'name': '重庆基础设施建设集团',
                'credit_code': '91500000012345678G',
                'contact_name': '吴总监',
                'contact_position': '副总经理',
                'phone': '023-01234567',
                'industry': '工程施工',
                'region': '重庆',
            },
        ]
        
        # 创建10个公海客户
        created_count = 0
        for i, data in enumerate(company_data):
            try:
                # 随机选择客户等级和信用等级
                client_level = random.choice(['vip', 'important', 'general', 'potential'])
                credit_level = random.choice(['excellent', 'good', 'normal', 'poor', 'bad'])
                source = random.choice(['self_development', 'customer_referral', 'industry_exhibition', 'online_promotion', 'other'])
                
                # 创建客户（公海客户：responsible_user为None）
                client = Client.objects.create(
                    name=data['name'],
                    unified_credit_code=data['credit_code'],
                    client_level=client_level,
                    credit_level=credit_level,
                    client_type=client_type,  # 必填字段
                    source=source,
                    industry=data['industry'],
                    region=data['region'],
                    contact_name=data['contact_name'],
                    contact_position=data['contact_position'],
                    phone=data['phone'],
                    company_address=f'{data["region"]}市{data["industry"]}区',
                    company_email=f'contact{i+1}@{data["name"][:4].lower()}.com',
                    description=f'客户公海示例数据 - {data["name"]}',
                    is_active=True,
                    responsible_user=None,  # 公海客户：没有负责人
                    public_sea_entry_time=timezone.now(),
                    public_sea_reason='unassigned',  # 未分配
                    created_by=user,
                    total_contract_amount=0,
                    total_payment_amount=0,
                    health_score=0,
                    score=0,
                )
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建公海客户 {i+1}/10: {data["name"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 创建公海客户失败 {data["name"]}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n成功创建 {created_count} 个客户公海示例数据！'))
        self.stdout.write(self.style.SUCCESS('这些客户可以在"客户管理 -> 客户信息管理 -> 客户公海"页面查看。'))






