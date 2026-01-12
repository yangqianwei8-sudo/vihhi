"""
侧边栏模板和工具函数测试
"""

from django.test import TestCase, RequestFactory
from django.template import Context, Template
from django.contrib.auth.models import User
from backend.core.sidebar_utils import prepare_menu_item, prepare_menu_items, get_menu_search_keywords
from backend.core.sidebar_config import SidebarConfig


class SidebarUtilsTest(TestCase):
    """侧边栏工具函数测试"""

    def test_prepare_menu_item_basic(self):
        """测试基本菜单项预处理"""
        menu_item = {
            'id': 'test_menu',
            'label': '测试菜单',
            'icon': '🏠',
            'url': '/test/',
        }
        
        result = prepare_menu_item(menu_item)
        
        self.assertEqual(result['id'], 'test_menu')
        self.assertEqual(result['label'], '测试菜单')
        self.assertEqual(result['icon'], '🏠')
        self.assertEqual(result['url'], '/test/')
        self.assertFalse(result['active'])
        self.assertFalse(result['expanded'])
        self.assertFalse(result['has_children'])

    def test_prepare_menu_item_with_children(self):
        """测试带子菜单的菜单项预处理"""
        menu_item = {
            'id': 'parent_menu',
            'label': '父菜单',
            'children': [
                {'id': 'child1', 'label': '子菜单1', 'url': '/child1/'},
                {'id': 'child2', 'label': '子菜单2', 'url': '/child2/'},
            ]
        }
        
        result = prepare_menu_item(menu_item)
        
        self.assertTrue(result['has_children'])
        self.assertEqual(len(result['children']), 2)
        self.assertEqual(result['children'][0]['label'], '子菜单1')

    def test_prepare_menu_item_active(self):
        """测试激活状态计算"""
        menu_item = {
            'id': 'active_menu',
            'label': '激活菜单',
            'url': '/active/',
        }
        
        result = prepare_menu_item(menu_item, active_id='active_menu')
        
        self.assertTrue(result['active'])

    def test_prepare_menu_item_expanded(self):
        """测试展开状态计算"""
        menu_item = {
            'id': 'parent_menu',
            'label': '父菜单',
            'children': [
                {'id': 'child1', 'label': '子菜单1', 'url': '/child1/'},
            ]
        }
        
        # 当子菜单激活时，父菜单应该展开
        result = prepare_menu_item(menu_item, active_id='child1')
        
        self.assertTrue(result['expanded'])

    def test_prepare_menu_items(self):
        """测试菜单项列表预处理"""
        menu_items = [
            {'id': 'menu1', 'label': '菜单1', 'url': '/menu1/'},
            {'id': 'menu2', 'label': '菜单2', 'url': '/menu2/'},
        ]
        
        result = prepare_menu_items(menu_items)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'menu1')
        self.assertEqual(result[1]['id'], 'menu2')

    def test_get_menu_search_keywords(self):
        """测试搜索关键词生成"""
        menu_item = {
            'label': '主菜单',
            'children': [
                {'label': '子菜单1'},
                {'label': '子菜单2'},
            ]
        }
        
        keywords = get_menu_search_keywords(menu_item)
        
        self.assertIn('主菜单', keywords)
        self.assertIn('子菜单1', keywords)
        self.assertIn('子菜单2', keywords)


class SidebarConfigTest(TestCase):
    """侧边栏配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SidebarConfig()
        
        self.assertEqual(config.theme, 'auto')
        self.assertTrue(config.collapsible)
        self.assertFalse(config.default_collapsed)
        self.assertTrue(config.show_icons)
        self.assertTrue(config.search_enabled)

    def test_custom_config(self):
        """测试自定义配置"""
        config = SidebarConfig(
            theme='dark',
            collapsible=False,
            search_enabled=False
        )
        
        self.assertEqual(config.theme, 'dark')
        self.assertFalse(config.collapsible)
        self.assertFalse(config.search_enabled)

    def test_to_dict(self):
        """测试转换为字典"""
        config = SidebarConfig(theme='light')
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['theme'], 'light')
        self.assertIn('menu_items', config_dict)
        self.assertIn('collapsible', config_dict)

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'theme': 'dark',
            'collapsible': False,
            'menu_items': [{'id': 'test', 'label': '测试'}]
        }
        
        config = SidebarConfig.from_dict(data)
        
        self.assertEqual(config.theme, 'dark')
        self.assertFalse(config.collapsible)
        self.assertEqual(len(config.menu_items), 1)


class SidebarTemplateTest(TestCase):
    """侧边栏模板测试"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_sidebar_template_renders(self):
        """测试侧边栏模板渲染"""
        template = Template("""
            {% load cache %}
            {% include 'shared/sidebar/base.html' with menu_items=menu_items %}
        """)
        
        menu_items = [
            {
                'id': 'test_menu',
                'label': '测试菜单',
                'icon': '🏠',
                'url': '/test/',
                'active': False,
                'expanded': False,
            }
        ]
        
        context = Context({
            'menu_items': menu_items,
            'request': self.factory.get('/'),
        })
        context['request'].user = self.user
        
        result = template.render(context)
        
        self.assertIn('测试菜单', result)
        self.assertIn('workspace-nav', result)

    def test_menu_item_template(self):
        """测试菜单项子模板"""
        template = Template("""
            {% include 'shared/sidebar/menu_item.html' with menu_item=menu_item forloop_counter=1 %}
        """)
        
        menu_item = {
            'id': 'test',
            'label': '测试',
            'url': '/test/',
            'active': True,
        }
        
        context = Context({'menu_item': menu_item})
        result = template.render(context)
        
        self.assertIn('测试', result)
        self.assertIn('sidenav-item', result)
        self.assertIn('active', result)

