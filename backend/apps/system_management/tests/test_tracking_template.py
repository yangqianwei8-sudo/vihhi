"""
目标跟踪模板自动化测试
验证 tracking_base.html 模板的所有功能是否完整实现
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django import forms
from datetime import timedelta

from backend.apps.system_management.models import User


class TrackingTemplateTests(TestCase):
    """目标跟踪模板功能测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.User = get_user_model()
        self.client = Client()
        
        # 创建管理员用户
        self.admin_user = self.User.objects.create_user(
            username='admin',
            password='test123456',
            is_superuser=True,
            is_staff=True,
            first_name='管理员',
            last_name='测试'
        )
        
        # 创建普通用户用于测试
        self.test_user = self.User.objects.create_user(
            username='testuser',
            password='test123456',
            first_name='测试',
            last_name='用户'
        )
    
    def test_tracking_example_page_access(self):
        """测试跟踪示例页面访问权限"""
        # 未登录用户应该被重定向
        response = self.client.get(reverse('system_pages:tracking_example'))
        self.assertEqual(response.status_code, 302)  # 重定向到登录页
        
        # 普通用户应该被拒绝
        self.client.login(username='testuser', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        self.assertEqual(response.status_code, 403)  # 权限拒绝
        
        # 管理员可以访问
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        self.assertEqual(response.status_code, 200)
    
    def test_tracking_example_context_variables(self):
        """测试上下文变量是否完整"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        
        # 检查必需变量
        required_vars = [
            'tracking_object',
            'progress_records',
            'can_update_progress',
            'valid_transitions',
            'can_complete',
            'all_users',
            'progress_form',
            'page_obj',
            'recorded_by_filter',
            'date_from',
            'date_to',
        ]
        
        for var in required_vars:
            self.assertIn(var, context, f"缺少必需的上下文变量: {var}")
        
        # 检查可选变量
        optional_vars = ['status_logs', 'adjustments']
        for var in optional_vars:
            self.assertIn(var, context, f"缺少可选的上下文变量: {var}")
    
    def test_tracking_object_attributes(self):
        """测试跟踪对象属性完整性"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        tracking_object = response.context['tracking_object']
        
        # 检查必需属性
        required_attrs = [
            'target_value',
            'current_value',
            'completion_rate',
            'status',
            'indicator_unit',
        ]
        
        for attr in required_attrs:
            self.assertTrue(
                hasattr(tracking_object, attr),
                f"tracking_object 缺少必需属性: {attr}"
            )
        
        # 检查方法
        self.assertTrue(
            hasattr(tracking_object, 'get_status_display'),
            "tracking_object 缺少 get_status_display 方法"
        )
        
        # 验证属性值类型
        self.assertIsInstance(tracking_object.target_value, (int, float))
        self.assertIsInstance(tracking_object.current_value, (int, float))
        self.assertIsInstance(tracking_object.completion_rate, (int, float))
        self.assertIsInstance(tracking_object.status, str)
    
    def test_progress_form_fields(self):
        """测试进度更新表单字段"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        progress_form = response.context['progress_form']
        
        # 检查表单字段
        required_fields = ['current_value', 'progress_description', 'notes']
        for field in required_fields:
            self.assertIn(field, progress_form.fields, f"表单缺少字段: {field}")
        
        # 检查字段类型
        self.assertIsInstance(
            progress_form.fields['current_value'],
            forms.DecimalField
        )
        self.assertIsInstance(
            progress_form.fields['progress_description'],
            forms.CharField
        )
        self.assertIsInstance(
            progress_form.fields['notes'],
            forms.CharField
        )
    
    def test_progress_records_structure(self):
        """测试进度记录数据结构"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        progress_records = response.context['progress_records']
        
        # 检查是否为列表
        self.assertIsInstance(progress_records, list)
        
        if progress_records:
            record = progress_records[0]
            # 检查记录属性
            required_attrs = [
                'recorded_time',
                'recorded_by',
                'current_value',
                'completion_rate',
                'progress_description',
            ]
            
            for attr in required_attrs:
                self.assertTrue(
                    hasattr(record, attr),
                    f"进度记录缺少属性: {attr}"
                )
    
    def test_status_logs_structure(self):
        """测试状态日志数据结构"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        status_logs = response.context.get('status_logs', [])
        
        if status_logs:
            log = status_logs[0]
            required_attrs = [
                'changed_time',
                'old_status',
                'new_status',
                'changed_by',
            ]
            
            for attr in required_attrs:
                self.assertTrue(
                    hasattr(log, attr),
                    f"状态日志缺少属性: {attr}"
                )
    
    def test_adjustments_structure(self):
        """测试调整申请数据结构"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        adjustments = response.context.get('adjustments', [])
        
        if adjustments:
            adjustment = adjustments[0]
            required_attrs = [
                'created_time',
                'status',
                'adjustment_reason',
            ]
            
            for attr in required_attrs:
                self.assertTrue(
                    hasattr(adjustment, attr),
                    f"调整申请缺少属性: {attr}"
                )
            
            # 检查方法
            self.assertTrue(
                hasattr(adjustment, 'get_status_display'),
                "调整申请缺少 get_status_display 方法"
            )
    
    def test_template_rendering(self):
        """测试模板渲染"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # 检查关键 HTML 元素
        key_elements = [
            'track-stats-grid',  # 统计卡片网格
            'track-form-card',   # 进度表单卡片
            'track-action-grid', # 操作卡片网格
            'list-table',        # 列表表格
            'track-extra-section', # 额外部分
        ]
        
        for element in key_elements:
            self.assertIn(
                element,
                content,
                f"模板缺少关键元素: {element}"
            )
    
    def test_progress_update_form_submission(self):
        """测试进度更新表单提交"""
        self.client.login(username='admin', password='test123456')
        
        # 提交进度更新表单
        response = self.client.post(
            reverse('system_pages:tracking_example'),
            {
                'update_progress': '1',
                'current_value': '700',
                'progress_description': '测试进度更新',
                'notes': '测试备注',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        # 检查是否有成功消息
        messages = list(response.context.get('messages', []))
        self.assertTrue(
            any('成功' in str(m) for m in messages),
            "进度更新应该显示成功消息"
        )
    
    def test_status_transition_form_submission(self):
        """测试状态转换表单提交"""
        self.client.login(username='admin', password='test123456')
        
        # 提交状态转换表单
        response = self.client.post(
            reverse('system_pages:tracking_example'),
            {
                'transition_status': '1',
                'new_status': 'completed',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        # 检查是否有成功消息
        messages = list(response.context.get('messages', []))
        self.assertTrue(
            any('转换' in str(m) or '状态' in str(m) for m in messages),
            "状态转换应该显示成功消息"
        )
    
    def test_complete_goal_form_submission(self):
        """测试完成确认表单提交"""
        self.client.login(username='admin', password='test123456')
        
        # 提交完成确认表单
        response = self.client.post(
            reverse('system_pages:tracking_example'),
            {
                'complete_goal': '1',
            }
        )
        
        self.assertEqual(response.status_code, 200)
        # 检查是否有成功消息
        messages = list(response.context.get('messages', []))
        self.assertTrue(
            any('完成' in str(m) for m in messages),
            "完成确认应该显示成功消息"
        )
    
    def test_filtering_functionality(self):
        """测试筛选功能"""
        self.client.login(username='admin', password='test123456')
        
        # 测试按记录人筛选
        response = self.client.get(
            reverse('system_pages:tracking_example'),
            {'recorded_by': str(self.admin_user.id)}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['recorded_by_filter'],
            str(self.admin_user.id)
        )
        
        # 测试按日期范围筛选
        date_from = (timezone.now() - timedelta(days=15)).date().isoformat()
        date_to = timezone.now().date().isoformat()
        
        response = self.client.get(
            reverse('system_pages:tracking_example'),
            {
                'date_from': date_from,
                'date_to': date_to,
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['date_from'], date_from)
        self.assertEqual(response.context['date_to'], date_to)
    
    def test_pagination(self):
        """测试分页功能"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        page_obj = response.context['page_obj']
        
        # 检查分页对象
        self.assertIsNotNone(page_obj)
        self.assertTrue(hasattr(page_obj, 'has_other_pages'))
        self.assertTrue(hasattr(page_obj, 'number'))
        self.assertTrue(hasattr(page_obj, 'paginator'))
    
    def test_template_blocks(self):
        """测试模板 block 是否正确继承"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        content = response.content.decode('utf-8')
        
        # 检查关键 block 内容
        # tracking_title 应该在 title 中
        self.assertIn('目标跟踪示例', content)
        
        # 检查统计卡片
        self.assertIn('目标值', content)
        self.assertIn('当前值', content)
        self.assertIn('完成率', content)
        self.assertIn('进度记录', content)
        
        # 检查表单
        self.assertIn('更新进度', content)
        self.assertIn('id_current_value', content)
        self.assertIn('id_progress_description', content)
        
        # 检查操作按钮
        self.assertIn('状态转换', content)
        self.assertIn('完成确认', content)
    
    def test_javascript_functionality(self):
        """测试 JavaScript 功能"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        content = response.content.decode('utf-8')
        
        # 检查 JavaScript 代码
        self.assertIn('predictedRate', content)
        self.assertIn('addEventListener', content)
        self.assertIn('DOMContentLoaded', content)
        
        # 检查完成率计算逻辑
        self.assertIn('targetValue', content)
        self.assertIn('currentValue', content)
    
    def test_all_users_list(self):
        """测试用户列表"""
        self.client.login(username='admin', password='test123456')
        response = self.client.get(reverse('system_pages:tracking_example'))
        
        all_users = response.context['all_users']
        
        # 检查用户列表
        self.assertIsNotNone(all_users)
        self.assertGreater(len(all_users), 0)
        
        # 检查用户对象
        if all_users:
            user = all_users[0]
            self.assertTrue(hasattr(user, 'id'))
            self.assertTrue(hasattr(user, 'username'))
            self.assertTrue(
                hasattr(user, 'get_full_name') or hasattr(user, 'first_name'),
                "用户对象应该有姓名相关属性"
            )
