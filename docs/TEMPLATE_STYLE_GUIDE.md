# 共享表单模板使用指南

## 概述

共享表单模板 (`_shared_form_wrapper.html` 和 `_shared_form_wrapper_customer.html`) 提供了统一的表单页面样式和布局。

## 重要原则

### 1. 样式选择器使用全局选择器

**❌ 错误示例：**
```css
.plan-content .pm-page-header {
  /* 样式 */
}
```

**✅ 正确示例：**
```css
.pm-page-header {
  /* 样式 */
}
```

**原因：**
- 全局选择器不依赖特定的父容器类名
- 可以确保样式在任何基础模板中都能正确应用
- 避免因父容器类名不同导致样式不生效

### 2. 基础模板样式必须与共享模板一致

如果基础模板（如 `customer_management/_base.html`）有自己的样式定义，必须与共享模板完全一致。

**必需的样式属性：**
- `.pm-page-header::after`: 下划线（纯黑色，延伸到屏幕边缘）
- `h1 font-size: 24px`
- `.pm-subtitle font-size: 12px`
- `.pm-actions align-self: flex-end`（按钮底部对齐）
- `.pm-page-header align-items: flex-end`（标题和副标题底部对齐）

### 3. 修改样式时的同步要求

如果修改共享模板的样式，必须同时更新：
1. 共享模板文件（`_shared_form_wrapper.html` 或 `_shared_form_wrapper_customer.html`）
2. 相关的基础模板文件（如 `customer_management/_base.html`）

## 使用步骤

1. **继承共享模板**
   ```django
   {% extends "shared/_partials/_shared_form_wrapper_customer.html" %}
   {% load static %}
   ```

2. **覆盖必要的块**
   ```django
   {% block pm_title %}{{ page_title|default:"创建客户" }}{% endblock %}
   {% block pm_subtitle %}<span class="pm-subtitle">{{ form_page_subtitle_text|default:"请填写客户基本信息" }}</span>{% endblock %}
   {% block pm_actions %}
   <a href="{% url 'business_pages:customer_list' %}" class="list-btn">
     返回列表
   </a>
   {% endblock %}
   ```

3. **删除老设计元素**
   - 删除旧的页面标题样式
   - 删除旧的表单容器样式
   - 删除重复的样式定义

## 验证

运行验证脚本检查样式一致性：
```bash
python3 check_template_styles.py
```

## 常见问题

### Q: 为什么样式不生效？

A: 检查以下几点：
1. 样式选择器是否使用了全局选择器（不是 `.plan-content .pm-page-header`）
2. 基础模板的样式是否与共享模板一致
3. 是否有其他样式覆盖了共享模板的样式

### Q: 如何添加新的样式？

A: 
1. 在共享模板中添加样式（使用全局选择器）
2. 如果基础模板有相关样式，同步更新
3. 运行验证脚本确保一致性

## 相关文件

- `backend/templates/shared/_partials/_shared_form_wrapper.html` - 通用共享模板
- `backend/templates/shared/_partials/_shared_form_wrapper_customer.html` - 客户管理专用共享模板
- `backend/templates/customer_management/_base.html` - 客户管理基础模板
- `check_template_styles.py` - 样式一致性验证脚本
