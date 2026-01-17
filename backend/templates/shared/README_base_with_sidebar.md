# base_with_sidebar.html 使用指南

## 📋 概述

`base_with_sidebar.html` 是一个**完全独立的共享模板**，用于改造现有表单页面。此模板提供了统一的顶部导航栏和左侧栏布局，适用于所有需要左侧栏的页面。

## ⚠️ 重要说明

### 完全独立模板

此模板是**完全独立的**，不继承任何其他模板：
- ❌ 无 `{% extends %}`
- ❌ 无 `{% include %}`
- ✅ 所有样式硬编码
- ✅ 所有脚本内联

### 改造现有表单时的要求

当使用此模板改造已经存在的表单时，**必须完全清除旧的模板继承关系**：

1. **完全删除旧的 `{% extends %}` 语句**
   ```django
   ❌ 删除：{% extends "customer_management/_base.html" %}
   ❌ 删除：{% extends "shared/_partials/_shared_form_wrapper_customer.html" %}
   ❌ 删除：{% extends "plan_management/_base.html" %}
   ```

2. **完全删除旧的 `{% include %}` 语句**（如有）

3. **替换为新的继承语句**
   ```django
   ✅ 使用：{% extends "shared/base_with_sidebar.html" %}
   ```

4. **确保视图函数提供必需的变量**
   - `scene_groups`: 场景分组菜单数据（列表）
   - `user`: 当前用户对象（django.contrib.auth.models.User）

### 禁止行为

❌ **不能同时继承旧模板和新模板**
❌ **不能新旧模板混合使用**
❌ **不能保留旧的 block 定义**（如果与新模板的 block 冲突）

## 📝 使用步骤

### 步骤 1：替换模板继承

```django
{# 旧代码 - 删除 #}
{% extends "customer_management/_base.html" %}
{% load static %}

{# 新代码 - 使用 #}
{% extends "shared/base_with_sidebar.html" %}
{% load static %}
```

### 步骤 2：调整 Block 定义

#### 方式 1：完全覆盖 content block（推荐用于复杂表单）

```django
{% extends "shared/base_with_sidebar.html" %}
{% load static %}

{% block title %}创建客户 - 维海科技{% endblock %}

{% block content %}
  <div class="page-header">
    <h1 class="page-title">创建客户</h1>
    <p class="page-subtitle">请填写客户基本信息</p>
  </div>
  
  <form method="post" class="form-container">
    {% csrf_token %}
    <!-- 表单内容 -->
  </form>
{% endblock %}
```

#### 方式 2：使用嵌套 block（推荐用于简单表单）

```django
{% extends "shared/base_with_sidebar.html" %}
{% load static %}

{% block title %}创建客户 - 维海科技{% endblock %}

{% block page_title %}创建客户{% endblock %}
{% block page_subtitle %}请填写客户基本信息{% endblock %}

{% block page_content %}
  <form method="post" class="form-container">
    {% csrf_token %}
    <!-- 表单内容 -->
  </form>
{% endblock %}
```

### 步骤 3：更新视图函数

确保视图函数提供必需的变量：

```python
from backend.core.views import _build_scene_groups

def your_form_view(request):
    # 获取用户权限
    permission_set = get_user_permission_codes(request.user)
    
    # 构建场景分组菜单
    scene_groups = _build_scene_groups(permission_set, request.user)
    
    # 构建上下文
    context = {
        'scene_groups': scene_groups,
        'user': request.user,
        # ... 其他变量
    }
    
    return render(request, 'your_app/your_form.html', context)
```

### 步骤 4：删除旧的样式和脚本

删除表单页面中与旧模板相关的：
- 旧的 CSS 样式引用
- 旧的 JavaScript 脚本引用
- 旧的 block 定义（如果与新模板冲突）

## 🎯 可用的 Block

### 1. `title`
页面标题（浏览器标题栏）

```django
{% block title %}创建客户 - 维海科技{% endblock %}
```

### 2. `extra_css`
额外的 CSS 样式

```django
{% block extra_css %}
<style>
  .custom-style {
    /* 自定义样式 */
  }
</style>
{% endblock %}
```

### 3. `content`
主内容区域（可完全覆盖）

```django
{% block content %}
  <!-- 完全自定义布局 -->
{% endblock %}
```

### 4. `page_title`
页面标题（默认布局内）

```django
{% block page_title %}创建客户{% endblock %}
```

### 5. `page_subtitle`
页面副标题（默认布局内）

```django
{% block page_subtitle %}请填写客户基本信息{% endblock %}
```

### 6. `page_content`
页面主要内容（默认布局内）

```django
{% block page_content %}
  <!-- 表单内容 -->
{% endblock %}
```

### 7. `extra_js`
额外的 JavaScript 脚本

```django
{% block extra_js %}
<script>
  // 自定义脚本
</script>
{% endblock %}
```

## 📋 迁移检查清单

使用此模板改造表单时，请检查：

- [ ] 已删除旧的 `{% extends %}` 语句
- [ ] 已删除旧的 `{% include %}` 语句（如有）
- [ ] 已替换为 `{% extends "shared/base_with_sidebar.html" %}`
- [ ] 已调整 block 定义（使用新的 block 名称）
- [ ] 已删除旧的 CSS 样式引用
- [ ] 已删除旧的 JavaScript 脚本引用
- [ ] 已更新视图函数，提供 `scene_groups` 变量
- [ ] 已更新视图函数，提供 `user` 变量
- [ ] 已测试页面显示正常
- [ ] 已测试左侧栏菜单正常
- [ ] 已测试响应式设计（移动端）

## 🔍 常见问题

### Q: 能否同时使用旧模板和新模板？

**A: 不能！** 必须完全替换旧的模板继承关系，不能新旧混合使用。

### Q: 如果完全覆盖 `content` block，`page_title` 等嵌套 block 还有效吗？

**A: 无效。** 如果完全覆盖 `content` block，则 `page_title`、`page_subtitle`、`page_content` 等嵌套 block 将无效。此时应直接在 `content` block 中编写完整的内容。

### Q: 如何自定义左侧栏菜单？

**A:** 通过视图函数的 `scene_groups` 变量来控制。参考 `backend/core/views.py` 中的 `_build_scene_groups` 函数。

### Q: 视图函数中没有 `_build_scene_groups` 函数怎么办？

**A:** 需要从 `backend.core.views` 导入：
```python
from backend.core.views import _build_scene_groups
```

## 📚 相关文档

- [Django 模板继承文档](https://docs.djangoproject.com/en/stable/topics/templates/#template-inheritance)
- [总工作台首页配置说明.md](/总工作台首页配置说明.md)

## 🎨 模板特性

- ✅ 完全独立（无外部依赖）
- ✅ 所有样式硬编码
- ✅ 所有脚本内联
- ✅ 响应式设计（支持移动端）
- ✅ 顶部导航栏（黑底白字）
- ✅ 左侧栏（232px 宽度，场景式分组）
- ✅ 主内容区（可完全自定义）

