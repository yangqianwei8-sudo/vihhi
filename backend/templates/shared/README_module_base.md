# 模块基础模板使用指南

## 概述

`module_base.html` 是一个**共享的模块级基础模板**，为所有功能模块提供统一的页面结构和样式。各模块的 `_base.html` 应该继承此模板，而不是直接继承 `two_column_layout_base.html`。

## 模板继承链

```
shared/two_column_layout_base.html (最底层 - 布局基础)
    ↓
shared/module_base.html (中间层 - 模块级共享模板)
    ↓
{module_name}/_base.html (模块专用 - 可覆盖特定配置)
    ↓
{module_name}/home.html (具体页面)
```

## 优势

1. **统一结构**：所有模块使用相同的页面标题区域结构
2. **统一 Block 命名**：`pm_title`, `pm_subtitle`, `pm_actions`, `pm_content`
3. **减少重复**：通用样式和脚本在共享模板中定义
4. **灵活扩展**：各模块可覆盖特定配置
5. **易于维护**：修改共享模板即可影响所有模块

## 可覆盖的 Block

### 基础信息 Block

- `module_title` - 模块标题（用于页面 `<title>` 标签）
- `module_sidebar_width` - 侧边栏宽度（默认：232px）

### 侧边栏 Block

- `module_sidebar` - 模块侧边栏内容（默认：通用侧边栏）

### 样式 Block

- `module_base_styles` - 模块基础样式文件（可覆盖）
- `module_styles` - 模块特定样式文件（各模块添加）
- `module_page_header_styles` - 页面标题区域样式（可覆盖）
- `module_content_wrapper_styles` - 内容包装器样式（可覆盖）
- `module_extra_css` - 模块额外样式

### 脚本 Block

- `module_base_scripts` - 模块基础脚本（可覆盖）
- `module_scripts` - 模块特定脚本（各模块添加）
- `module_extra_js` - 模块额外脚本

### 内容结构 Block

- `module_content_wrapper_class` - 内容包装器类名（默认：`module-content-wrapper`）
- `pm_title` / `module_title` - 页面主标题
- `pm_subtitle` / `module_subtitle` - 页面副标题
- `pm_actions` / `module_actions` - 页面操作按钮区域
- `pm_content` / `module_content` - 页面主要内容

## 使用示例

### 客户管理模块 `_base.html`

```django
{% extends "shared/module_base.html" %}
{% load static %}

{# 模块标题 #}
{% block module_title %}客户管理{% endblock %}

{# 侧边栏宽度 #}
{% block module_sidebar_width %}232px{% endblock %}

{# 模块侧边栏 #}
{% block module_sidebar %}
  {% include "customer_management/_sidebar.html" %}
{% endblock %}

{# 内容包装器样式覆盖 #}
{% block module_content_wrapper_styles %}
.customer-content-wrapper {
  padding: 8px 8px 24px 8px;
}
{% endblock %}

{# 内容包装器类名覆盖 #}
{% block module_content_wrapper_class %}customer-content-wrapper{% endblock %}
```

### 计划管理模块 `_base.html`

```django
{% extends "shared/module_base.html" %}
{% load static %}

{% block module_title %}计划管理{% endblock %}
{% block module_sidebar_width %}232px{% endblock %}

{% block module_sidebar %}
  {% include "plan_management/_sidebar.html" %}
{% endblock %}

{% block module_styles %}
<link rel="stylesheet" href="{% static 'css/components/plan_specific.css' %}">
{% endblock %}
```

### 具体页面使用

```django
{% extends "customer_management/_base.html" %}
{% load static %}

{% block pm_title %}客户管理{% endblock %}
{% block pm_subtitle %}<span class="pm-subtitle">数据展示中心 - 集中展示客户、联系人、商机等关键指标和动态</span>{% endblock %}

{% block pm_content %}
  <!-- 页面内容 -->
{% endblock %}
```

## 迁移步骤

1. **创建共享模板**：`shared/module_base.html` ✅
2. **更新各模块的 `_base.html`**：
   - 改为继承 `shared/module_base.html`
   - 移除重复的样式和脚本定义
   - 只保留模块特定的配置
3. **统一 Block 命名**：确保所有页面使用 `pm_title`, `pm_subtitle`, `pm_actions`, `pm_content`
4. **测试验证**：确保各模块页面正常显示

## 注意事项

1. **样式一致性**：页面标题区域的样式必须与共享表单模板保持一致
2. **Block 命名**：统一使用 `pm_*` 前缀的 Block 名称
3. **向后兼容**：保留 `module_*` 前缀的 Block 作为别名，方便迁移
4. **内容包装器**：各模块可以覆盖 `module_content_wrapper_class` 和 `module_content_wrapper_styles` 来自定义样式

## 相关文件

- `shared/two_column_layout_base.html` - 两栏布局基础模板
- `shared/module_base.html` - 模块基础模板（本文件）
- `{module_name}/_base.html` - 各模块的基础模板
- `static/css/components/pm_page_header.css` - 页面标题区域样式
- `static/js/pm_page_header_fix.js` - 页面标题修复脚本

