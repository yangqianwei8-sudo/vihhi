#!/usr/bin/env python
"""
验证沟通清单问题功能是否正常
运行方式：python manage.py shell < verify_checklist_questions.py
或者：python manage.py shell，然后复制粘贴以下代码
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.customer_management.models import (
    CommunicationChecklistQuestion,
    CommunicationChecklistAnswer,
    CustomerCommunicationChecklist
)

def verify_questions():
    """验证问题数据"""
    print("=" * 60)
    print("验证沟通清单问题功能")
    print("=" * 60)
    
    # 1. 检查问题数量
    total_questions = CommunicationChecklistQuestion.objects.count()
    active_questions = CommunicationChecklistQuestion.objects.filter(is_active=True).count()
    
    print(f"\n1. 问题统计：")
    print(f"   - 总问题数：{total_questions}")
    print(f"   - 启用问题数：{active_questions}")
    
    # 2. 按部分统计
    print(f"\n2. 按部分统计：")
    for part_code, part_name in CommunicationChecklistQuestion.PART_CHOICES:
        count = CommunicationChecklistQuestion.objects.filter(part=part_code, is_active=True).count()
        print(f"   - {part_name}：{count} 个问题")
    
    # 3. 检查问题顺序
    print(f"\n3. 检查问题顺序：")
    for part_code, part_name in CommunicationChecklistQuestion.PART_CHOICES:
        questions = CommunicationChecklistQuestion.objects.filter(
            part=part_code, 
            is_active=True
        ).order_by('order')
        
        if questions.exists():
            print(f"\n   {part_name}：")
            for q in questions:
                print(f"     序号 {q.order}: {q.question_text[:50]}...")
    
    # 4. 检查答案数据
    total_answers = CommunicationChecklistAnswer.objects.count()
    total_checklists = CustomerCommunicationChecklist.objects.count()
    
    print(f"\n4. 清单和答案统计：")
    print(f"   - 总清单数：{total_checklists}")
    print(f"   - 总答案数：{total_answers}")
    
    # 5. 检查是否有清单使用新系统
    if total_checklists > 0:
        checklists_with_answers = CustomerCommunicationChecklist.objects.filter(
            answers__isnull=False
        ).distinct().count()
        print(f"   - 使用新系统的清单数：{checklists_with_answers}")
    
    # 6. 验证数据完整性
    print(f"\n5. 数据完整性检查：")
    
    # 检查是否有重复的问题代码
    from django.db.models import Count
    duplicate_codes = CommunicationChecklistQuestion.objects.values('question_code').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicate_codes.exists():
        print(f"   ⚠️  发现重复的问题代码：")
        for dup in duplicate_codes:
            print(f"      - {dup['question_code']}")
    else:
        print(f"   ✅ 问题代码唯一性检查通过")
    
    # 检查是否有问题缺少必填字段
    from django.db.models import Q
    incomplete_questions = CommunicationChecklistQuestion.objects.filter(
        Q(question_text__isnull=True) | 
        Q(question_text='') |
        Q(question_code__isnull=True) |
        Q(question_code='')
    )
    
    if incomplete_questions.exists():
        print(f"   ⚠️  发现不完整的问题：{incomplete_questions.count()} 个")
    else:
        print(f"   ✅ 问题数据完整性检查通过")
    
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)

if __name__ == '__main__':
    verify_questions()

