"""
目标跟踪模板验证脚本
通过解析模板文件来验证所有必需的功能块和变量
"""
import os
import re
from django.test import TestCase
from django.conf import settings


class TrackingTemplateValidationTests(TestCase):
    """模板结构验证测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.template_path = os.path.join(
            settings.BASE_DIR,
            'templates',
            'shared',
            'tracking_base.html'
        )
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
    
    def test_required_blocks_exist(self):
        """测试所有必需的 block 是否存在"""
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
            self.assertTrue(
                re.search(pattern, self.template_content),
                f"模板缺少必需的 block: {block}"
            )
    
    def test_required_css_classes(self):
        """测试所有必需的 CSS 类是否定义"""
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
            self.assertTrue(
                re.search(pattern, self.template_content),
                f"模板缺少必需的 CSS 类: {css_class}"
            )
    
    def test_required_template_variables(self):
        """测试模板中使用的所有变量"""
        # 查找所有模板变量
        variable_pattern = r'\{\{\s*(\w+)(?:\.[\w|]+)*\s*\}\}'
        variables = re.findall(variable_pattern, self.template_content)
        
        # 必需的上下文变量
        required_variables = [
            'tracking_object',
            'progress_records',
            'can_update_progress',
            'valid_transitions',
            'can_complete',
            'all_users',
            'progress_form',
            'page_obj',
        ]
        
        # 检查变量是否在模板中使用
        variables_set = set(variables)
        for var in required_variables:
            # 检查变量或其属性是否被使用
            var_pattern = rf'{var}(?:\.[\w|]+)*'
            found = any(re.search(var_pattern, v) for v in variables)
            self.assertTrue(
                found,
                f"模板中未使用必需的变量: {var}"
            )
    
    def test_form_handling(self):
        """测试表单处理逻辑"""
        # 检查进度更新表单
        self.assertIn('update_progress', self.template_content)
        self.assertIn('id="tracking-progress-form"', self.template_content)
        
        # 检查状态转换表单
        self.assertIn('transition_status', self.template_content)
        self.assertIn('new_status', self.template_content)
        
        # 检查完成确认表单
        self.assertIn('complete_goal', self.template_content)
    
    def test_javascript_functionality(self):
        """测试 JavaScript 功能代码"""
        # 检查完成率计算
        self.assertIn('predictedRate', self.template_content)
        self.assertIn('targetValue', self.template_content)
        self.assertIn('currentValue', self.template_content)
        
        # 检查事件监听
        self.assertIn('addEventListener', self.template_content)
        self.assertIn('DOMContentLoaded', self.template_content)
    
    def test_template_inheritance(self):
        """测试模板继承（两栏基模板）"""
        self.assertIn('extends "shared/two_column_layout_base.html"', self.template_content)
        self.assertIn('{% block pm_content %}', self.template_content)
    
    def test_empty_state_handling(self):
        """测试空状态处理"""
        # 检查空状态显示
        self.assertIn('list-empty-state', self.template_content)
        self.assertIn('empty', self.template_content.lower())
    
    def test_conditional_rendering(self):
        """测试条件渲染"""
        # 检查条件判断
        self.assertIn('{% if can_update_progress %}', self.template_content)
        self.assertIn('{% if valid_transitions', self.template_content)
        self.assertIn('{% if can_complete %}', self.template_content)
        self.assertIn('{% if status_logs %}', self.template_content)
        self.assertIn('{% if adjustments %}', self.template_content)
    
    def test_pagination_inclusion(self):
        """测试分页组件包含"""
        self.assertIn('_pagination.html', self.template_content)
        self.assertIn('has_other_pages', self.template_content)
    
    def test_static_files(self):
        """测试静态文件引用（list-layout.css 已由 common.css 统一引入，此处仅校验 static 用法）"""
        self.assertIn('{% static', self.template_content)
