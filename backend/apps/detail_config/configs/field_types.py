"""
字段类型定义
提供详情页配置的数据结构定义
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldConfig:
    """字段配置"""
    id: str  # 字段ID，支持嵌套路径（如 'user.profile.name'）
    label: str  # 字段标签
    type: str = "text"  # 字段类型：text, date, datetime, status, link, tag, phone, email, address, currency, percent
    span: int = 12  # 栅格跨度（12列系统）
    format: Optional[str] = None  # 格式化方式：currency, date, datetime, percent
    options: Optional[Dict] = None  # 选项（用于select等）
    renderer: Optional[str] = None  # 自定义渲染器名称
    permission: Optional[str] = None  # 权限要求
    default: Optional[str] = None  # 默认值
    conditions: Optional[Dict] = None  # 显示条件


@dataclass
class SectionConfig:
    """区块配置"""
    id: str  # 区块ID
    title: str  # 区块标题
    layout: str = "grid"  # 布局方式：grid, list
    fields: List[FieldConfig] = field(default_factory=list)  # 字段列表
    columns: int = 2  # 栅格列数（grid布局时使用）
    collapsible: bool = False  # 是否可折叠
    default_collapsed: bool = False  # 默认是否折叠
    permission: Optional[str] = None  # 权限要求
    conditions: Optional[Dict] = None  # 显示条件
    component: Optional[str] = None  # 自定义组件模板路径
    component_context: Optional[Dict] = None  # 传递给组件的上下文
    render_mode: str = "config"  # 渲染模式：config（配置驱动）, custom（自定义组件）


@dataclass
class TabConfig:
    """标签页配置"""
    id: str  # 标签页ID
    title: str  # 标签页标题
    section_ids: List[str] = field(default_factory=list)  # 包含的区块ID列表
    component: Optional[str] = None  # 自定义组件模板路径
    permission: Optional[str] = None  # 权限要求
    conditions: Optional[Dict] = None  # 显示条件


@dataclass
class ActionConfig:
    """操作配置"""
    id: str  # 操作ID
    label: str  # 操作标签
    type: str = "primary"  # 按钮类型：primary, secondary, danger, success, warning, info
    icon: Optional[str] = None  # 图标名称（Bootstrap Icons）
    url_name: Optional[str] = None  # URL名称（用于reverse）
    url_args: Optional[List] = None  # URL参数列表
    url_kwargs: Optional[Dict] = None  # URL关键字参数
    handler: Optional[str] = None  # JavaScript函数名
    ajax_url: Optional[str] = None  # AJAX操作URL
    permission: Optional[str] = None  # 权限要求
    confirm: Optional[str] = None  # 确认消息
    conditions: Optional[Dict] = None  # 显示条件


@dataclass
class DetailPageConfig:
    """详情页配置"""
    title: str  # 页面标题
    layout: str = "standard"  # 布局模式：standard（标准）, tabbed（标签页）
    sections: List[SectionConfig] = field(default_factory=list)  # 区块列表
    tabs: List[TabConfig] = field(default_factory=list)  # 标签页列表（tabbed模式）
    actions: List[ActionConfig] = field(default_factory=list)  # 操作按钮列表
    timeline_enabled: bool = True  # 是否启用时间线
    timeline_config: Optional[Dict] = None  # 时间线配置

