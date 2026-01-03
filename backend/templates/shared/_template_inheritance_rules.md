# 模板继承规则和约定

## 🎯 核心原则

### 1. 继承链深度限制

**硬性规则：最多3层继承**

```
✅ 允许：
base.html -> module_base.html -> 具体页面 (3层)

❌ 禁止：
base.html -> A -> B -> C -> 具体页面 (4层+)
```

### 2. 块命名规范

**统一使用前缀区分不同层级的块：**

| 层级 | 前缀 | 示例 |
|------|------|------|
| 模块级 | `module_` | `module_content`, `module_extra_css` |
| 详情页 | `detail_` | `detail_content`, `detail_timeline` |
| 列表页 | `list_page_` | `list_page_title`, `list_page_table` |
| 表单页 | `form_page_` | `form_page_title`, `form_page_content` |

### 3. 片段命名规范

**使用 `_` 前缀表示片段模板（partial）：**

```
✅ 正确：
_workspace_layout.html
_detail_hero.html
_list_filters.html

❌ 错误：
workspace_layout.html (缺少 _ 前缀)
detail_hero.html (缺少 _ 前缀)
```

### 4. 块定义位置

**规则：块必须在继承链中定义，不能在 include 片段中定义**

```django
✅ 正确：
{# module_base.html #}
{% block module_content %}{% endblock %}

{# 具体页面 #}
{% block module_content %}内容{% endblock %}

❌ 错误：
{# _workspace_layout.html #}
{% block module_content %}{% endblock %}  ← 不能在 include 片段中定义块
```

---

## 📋 模板类型和继承关系

### 类型1：通用模块页面

**继承：** `module_base.html`

**使用场景：**
- 普通的内容页面
- 不需要特殊布局的页面
- 只需要侧边栏导航的页面

**示例：**
```django
{% extends "shared/module_base.html" %}
{% block module_content %}
    <!-- 页面内容 -->
{% endblock %}
```

---

### 类型2：详情页面

**继承：** `detail_page_base.html`（直接继承 `base.html`）

**使用场景：**
- 需要 Hero 区域的详情页
- 需要时间线侧边栏的页面
- 需要三栏布局的页面

**可覆盖的块：**
- `detail_hero_icon` - Hero 图标
- `detail_hero_title` - Hero 标题
- `detail_hero_subtitle` - Hero 副标题
- `detail_actions` - 操作按钮区域
- `detail_content` - 主要内容
- `detail_timeline` - 时间线侧边栏

**示例：**
```django
{% extends "shared/detail_page_base.html" %}
{% block detail_hero_title %}工作流详情{% endblock %}
{% block detail_content %}
    <!-- 详情内容 -->
{% endblock %}
```

---

### 类型3：列表页面

**继承：** `list_page_base.html`（直接继承 `base.html`）

**使用场景：**
- 数据列表页面
- 需要筛选、搜索、分页的页面
- 需要批量操作的页面

**可覆盖的块：**
- `list_page_title` - 页面标题
- `list_page_filters` - 筛选区域
- `list_page_table` - 表格内容
- `list_page_extra_css` - 额外 CSS
- `list_page_custom_js` - 自定义 JavaScript

---

### 类型4：表单页面

**继承：** `form_page_base.html`（直接继承 `base.html`）

**使用场景：**
- 创建/编辑表单页面
- 需要表单验证的页面
- 需要分步表单的页面

**可覆盖的块：**
- `form_page_title` - 表单标题
- `form_page_content` - 表单内容
- `form_page_extra_css` - 额外 CSS
- `form_page_custom_js` - 自定义 JavaScript

---

## 🔍 块覆盖规则

### 规则1：只能覆盖父模板中已定义的块

```django
{# module_base.html #}
{% block module_content %}{% endblock %}

{# 具体页面 #}
{% block module_content %}
    内容  ← ✅ 正确：覆盖父模板的块
{% endblock %}

{% block new_block %}
    内容  ← ❌ 错误：父模板中没有定义此块
{% endblock %}
```

### 规则2：使用 `{{ block.super }}` 扩展父块

```django
{# module_base.html #}
{% block module_extra_css %}
<link rel="stylesheet" href="base.css">
{% endblock %}

{# 具体页面 #}
{% block module_extra_css %}
{{ block.super }}  ← 包含父模板的内容
<link rel="stylesheet" href="custom.css">
{% endblock %}
```

### 规则3：避免在多个层级定义同名块

```django
❌ 错误结构：
{# module_base.html #}
{% block content %}{% endblock %}

{# detail_page_base.html #}
{% block content %}{% endblock %}  ← 与父模板冲突

✅ 正确结构：
{# module_base.html #}
{% block module_content %}{% endblock %}

{# detail_page_base.html #}
{% block detail_content %}{% endblock %}  ← 使用不同前缀
```

---

## 🧩 片段使用规则

### 规则1：片段不定义块

```django
✅ 正确：
{# _workspace_layout.html #}
<div class="workspace">
    <main class="workspace-main">
        <!-- 内容 -->
    </main>
</div>

❌ 错误：
{# _workspace_layout.html #}
<div class="workspace">
    {% block content %}{% endblock %}  ← 不能在片段中定义块
</div>
```

### 规则2：片段通过 include 组合

```django
{# module_base.html #}
{% block content %}
    {% include 'shared/_workspace_layout.html' %}
{% endblock %}
```

### 规则3：片段可以接受上下文变量

```django
{# _detail_hero.html #}
<div class="detail-hero">
    <h1>{{ detail_title|default:"详情" }}</h1>
</div>

{# detail_page_base.html #}
{% include 'shared/_detail_hero.html' with detail_title=page_title %}
```

---

## 📊 模板选择决策树

```
需要特殊布局？
├─ 是 → 详情页布局？
│   ├─ 是 → 继承 detail_page_base.html
│   └─ 否 → 列表页布局？
│       ├─ 是 → 继承 list_page_base.html
│       └─ 否 → 表单页布局？
│           ├─ 是 → 继承 form_page_base.html
│           └─ 否 → 继承 module_base.html
└─ 否 → 继承 module_base.html
```

---

## ✅ 代码审查检查点

创建或修改模板时检查：

1. **继承链深度**
   - [ ] 继承链 ≤ 3层
   - [ ] 没有不必要的中间层

2. **块命名**
   - [ ] 使用统一前缀
   - [ ] 块名称清晰明确
   - [ ] 没有命名冲突

3. **块定义**
   - [ ] 块在继承链中定义
   - [ ] 不在 include 片段中定义块
   - [ ] 块有文档注释

4. **片段使用**
   - [ ] 片段使用 `_` 前缀
   - [ ] 片段不定义块
   - [ ] 片段职责单一

5. **文档**
   - [ ] 模板有功能说明注释
   - [ ] 可覆盖的块有文档
   - [ ] 上下文变量有说明

---

## 🚨 常见错误和解决方案

### 错误1：继承链过深

```django
❌ 错误：
base.html -> A -> B -> C -> 页面 (5层)

✅ 解决：
base.html -> module_base.html -> 页面 (3层)
```

### 错误2：块命名冲突

```django
❌ 错误：
{# A.html #}
{% block content %}{% endblock %}

{# B.html #}
{% block content %}{% endblock %}  ← 冲突

✅ 解决：
{# A.html #}
{% block module_content %}{% endblock %}

{# B.html #}
{% block detail_content %}{% endblock %}  ← 使用不同前缀
```

### 错误3：在片段中定义块

```django
❌ 错误：
{# _layout.html #}
{% block content %}{% endblock %}

✅ 解决：
{# module_base.html #}
{% block content %}
    {% include '_layout.html' %}
    {% block module_content %}{% endblock %}
{% endblock %}
```

---

## 📚 参考示例

查看以下文件了解正确的模板结构：

- `shared/module_base.html` - 通用模块基础模板
- `shared/detail_page_base.html` - 详情页基础模板
- `shared/_workspace_layout.html` - 布局片段示例
- `workflow_engine/home.html` - 通用模块页面示例
- `workflow_engine/workflow_detail.html` - 详情页面示例

