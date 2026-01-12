# 详情页配置驱动系统

## 概述

详情页配置驱动系统提供了一个统一的、可配置的方式来构建详情页面。通过配置驱动，可以快速创建和维护详情页面，减少重复代码，提高开发效率。

## 功能特性

- **配置驱动**：通过Python配置类定义页面结构，无需编写大量模板代码
- **组件化**：可复用的字段组件和区块组件
- **响应式设计**：自动适配不同屏幕尺寸
- **向后兼容**：与现有模板系统完全兼容，支持逐步迁移
- **灵活扩展**：支持自定义组件和混合模式

## 快速开始

### 1. 创建配置

在 `apps/detail_config/configs/template_configs.py` 中创建配置：

```python
from apps.detail_config.configs.field_types import (
    FieldConfig, SectionConfig, DetailPageConfig, ActionConfig
)

MY_DETAIL_CONFIG = DetailPageConfig(
    title="我的详情页",
    layout="standard",
    sections=[
        SectionConfig(
            id="basic-info",
            title="基本信息",
            layout="grid",
            columns=2,
            fields=[
                FieldConfig(id="name", label="名称", type="text", span=12),
                FieldConfig(id="code", label="编码", type="text", span=6),
                FieldConfig(id="status", label="状态", type="status", span=6),
            ]
        ),
    ],
    actions=[
        ActionConfig(
            id="edit",
            label="编辑",
            type="primary",
            icon="pencil",
            url_name="myapp:edit",
        ),
    ],
)
```

### 2. 在视图中使用配置

```python
from apps.detail_config.configs.template_configs import MY_DETAIL_CONFIG

def my_detail(request, pk):
    obj = get_object_or_404(MyModel, pk=pk)
    context = {
        'object': obj,
        'config': MY_DETAIL_CONFIG,
        'data': obj,  # 传递给模板的数据对象
    }
    return render(request, 'myapp/my_detail.html', context)
```

### 3. 在模板中使用配置

```django
{% extends "shared/detail_page_base.html" %}
{% load detail_tags %}
{% load static %}

{% block detail_page_extra_css %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'css/details/detail.css' %}">
{% endblock %}

{% block detail_hero_title %}{{ config.title }}{% endblock %}
{% block detail_hero_subtitle %}编号：{{ object.code }}{% endblock %}

{% block detail_content %}
    {% include 'shared/details/layouts/_detail_layout.html' with config=config data=object %}
{% endblock %}
```

## 字段类型

支持的字段类型：

- `text` - 文本字段
- `date` - 日期字段
- `datetime` - 日期时间字段
- `status` - 状态字段（显示为徽章）
- `link` - 链接字段
- `phone` - 电话字段
- `email` - 邮箱字段
- `tag` - 标签字段
- `currency` - 货币字段
- `percent` - 百分比字段

## 布局模式

- `standard` - 标准布局（所有区块垂直排列）
- `tabbed` - 标签页布局（区块分组到标签页中）

## 配置选项

### FieldConfig

- `id` - 字段ID（支持嵌套路径，如 `user.profile.name`）
- `label` - 字段标签
- `type` - 字段类型
- `span` - 栅格跨度（1-12）
- `format` - 格式化方式（currency, date, datetime, percent）
- `permission` - 权限要求

### SectionConfig

- `id` - 区块ID
- `title` - 区块标题
- `layout` - 布局方式（grid, list）
- `fields` - 字段列表
- `columns` - 栅格列数（grid布局时）
- `component` - 自定义组件模板路径
- `render_mode` - 渲染模式（config, custom）

### ActionConfig

- `id` - 操作ID
- `label` - 操作标签
- `type` - 按钮类型（primary, secondary, danger等）
- `icon` - 图标名称
- `url_name` - URL名称
- `handler` - JavaScript函数名
- `ajax_url` - AJAX操作URL
- `confirm` - 确认消息

## 示例

查看 `apps/detail_config/configs/template_configs.py` 中的 `INCOMING_DOCUMENT_DETAIL_CONFIG` 配置示例。

## 迁移指南

1. 保持现有模板不变
2. 创建配置对象
3. 创建新版本模板（可选，用于测试）
4. 逐步迁移到配置驱动

## 最佳实践

1. **字段ID命名**：使用模型字段名，支持嵌套路径
2. **配置组织**：按模块组织配置，便于维护
3. **组件复用**：优先使用现有组件，必要时创建自定义组件
4. **权限控制**：在视图层处理权限，配置中声明权限要求
5. **条件显示**：使用 `conditions` 字段控制区块显示

## 扩展

### 自定义字段类型

1. 创建字段模板：`templates/shared/details/components/fields/_my_field.html`
2. 在 `field_renderers.py` 中添加模板映射
3. 在配置中使用新类型

### 自定义组件

使用 `render_mode='custom'` 和 `component` 字段指定自定义组件模板。

## 技术支持

如有问题，请查看代码注释或联系开发团队。

