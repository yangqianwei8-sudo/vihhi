# 侧边栏扩展使用指南

## 📋 概述

为了防止改造不彻底、支持自定义内容实现和样式隔离，我们在共享模板中提供了扩展点机制。

## ⚠️ 重要规范

### 禁止行为

1. ❌ **禁止覆盖 `module_sidebar` block 来替换共享侧边栏模板**
2. ❌ **禁止覆盖 `sidebar_content` block 来替换共享侧边栏模板**
3. ❌ **禁止直接修改 `sidebar_v2_wireframe_fixed.html` 的 HTML 结构**
4. ❌ **禁止使用旧的 `two-col-sidebar` 类名体系**
5. ❌ **禁止直接修改 `.vh-sb` 的全局样式（应使用后代选择器）**

### 正确做法

1. ✅ **使用扩展点 block 添加自定义内容**
2. ✅ **使用样式隔离 block 添加自定义样式**
3. ✅ **使用模块特定的命名空间避免全局污染**
4. ✅ **使用 CSS 变量覆盖共享样式**

## 🎯 扩展点说明

### 1. module_base.html 的扩展点

#### 1.1 `module_sidebar_extra` - 侧边栏内容扩展

**位置**: 在共享侧边栏模板之后

**用途**: 在侧边栏外部添加自定义内容（不影响共享模板结构）

**示例**:
```django
{% block module_sidebar_extra %}
  <div class="module-sidebar-custom">
    <!-- 自定义内容 -->
  </div>
{% endblock %}
```

#### 1.2 `module_sidebar_styles` - 侧边栏样式隔离

**位置**: 在样式 block 中

**用途**: 添加模块特定的侧边栏样式（样式隔离）

**示例**:
```django
{% block module_sidebar_styles %}
<style>
  /* 方式1：使用模块特定的命名空间 */
  .module-sidebar-custom {
    padding: 8px;
    background: #F5F5F5;
  }
  
  /* 方式2：使用 CSS 变量覆盖 */
  :root {
    --module-sidebar-bg: #F5F5F5;
  }
  
  /* 方式3：使用后代选择器限制作用域 */
  .vh-sb .module-sidebar-custom {
    padding: 8px;
  }
</style>
{% endblock %}
```

### 2. two_column_layout_base.html 的扩展点

#### 2.1 `sidebar_content_extra` - 侧边栏内容扩展

**位置**: 在共享侧边栏模板之后

**用途**: 在侧边栏外部添加自定义内容

**示例**:
```django
{% block sidebar_content_extra %}
  <div class="custom-sidebar-content">
    <!-- 自定义内容 -->
  </div>
{% endblock %}
```

#### 2.2 `sidebar_custom_styles` - 侧边栏样式隔离

**位置**: 在 `sidebar_styles` block 中

**用途**: 添加自定义侧边栏样式（样式隔离）

**示例**:
```django
{% block sidebar_custom_styles %}
<style>
  .custom-sidebar-content {
    padding: 8px;
    background: #F5F5F5;
  }
</style>
{% endblock %}
```

### 3. sidebar_v2_wireframe_fixed.html 的扩展点

#### 3.1 `sidebar_top_extra` - 顶部区域扩展

**位置**: 在标题区域内部

**用途**: 在顶部标题区域添加自定义内容

**示例**:
```django
{% block sidebar_top_extra %}
  <div class="sidebar-top-custom">
    <!-- 自定义内容 -->
  </div>
{% endblock %}
```

#### 3.2 `sidebar_nav_extra` - 导航区域扩展

**位置**: 在菜单项之后

**用途**: 在导航菜单后添加自定义内容

**示例**:
```django
{% block sidebar_nav_extra %}
  <div class="sidebar-nav-custom">
    <!-- 自定义内容 -->
  </div>
{% endblock %}
```

#### 3.3 `sidebar_bottom_extra` - 底部区域扩展

**位置**: 在默认底部按钮之后

**用途**: 在底部功能区添加自定义内容

**示例**:
```django
{% block sidebar_bottom_extra %}
  <div class="sidebar-bottom-custom">
    <!-- 自定义内容 -->
  </div>
{% endblock %}
```

## 📝 完整使用示例

### 示例 1：在资源管理模块中添加自定义内容

```django
{# resource_standard/_base.html #}
{% extends "shared/module_base.html" %}

{# 方式1：在侧边栏外部添加自定义内容 #}
{% block module_sidebar_extra %}
  <div class="resource-sidebar-extra">
    <div class="resource-sidebar-widget">
      <h3>快捷操作</h3>
      <a href="#">快速创建</a>
    </div>
  </div>
{% endblock %}

{# 方式2：添加自定义样式（样式隔离） #}
{% block module_sidebar_styles %}
<style>
  /* 使用模块特定的命名空间 */
  .resource-sidebar-extra {
    padding: 16px;
    background: #F5F5F5;
    border-top: 1px solid #E0E0E0;
  }
  
  .resource-sidebar-widget {
    padding: 12px;
    background: #FFFFFF;
    border-radius: 4px;
  }
</style>
{% endblock %}
```

### 示例 2：在共享侧边栏内部添加自定义内容

```django
{# 如果需要在侧边栏内部添加内容，可以通过覆盖 sidebar_top_extra 等 block #}
{% block module_sidebar %}
  {% include "shared/sidebar_v2_wireframe_fixed.html" %}
  
  {# 注意：sidebar_top_extra 等 block 需要在共享模板内部定义 #}
  {# 如果需要在内部添加，需要创建中间层模板 #}
{% endblock %}
```

## 🔍 样式隔离最佳实践

### 1. 使用模块特定的命名空间

```django
{% block module_sidebar_styles %}
<style>
  /* ✅ 正确：使用模块前缀 */
  .resource-sidebar-custom {
    /* 样式 */
  }
  
  /* ❌ 错误：直接修改全局样式 */
  .vh-sb {
    /* 不要这样做 */
  }
</style>
{% endblock %}
```

### 2. 使用后代选择器限制作用域

```django
{% block module_sidebar_styles %}
<style>
  /* ✅ 正确：使用后代选择器 */
  .vh-sb .resource-sidebar-custom {
    /* 样式 */
  }
</style>
{% endblock %}
```

### 3. 使用 CSS 变量覆盖

```django
{% block module_sidebar_styles %}
<style>
  /* ✅ 正确：使用 CSS 变量 */
  :root {
    --module-sidebar-bg: #F5F5F5;
  }
</style>
{% endblock %}
```

## ✅ 检查清单

使用扩展点时，请检查：

- [ ] 是否使用了正确的扩展点 block
- [ ] 是否使用了模块特定的命名空间
- [ ] 是否避免了直接修改全局样式
- [ ] 是否遵循了样式隔离原则
- [ ] 是否添加了必要的注释说明

## 📚 相关文档

- [Django 模板继承文档](https://docs.djangoproject.com/en/stable/topics/templates/#template-inheritance)
- [BEM 命名规范](http://getbem.com/)
