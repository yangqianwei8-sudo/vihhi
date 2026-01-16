from backend.apps.system_management.models import User, Department, DataDictionary
from backend.apps.customer_management.models import Client
from django.contrib.auth import get_user_model
import os

def create_test_data():
    """创建测试数据"""
    
    # 创建部门
    dept_it, created = Department.objects.get_or_create(
        name='技术部',
        code='TECH',
        defaults={'description': '技术研发部门'}
    )
    
    dept_business, created = Department.objects.get_or_create(
        name='商务部',
        code='BUSINESS',
        defaults={'description': '商务和市场部门'}
    )
    
    # 创建测试用户（如果不是超级用户）
    User = get_user_model()
    if not User.objects.filter(username='test_user').exists():
        test_user = User.objects.create_user(
            username='test_user',
            email='test@weihai.com',
            password='test123456',
            first_name='测试',
            last_name='用户',
            department=dept_it,
            position='工程师'
        )
    
    # 创建数据字典
    dict_types = [
        ('project', '项目相关'),
        ('resource', '资源相关'),
        ('finance', '财务相关'),
        ('customer', '客户相关'),
    ]
    
    for dict_type, dict_name in dict_types:
        DataDictionary.objects.get_or_create(
            code=f'TYPE_{dict_type.upper()}',
            name=dict_name,
            dict_type='system',
            value=dict_type,
            defaults={'description': f'{dict_name}数据类型'}
        )
    
    # 创建示例客户
    if not Client.objects.filter(code='C001').exists():
        client = Client.objects.create(
            name='示例建筑公司',
            short_name='示例建筑',
            code='C001',
            client_level='vip',
            credit_level='excellent',
            industry='建筑设计',
            address='成都市高新区示例街道123号',
            phone='028-12345678',
            email='contact@example.com',
            description='示例客户用于测试',
            created_by=User.objects.first()
        )
    
    print("测试数据创建完成！")
