# 两栏布局父模板使用说明

## 概述

`two_column_layout_base.html` 是一个通用的两栏布局父模板，提供：
- 左侧固定侧边栏
- 右侧自适应主内容区
- 响应式设计（移动端支持）
- 顶部导航栏集成

## 文件结构

```
templates/shared/
  ├── two_column_layout_base.html      # 父模板
  └── two_column_layout_example.html  # 使用示例

static/css/components/
  └── two_column_layout.css           # 样式文件
```

## 基本使用

### 1. 继承模板

```django
{% extends "shared/two_column_layout_base.html" %}
{% load static %}
```

### 2. 定义侧边栏内容

```django
{% block sidebar_content %}
  <div class="two-col-sidebar__header">
    <h2 class="two-col-sidebar__title">菜单标题</h2>
    <p class="two-col-sidebar__subtitle">副标题</p>
  </div>

  <nav class="two-col-sidebar__body">
    <!-- 你的菜单项 -->
    <ul class="list-unstyled">
      <li><a href="#">菜单项1</a></li>
      <li><a href="#">菜单项2</a></li>
    </ul>
  </nav>

  <div class="two-col-sidebar__footer">
    <!-- 底部内容 -->
  </div>
{% endblock %}
```

### 3. 定义主内容区

```django
{% block content_inner %}
  <div class="mb-4">
    <h1>页面标题</h1>
    <p>页面内容...</p>
  </div>
{% endblock %}
```

## 自定义侧边栏宽度

### 方法1：使用 CSS 变量

```django
{% block extra_css %}
<style>
  :root {
    --sidebar-width: 280px; /* 自定义宽度 */
  }
</style>
{% endblock %}
```

### 方法2：使用工具类

```django
{% block sidebar %}
  <aside class="two-col-sidebar two-col-sidebar--wide">
    <!-- 侧边栏内容 -->
  </aside>
{% endblock %}
```

可用工具类：
- `two-col-sidebar--narrow`: 180px
- `two-col-sidebar--wide`: 280px

## 完整示例

参考 `two_column_layout_example.html` 查看完整示例。

## 响应式行为

- **桌面端（>768px）**: 侧边栏固定在左侧，主内容区自适应
- **移动端（≤768px）**: 侧边栏变为抽屉式，可通过 JavaScript 控制显示/隐藏

## 可用的 Block

- `title`: 页面标题（`<title>` 标签）
- `top_nav`: 顶部导航栏（默认包含 `_top_nav.html`）
- `sidebar`: 整个侧边栏容器（可完全自定义）
- `sidebar_content`: 侧边栏内容（推荐使用）
- `content`: 主内容区容器（可完全自定义）
- `content_inner`: 主内容区内容（推荐使用）
- `extra_css`: 额外的 CSS
- `extra_js`: 额外的 JavaScript

## 样式定制

所有样式都在 `two_column_layout.css` 中定义，可以通过覆盖 CSS 变量或添加自定义样式来定制：

```django
{% block extra_css %}
<style>
  .two-col-sidebar {
    background: #f5f5f5;
  }
  
  .two-col-content {
    padding: 32px;
  }
</style>
{% endblock %}
```
