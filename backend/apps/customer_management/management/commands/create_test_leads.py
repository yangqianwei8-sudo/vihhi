from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.customer_management.models import CustomerLead
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = '创建测试客户线索数据'
    
    def handle(self, *args, **options):
        self.stdout.write('开始创建测试客户线索...')
        
        # 获取创建人（使用第一个活跃用户）
        creator = User.objects.filter(is_active=True).first()
        if not creator:
            creator = User.objects.filter(username='admin').first()
        if not creator:
            self.stdout.write(self.style.ERROR('错误：找不到可用的用户，请先创建用户'))
            return
        
        self.stdout.write(f'使用创建人：{creator.username}')
        
        # 测试数据
        test_leads_data = [
            {
                'contact_name': '刁总',
                'company_name': '四川欧亚实业集团',
                'lead_source': 'rcc_platform',
                'province': '四川',
                'city': '成都市',
                'district': '成华区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,  # 使用创建人
                'is_friend_added': False,
                'days_not_followed': 350,
                'created_time_offset': -350,
            },
            {
                'contact_name': '潘尚',
                'company_name': '四川三酉控股有限责任公司',
                'lead_source': 'rcc_platform',
                'province': '四川',
                'city': '成都市',
                'district': '高新区',
                'follow_status': 'unhandled',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 364,
                'created_time_offset': -364,
            },
            {
                'contact_name': '张经理',
                'company_name': '成都天府新区建设投资有限公司',
                'lead_source': 'bidding_data',
                'province': '四川',
                'city': '成都市',
                'district': '天府新区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 120,
                'created_time_offset': -120,
            },
            {
                'contact_name': '李总',
                'company_name': '四川华西集团有限公司',
                'lead_source': 'old_customer',
                'province': '四川',
                'city': '成都市',
                'district': '锦江区',
                'follow_status': 'converted',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 0,
                'created_time_offset': -200,
            },
            {
                'contact_name': '王主任',
                'company_name': '四川省建筑设计研究院',
                'lead_source': 'contact_referral',
                'province': '四川',
                'city': '成都市',
                'district': '武侯区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 45,
                'created_time_offset': -45,
            },
            {
                'contact_name': '陈总',
                'company_name': '成都建工集团有限公司',
                'lead_source': 'rcc_platform',
                'province': '四川',
                'city': '成都市',
                'district': '青羊区',
                'follow_status': 'unhandled',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 280,
                'created_time_offset': -280,
            },
            {
                'contact_name': '刘经理',
                'company_name': '四川路桥建设集团股份有限公司',
                'lead_source': 'bidding_data',
                'province': '四川',
                'city': '成都市',
                'district': '金牛区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 30,
                'created_time_offset': -30,
            },
            {
                'contact_name': '赵总',
                'company_name': '成都轨道交通集团有限公司',
                'lead_source': 'online_contact',
                'province': '四川',
                'city': '成都市',
                'district': '成华区',
                'follow_status': 'contact_invalid',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 180,
                'created_time_offset': -180,
            },
            {
                'contact_name': '孙主任',
                'company_name': '四川省交通投资集团有限责任公司',
                'lead_source': 'external_partner',
                'province': '四川',
                'city': '成都市',
                'district': '高新区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 90,
                'created_time_offset': -90,
            },
            {
                'contact_name': '周总',
                'company_name': '成都兴城投资集团有限公司',
                'lead_source': 'rcc_platform',
                'province': '四川',
                'city': '成都市',
                'district': '锦江区',
                'follow_status': 'unhandled',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 250,
                'created_time_offset': -250,
            },
            {
                'contact_name': '吴经理',
                'company_name': '四川能投发展股份有限公司',
                'lead_source': 'new_employee_resource',
                'province': '四川',
                'city': '成都市',
                'district': '武侯区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 15,
                'created_time_offset': -15,
            },
            {
                'contact_name': '郑总',
                'company_name': '成都环境投资集团有限公司',
                'lead_source': 'old_customer',
                'province': '四川',
                'city': '成都市',
                'district': '青羊区',
                'follow_status': 'converted',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 0,
                'created_time_offset': -150,
            },
            {
                'contact_name': '钱主任',
                'company_name': '四川省水利水电勘测设计研究院',
                'lead_source': 'bidding_data',
                'province': '四川',
                'city': '成都市',
                'district': '金牛区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 60,
                'created_time_offset': -60,
            },
            {
                'contact_name': '冯总',
                'company_name': '成都交投建设集团有限公司',
                'lead_source': 'rcc_platform',
                'province': '四川',
                'city': '成都市',
                'district': '成华区',
                'follow_status': 'unhandled',
                'responsible_user_username': None,
                'is_friend_added': False,
                'days_not_followed': 320,
                'created_time_offset': -320,
            },
            {
                'contact_name': '韩经理',
                'company_name': '四川发展（控股）有限责任公司',
                'lead_source': 'contact_referral',
                'province': '四川',
                'city': '成都市',
                'district': '高新区',
                'follow_status': 'contact_valid',
                'responsible_user_username': None,
                'is_friend_added': True,
                'days_not_followed': 20,
                'created_time_offset': -20,
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        for lead_data in test_leads_data:
            try:
                # 检查是否已存在
                if CustomerLead.objects.filter(company_name=lead_data['company_name']).exists():
                    self.stdout.write(f'跳过已存在的线索：{lead_data["company_name"]}')
                    skipped_count += 1
                    continue
                
                # 获取负责人（使用创建人）
                responsible_user = creator
                
                # 计算创建时间
                created_time = timezone.now() + timedelta(days=lead_data['created_time_offset'])
                
                # 计算实际跟进时间（如果有跟进）
                actual_followup_time = None
                if lead_data['follow_status'] in ['contact_valid', 'converted']:
                    # 如果有跟进，实际跟进时间设置为创建后几天
                    followup_offset = lead_data['created_time_offset'] + min(lead_data['days_not_followed'], 30)
                    actual_followup_time = timezone.now() + timedelta(days=followup_offset)
                
                # 创建线索
                lead = CustomerLead.objects.create(
                    contact_name=lead_data['contact_name'],
                    company_name=lead_data['company_name'],
                    lead_source=lead_data['lead_source'],
                    province=lead_data['province'],
                    city=lead_data['city'],
                    district=lead_data['district'],
                    follow_status=lead_data['follow_status'],
                    responsible_user=responsible_user,
                    is_friend_added=lead_data['is_friend_added'],
                    days_not_followed=lead_data['days_not_followed'],
                    actual_followup_time=actual_followup_time,
                    created_by=creator,
                    created_time=created_time,
                )
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建线索：{lead.company_name} - {lead.contact_name}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ 创建线索失败：{lead_data["company_name"]} - {e}'))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n完成！创建了 {created_count} 条线索，跳过了 {skipped_count} 条线索'))

