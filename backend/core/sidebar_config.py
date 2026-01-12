"""
侧边栏配置类
用于统一管理侧边栏的各种配置参数
"""


class SidebarConfig:
    """侧边栏配置类"""
    
    def __init__(self, 
                 menu_items=None,
                 theme='auto',
                 collapsible=True,
                 default_collapsed=False,
                 show_icons=True,
                 search_enabled=True,
                 animation_speed=300,
                 breakpoint='lg'):
        """
        初始化侧边栏配置
        
        Args:
            menu_items: 菜单项列表
            theme: 主题 ('light', 'dark', 'auto')
            collapsible: 是否可折叠
            default_collapsed: 默认是否折叠
            show_icons: 是否显示图标
            search_enabled: 是否启用搜索
            animation_speed: 动画速度（毫秒）
            breakpoint: 响应式断点 ('sm', 'md', 'lg', 'xl')
        """
        self.menu_items = menu_items or []
        self.theme = theme
        self.collapsible = collapsible
        self.default_collapsed = default_collapsed
        self.show_icons = show_icons
        self.search_enabled = search_enabled
        self.animation_speed = animation_speed
        self.breakpoint = breakpoint
    
    def to_dict(self):
        """转换为字典格式，用于传递给模板"""
        return {
            'menu_items': self.menu_items,
            'theme': self.theme,
            'collapsible': self.collapsible,
            'default_collapsed': self.default_collapsed,
            'show_icons': self.show_icons,
            'search_enabled': self.search_enabled,
            'animation_speed': self.animation_speed,
            'breakpoint': self.breakpoint,
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建配置对象"""
        return cls(
            menu_items=data.get('menu_items'),
            theme=data.get('theme', 'auto'),
            collapsible=data.get('collapsible', True),
            default_collapsed=data.get('default_collapsed', False),
            show_icons=data.get('show_icons', True),
            search_enabled=data.get('search_enabled', True),
            animation_speed=data.get('animation_speed', 300),
            breakpoint=data.get('breakpoint', 'lg'),
        )
    
    def get_default_config():
        """获取默认配置"""
        return SidebarConfig()

