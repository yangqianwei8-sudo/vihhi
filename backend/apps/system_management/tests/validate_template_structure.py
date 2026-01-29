#!/usr/bin/env python
"""
独立的模板结构验证脚本
不依赖数据库，可以直接运行
"""
import os
import re
import sys

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
sys.path.insert(0, project_root)

import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.conf import settings


def validate_template_structure():
    """验证模板结构"""
    template_path = os.path.join(
        settings.BASE_DIR,
        'templates',
        'shared',
        'tracking_base.html'
    )
    
    if not os.path.exists(template_path):
        print(f"❌ 模板文件不存在: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    errors = []
    warnings = []
    
    # 检查必需的 block
    required_blocks = [
        'tracking_title',
        'tracking_page_title',
        'tracking_stats_section',
        'tracking_stats_content',
        'tracking_progress_form_section',
        'tracking_progress_form_fields',
        'tracking_actions_section',
        'tracking_filters_section',
        'tracking_records_section',
        'tracking_pagination_section',
        'tracking_status_logs_section',
        'tracking_adjustments_section',
        'tracking_target_value_js',
    ]
    
    for block in required_blocks:
        pattern = rf'{{\%\s*block\s+{block}'
        if not re.search(pattern, template_content):
            errors.append(f"缺少必需的 block: {block}")
    
    # 检查必需的 CSS 类
    required_css_classes = [
        'track-stats-grid',
        'track-stat-card',
        'track-form-card',
        'track-form-header',
        'track-form-body',
        'track-action-grid',
        'track-action-card',
        'track-extra-section',
    ]
    
    for css_class in required_css_classes:
        pattern = rf'\.{css_class}\s*\{{'
        if not re.search(pattern, template_content):
            warnings.append(f"缺少 CSS 类定义: {css_class}")
    
    # 检查模板继承
    if 'extends "shared/module_base.html"' not in template_content:
        errors.append("模板未正确继承 module_base.html")
    
    # 检查关键功能
    if 'update_progress' not in template_content:
        errors.append("缺少进度更新表单处理")
    if 'transition_status' not in template_content:
        errors.append("缺少状态转换表单处理")
    if 'complete_goal' not in template_content:
        errors.append("缺少完成确认表单处理")
    
    # 检查 JavaScript
    if 'predictedRate' not in template_content:
        warnings.append("缺少完成率自动计算 JavaScript")
    
    # 输出结果
    if errors:
        print("❌ 发现错误：")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print("⚠️  发现警告：")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("✅ 模板结构验证通过！")
    return True


if __name__ == '__main__':
    success = validate_template_structure()
    sys.exit(0 if success else 1)
