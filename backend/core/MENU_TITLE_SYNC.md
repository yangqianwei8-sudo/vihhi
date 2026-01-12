# 主内容区标题与左侧栏菜单同步

## 📋 概述

本功能实现了主内容区标题自动从左侧栏激活菜单项中获取，避免硬编码标题，保持标题与菜单项名称的一致性。

## 🎯 功能说明

当页面有左侧栏菜单时，主内容区的标题会自动显示当前激活菜单项的标签（`label`），无需在每个页面模板中硬编码标题。

## 🔧 实现方式

### 1. 辅助函数

在 `backend/core/views.py` 中提供了 `get_active_menu_label()` 函数：

```python
def get_active_menu_label(menu_items):
    """
    从菜单项列表中获取激活菜单项的标签
    
    Args:
        menu_items: 菜单项列表（module_sidebar_nav 格式）
    
    Returns:
        str: 激活菜单项的标签，如果没有找到则返回 None
    """
```

### 2. 视图函数集成

在视图函数的 `_context` 函数中，构建菜单后自动获取激活菜单标签：

```python
from backend.core.views import get_active_menu_label

def _context(page_title, page_icon, description, ...):
    # ... 构建菜单 ...
    context['module_sidebar_nav'] = _build_xxx_sidebar_nav(...)
    
    # 从激活菜单项中获取标签
    active_menu_label = get_active_menu_label(context['module_sidebar_nav'])
    if active_menu_label:
        context['active_menu_label'] = active_menu_label
    
    return context
```

### 3. 模板使用

模板会自动使用 `active_menu_label` 变量，如果没有提供，则从 `module_sidebar_nav` 中查找：

**详情页模板（detail_page_base.html）：**
```django
<h1 class="hero-title">
    {% block detail_hero_title %}
        {% if active_menu_label %}
            {{ active_menu_label }}
        {% elif module_sidebar_nav %}
            {% for menu_item in module_sidebar_nav %}
                {% if menu_item.active %}
                    {{ menu_item.label }}
                {% elif menu_item.children %}
                    {% for child in menu_item.children %}
                        {% if child.active %}
                            {{ child.label }}
                        {% endif %}
                    {% endfor %}
                {% endif %}
            {% endfor %}
        {% else %}
            详情
        {% endif %}
    {% endblock %}
</h1>
```

**列表页模板（list_page_base.html）：**
```django
<h1 class="list-page-title">
    {% block list_page_title %}
        {% if active_menu_label %}
            {{ active_menu_label }}
        {% elif module_sidebar_nav %}
            {% for menu_item in module_sidebar_nav %}
                {% if menu_item.active %}
                    {{ menu_item.label }}
                {% elif menu_item.children %}
                    {% for child in menu_item.children %}
                        {% if child.active %}
                            {{ child.label }}
                        {% endif %}
                    {% endfor %}
                {% endif %}
            {% endfor %}
        {% else %}
            列表
        {% endif %}
    {% endblock %}
</h1>
```

## 📝 使用示例

### 示例 1：行政管理模块

在 `backend/apps/administrative_management/views_pages.py` 中：

```python
from backend.core.views import get_active_menu_label

def _context(page_title, page_icon, description, ...):
    # ... 其他代码 ...
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['module_sidebar_nav'] = _build_administrative_sidebar_nav(permission_set, request.path)
        
        # 获取激活菜单标签
        active_menu_label = get_active_menu_label(context['module_sidebar_nav'])
        if active_menu_label:
            context['active_menu_label'] = active_menu_label
    
    return context
```

### 示例 2：客户管理模块

在 `backend/apps/customer_management/views_pages.py` 中：

```python
from backend.core.views import get_active_menu_label

def _context(page_title, page_icon, description, ...):
    # ... 构建菜单 ...
    context['module_sidebar_nav'] = _build_customer_management_menu(permission_set, active_id=active_menu_id)
    
    # 获取激活菜单标签
    active_menu_label = get_active_menu_label(context['module_sidebar_nav'])
    if active_menu_label:
        context['active_menu_label'] = active_menu_label
    
    return context
```

## ✅ 优势

1. **自动同步**：标题自动与菜单项名称保持一致
2. **减少硬编码**：无需在每个页面模板中硬编码标题
3. **易于维护**：修改菜单项名称时，标题自动更新
4. **向后兼容**：如果找不到激活菜单项，使用默认值

## 🔄 迁移指南

### 对于现有模块

1. **更新导入**：
   ```python
   from backend.core.views import get_active_menu_label
   ```

2. **在 `_context` 函数中添加**：
   ```python
   active_menu_label = get_active_menu_label(context['module_sidebar_nav'])
   if active_menu_label:
       context['active_menu_label'] = active_menu_label
   ```

3. **移除模板中的硬编码标题**（可选）：
   - 如果模板中硬编码了标题，可以移除，让系统自动使用菜单标签

### 对于新模块

直接使用 `get_active_menu_label()` 函数即可，模板会自动处理。

## 📚 相关文件

- `backend/core/views.py` - 辅助函数定义
- `backend/templates/shared/detail_page_base.html` - 详情页模板
- `backend/templates/shared/list_page_base.html` - 列表页模板
- `backend/apps/administrative_management/views_pages.py` - 示例实现

## ⚠️ 注意事项

1. **优先级**：`active_menu_label` 变量优先级最高，如果提供了该变量，模板会优先使用
2. **默认值**：如果没有找到激活菜单项，模板会使用默认值（"详情" 或 "列表"）
3. **子菜单**：如果激活的是子菜单项，会使用子菜单项的标签
4. **向后兼容**：如果子模板覆盖了 `detail_hero_title` 或 `list_page_title` 块，会优先使用子模板的值

