# 模板使用指南

## 风格特点

- **简洁、美观、大方**：设计简洁，视觉美观，布局大方
- **颜色稳重**：以灰色、黑色为主色调
- **卡片直角**：所有卡片使用直角设计（无圆角）
- **无彩色图标**：使用简洁的符号代替彩色图标

## 模板结构

### 1. 两栏布局基础模板
`templates/shared/two_column_layout_base.html`

这是所有两栏布局页面的基础模板，提供：
- 统一的侧边栏引入方式
- 灵活的样式和脚本扩展点
- 可配置的侧边栏宽度

### 2. 侧边栏模板
`templates/shared/sidebar_v2_wireframe_fixed.html`

通用侧边栏模板，支持动态菜单数据。

### 3. 模块特定侧边栏
`templates/plan_management/_sidebar.html`

计划管理模块专用侧边栏，可扩展模块特定内容。

### 4. 模块基础模板
`templates/plan_management/_base.html`

计划管理模块的基础模板，继承两栏布局基础模板。

## 使用示例

### 基础使用

```django
{% extends "plan_management/_base.html" %}
{% load static %}

{% block pm_title %}页面标题{% endblock %}

{% block pm_subtitle %}
  <p class="pm-subtitle">页面副标题</p>
{% endblock %}

{% block pm_content %}
  <!-- 页面内容 -->
{% endblock %}
```

### 使用两栏布局基础模板

```django
{% extends "shared/two_column_layout_base.html" %}
{% load static %}

{% block title %}页面标题{% endblock %}

{% block sidebar_content %}
  {% include "shared/sidebar_v2_wireframe_fixed.html" %}
{% endblock %}

{% block content_inner %}
  <!-- 页面内容 -->
{% endblock %}
```

### 自定义侧边栏宽度

```django
{% block sidebar_width %}280px{% endblock %}
```

### 添加页面特定样式

```django
{% block extra_css %}
<style>
  .custom-style {
    /* 自定义样式 */
  }
</style>
{% endblock %}
```

### 添加页面特定脚本

```django
{% block extra_js %}
<script>
  // 自定义脚本
</script>
{% endblock %}
```

## 颜色方案

### 主要颜色
- **背景色**：`#FFFFFF`（白色）、`#F5F5F5`（浅灰）
- **文字色**：`#1A1A1A`（深黑）、`#333333`（黑色）、`#666666`（灰色）
- **边框色**：`#E0E0E0`（浅灰）
- **激活背景**：`#E8E8E8`（中灰）
- **悬停背景**：`#F5F5F5`（浅灰）

### 使用CSS变量

```css
/* 推荐使用CSS变量 */
color: var(--vh-text, #1A1A1A);
background: var(--vh-card-bg, #FFFFFF);
border-color: var(--vh-border, #E0E0E0);
```

## 样式规范

### 卡片样式
- **无圆角**：`border-radius: 0`
- **边框**：`1px solid #E0E0E0`
- **阴影**：`0 1px 3px rgba(0, 0, 0, 0.1)`

### 间距规范
- **页面内边距**：`24px`
- **卡片内边距**：`24px`
- **元素间距**：`16px`、`12px`、`8px`

### 字体规范
- **标题**：`font-size: 24px`，`font-weight: 600`
- **正文**：`font-size: 14px`，`font-weight: 400`
- **小字**：`font-size: 12px`

## 最佳实践

1. **统一使用基础模板**：所有页面应继承相应的基础模板
2. **模块化侧边栏**：每个模块创建自己的侧边栏模板
3. **使用CSS变量**：保持颜色一致性
4. **保持简洁**：避免过度装饰
5. **直角设计**：所有卡片和按钮使用直角

## 文件清单

- `templates/shared/two_column_layout_base.html` - 两栏布局基础模板
- `templates/shared/sidebar_v2_wireframe_fixed.html` - 通用侧边栏模板
- `templates/plan_management/_sidebar.html` - 计划管理模块侧边栏
- `templates/plan_management/_base.html` - 计划管理模块基础模板
- `static/css/components/sidebar_v2_fixed.css` - 侧边栏样式
- `static/css/components/two_column_layout.css` - 两栏布局样式
