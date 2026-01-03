#!/usr/bin/env python
"""
为已存在的赢单商机创建对应的项目
项目编号 = 商机编号（opportunity_number）

使用方法：
    python create_projects_for_won_opportunities.py
"""

import os
import sys
import django

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import transaction
from backend.apps.customer_management.models import BusinessOpportunity
from backend.apps.production_management.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()


def create_projects_for_won_opportunities():
    """
    为所有已存在的赢单商机创建对应的项目
    项目编号 = 商机编号（opportunity_number）
    """
    # 获取所有状态为赢单的商机
    won_opportunities = BusinessOpportunity.objects.filter(
        status='won',
        opportunity_number__isnull=False
    ).exclude(opportunity_number='')
    
    print(f"找到 {won_opportunities.count()} 个赢单商机")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    # 获取系统用户（用于创建人字段，如果商机没有创建人）
    system_user = None
    try:
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            system_user = User.objects.first()
    except Exception:
        pass
    
    for opportunity in won_opportunities:
        try:
            project_number = opportunity.opportunity_number
            
            # 检查项目是否已存在
            existing_project = Project.objects.filter(project_number=project_number).first()
            if existing_project:
                skipped_count += 1
                print(f'⏭️  项目已存在，跳过：项目编号={project_number}')
                continue
            
            # 准备项目数据
            project_data = {
                'project_number': project_number,
                'name': opportunity.project_name or opportunity.name or '未命名项目',
                'client': opportunity.client,
                'service_type': opportunity.service_type,
                'status': 'draft',  # 初始状态为草稿
            }
            
            # 设置创建人
            if opportunity.created_by:
                project_data['created_by'] = opportunity.created_by
            elif system_user:
                project_data['created_by'] = system_user
            
            # 如果商机有项目地址，设置到项目描述中
            if opportunity.project_address:
                project_data['description'] = f'项目地址：{opportunity.project_address}'
            
            # 创建项目
            with transaction.atomic():
                new_project = Project.objects.create(**project_data)
                created_count += 1
                print(f'✅ 创建项目：项目编号={project_number}, 项目名称={project_data["name"]}')
                
        except Exception as e:
            error_count += 1
            print(f'❌ 创建项目失败：商机ID={opportunity.id}, 商机编号={opportunity.opportunity_number}, 错误={str(e)}')
            import traceback
            traceback.print_exc()
    
    print(f'\n迁移完成：')
    print(f'  ✅ 创建：{created_count} 个项目')
    print(f'  ⏭️  跳过：{skipped_count} 个项目（已存在）')
    print(f'  ❌ 错误：{error_count} 个项目')
    
    return created_count, skipped_count, error_count


if __name__ == '__main__':
    print("=" * 60)
    print("为已存在的赢单商机创建对应的项目")
    print("=" * 60)
    print()
    
    try:
        create_projects_for_won_opportunities()
        print("\n✅ 脚本执行完成！")
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

