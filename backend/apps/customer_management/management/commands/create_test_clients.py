from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.customer_management.models import Client
from django.db.models import Max
import random

User = get_user_model()

class Command(BaseCommand):
    help = '创建10个随机测试客户'
    
    def handle(self, *args, **options):
        self.stdout.write('开始创建测试客户...')
        
        # 获取第一个用户作为创建人
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('错误：系统中没有用户，请先创建用户'))
            return
        
        # 生成客户编码
        # 注意：Client模型中没有code字段，使用id作为标识
        # max_code = Client.objects.filter(code__regex=r'^KH\d+$').aggregate(max_num=Max('code'))['max_num']
        max_code = None
        if max_code:
            try:
                seq = int(max_code[2:]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        
        # 测试数据模板
        company_names = [
            '北京建工集团有限公司',
            '上海建筑设计研究院',
            '深圳科技发展有限公司',
            '广州城市建设集团',
            '杭州智能科技有限公司',
            '成都房地产开发有限公司',
            '武汉工程咨询有限公司',
            '西安建筑装饰工程公司',
            '南京规划设计院',
            '重庆基础设施建设集团'
        ]
        
        short_names = [
            '北京建工', '上海设计院', '深圳科技', '广州城建', '杭州智能',
            '成都地产', '武汉工程', '西安装饰', '南京规划', '重庆基建'
        ]
        
        contact_names = [
            '张总', '李经理', '王主任', '刘部长', '陈总监',
            '杨主管', '赵经理', '孙主任', '周部长', '吴总监'
        ]
        
        positions = [
            '总经理', '副总经理', '技术总监', '市场总监', '运营总监',
            '项目经理', '部门经理', '业务主管', '技术经理', '商务经理'
        ]
        
        phones = [
            '010-12345678', '021-23456789', '0755-34567890', '020-45678901', '0571-56789012',
            '028-67890123', '027-78901234', '029-89012345', '025-90123456', '023-01234567'
        ]
        
        # 创建10个客户
        created_count = 0
        for i in range(10):
            # 注意：Client模型中没有code字段，不再生成客户编码
            # code = f'KH{seq:06d}'
            # seq += 1
            
            # 随机选择数据
            name = company_names[i]
            # short_name 字段已删除，不再使用
            # short_name = short_names[i]
            contact_name = random.choice(contact_names)
            contact_position = random.choice(positions)
            phone = phones[i]
            
            # 生成统一社会信用代码（18位，格式：91 + 6位地区码 + 8位日期 + 1位校验码 + 1位随机）
            credit_code = f'91{random.randint(100000, 999999)}{random.randint(20000101, 20231231)}{random.randint(0, 9)}{random.choice("0123456789ABCDEFGHJKLMNPQRTUWXY")}'
            
            # 随机选择分类（确保必填字段有值）
            client_level = random.choice(['vip', 'important', 'general', 'potential'])
            grade = random.choice(['strategic', 'core', 'potential', 'regular', 'nurturing', 'observing', None])
            credit_level = random.choice(['excellent', 'good', 'normal', 'poor', 'bad'])
            client_type = random.choice(['developer', 'government', 'design_institute', 'general_contractor', 'other'])
            company_scale = random.choice(['large', 'medium', 'small'])
            source = random.choice(['self_development', 'customer_referral', 'industry_exhibition', 'online_promotion', 'other'])
            industry = random.choice(['房地产开发', '建筑设计', '工程施工', '工程咨询', '规划设计', '科技服务', ''])
            region = random.choice(['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '西安', '南京', '重庆', ''])
            
            # 创建客户（使用原始SQL，只插入存在的字段）
            try:
                from django.db import connection
                from django.utils import timezone
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO customer_client 
                        (name, unified_credit_code, client_level, grade, 
                         credit_level, client_type, source, industry, region,
                         contact_name, contact_position, phone, company_address, company_email, description,
                         is_active, created_time, updated_time, created_by_id, 
                         total_contract_amount, total_payment_amount, health_score, score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        name, credit_code, client_level, grade,
                        credit_level, client_type, source, industry, region,
                        contact_name, contact_position, phone, '', '', '测试客户',
                        True, timezone.now(), timezone.now(), user.id, 0, 0, 0, 0
                    ])
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建客户: {name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 创建客户失败 {name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n成功创建 {created_count} 个测试客户！'))

