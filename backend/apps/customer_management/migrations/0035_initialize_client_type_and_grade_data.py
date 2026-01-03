# Generated migration for initializing ClientType and ClientGrade data

from django.db import migrations


def initialize_client_types_and_grades(apps, schema_editor):
    """初始化客户类型和客户分级数据"""
    ClientType = apps.get_model('customer_management', 'ClientType')
    ClientGrade = apps.get_model('customer_management', 'ClientGrade')
    
    # 初始化客户类型
    client_types = [
        {'code': 'developer', 'name': '开发商', 'display_order': 1},
        {'code': 'government', 'name': '政府单位', 'display_order': 2},
        {'code': 'design_institute', 'name': '设计院', 'display_order': 3},
        {'code': 'general_contractor', 'name': '总包单位', 'display_order': 4},
        {'code': 'school', 'name': '各类学校', 'display_order': 5},
        {'code': 'government_platform', 'name': '政府平台公司', 'display_order': 6},
        {'code': 'institution', 'name': '事业单位', 'display_order': 7},
        {'code': 'other', 'name': '其他', 'display_order': 99},
    ]
    
    for ct_data in client_types:
        ClientType.objects.get_or_create(
            code=ct_data['code'],
            defaults={
                'name': ct_data['name'],
                'display_order': ct_data['display_order'],
                'is_active': True,
            }
        )
    
    # 初始化客户分级
    client_grades = [
        {'code': 'strategic', 'name': '战略客户', 'display_order': 1},
        {'code': 'core', 'name': '核心客户', 'display_order': 2},
        {'code': 'potential', 'name': '潜力客户', 'display_order': 3},
        {'code': 'regular', 'name': '常规客户', 'display_order': 4},
        {'code': 'nurturing', 'name': '培育客户', 'display_order': 5},
        {'code': 'observing', 'name': '观察客户', 'display_order': 6},
    ]
    
    for cg_data in client_grades:
        ClientGrade.objects.get_or_create(
            code=cg_data['code'],
            defaults={
                'name': cg_data['name'],
                'display_order': cg_data['display_order'],
                'is_active': True,
            }
        )


def reverse_initialize_client_types_and_grades(apps, schema_editor):
    """回滚：删除初始化的数据"""
    ClientType = apps.get_model('customer_management', 'ClientType')
    ClientGrade = apps.get_model('customer_management', 'ClientGrade')
    
    ClientType.objects.all().delete()
    ClientGrade.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0034_add_client_type_and_grade_models'),
    ]

    operations = [
        migrations.RunPython(
            initialize_client_types_and_grades,
            reverse_initialize_client_types_and_grades
        ),
    ]

