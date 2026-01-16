# 共享列表页面组件使用说明

## 组件列表

### 1. `_list_stats.html` - 统计卡片组件
**位置**: `shared/_partials/_list_stats.html`

**使用方式**:
```django
{# 方式1: 覆盖block定义具体内容 #}
{% include "shared/_partials/_list_stats.html" %}
{% block list_stats_content %}
<div class="row g-3 mb-3">
  <div class="col-md-2">
    <div class="info-card">
      <div class="info-card-header">
        <span class="info-card-title">总数</span>
      </div>
      <div class="info-card-value">{{ total_count }}</div>
    </div>
  </div>
  ...
</div>
{% endblock %}

{# 方式2: 使用stats变量（需要在视图中准备数据） #}
{% include "shared/_partials/_list_stats.html" with stats=stats_list %}
```

### 2. `_list_filters.html` - 筛选组件
**位置**: `shared/_partials/_list_filters.html`

**使用方式**:
```django
{% include "shared/_partials/_list_filters.html" %}
{% block filter_fields %}
<div class="col-md-3">
  <label class="form-label small">搜索</label>
  <input type="text" name="search" class="form-control form-control-sm" 
         value="{{ search }}" placeholder="搜索关键词">
</div>
<div class="col-md-2">
  <label class="form-label small">状态</label>
  <select name="status" class="form-select form-select-sm">
    <option value="">全部状态</option>
    {% for value, label in status_choices %}
    <option value="{{ value }}" {% if status == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
</div>
{% endblock %}
{% block reset_button %}
<div class="col-md-1">
  <label class="form-label small">&nbsp;</label>
  <a href="{% url 'your_list_url' %}" class="btn btn-outline-secondary btn-sm w-100">重置</a>
</div>
{% endblock %}
```

### 3. `_list_action_bar.html` - 操作栏组件
**位置**: `shared/_partials/_list_action_bar.html`

**使用方式**:
```django
{% include "shared/_partials/_list_action_bar.html" with total_count=page_obj.paginator.count %}
```

### 4. `_list_table.html` - 表格组件
**位置**: `shared/_partials/_list_table.html`

**使用方式**:
```django
{% include "shared/_partials/_list_table.html" %}
{% block list_table_headers %}
<th>编号</th>
<th>名称</th>
<th>状态</th>
<th>操作</th>
{% endblock %}

{% block list_table_rows %}
{% for item in page_obj %}
<tr>
  <td><code>{{ item.number }}</code></td>
  <td>{{ item.name }}</td>
  <td><span class="badge bg-secondary">{{ item.get_status_display }}</span></td>
  <td>
    <div class="btn-group btn-group-sm">
      <a href="{% url 'item_detail' item.id %}" class="btn btn-outline-primary" title="查看">
        <i class="bi bi-eye"></i>
      </a>
    </div>
  </td>
</tr>
{% empty %}
<tr>
  <td colspan="4" class="text-center text-muted py-5">
    <i class="bi bi-inbox" style="font-size: 48px; opacity: 0.3;"></i>
    <p class="mt-3 mb-0">暂无数据</p>
    <p class="text-muted small">请创建第一条记录开始使用</p>
  </td>
</tr>
{% endfor %}
{% endblock %}
```

### 5. `_base_list_page.html` - 基础列表页面模板
**位置**: `shared/_partials/_base_list_page.html`

**使用方式**:
```django
{% extends "your_base_template.html" %}
{% load static %}

{% block content %}
{% include "shared/_partials/_base_list_page.html" %}
{% block list_page_title %}我的列表{% endblock %}
{% block list_page_description %}列表页面描述{% endblock %}
{% block list_stats_content %}
  {# 统计卡片内容 #}
{% endblock %}
{% block filter_fields %}
  {# 筛选字段 #}
{% endblock %}
{% block list_table_headers %}
  {# 表头 #}
{% endblock %}
{% block list_table_rows %}
  {# 表格行 #}
{% endblock %}
{% endblock %}
```

## 完整示例

### 示例：商机列表页面
```django
{% extends "customer_management/_base.html" %}
{% load static %}

{% block cm_title %}商机列表{% endblock %}
{% block cm_subtitle %}<span class="pm-subtitle">查看和管理所有商机</span>{% endblock %}

{% block cm_actions %}
<a href="{% url 'business_pages:opportunity_create' %}" class="list-btn list-btn-primary">
  创建商机
</a>
{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/common.css' %}">
<link rel="stylesheet" href="{% static 'css/components/list_layout.css' %}">
<style>
    .list-page-container {
        padding: 12px !important;
        gap: 8px !important;
    }
</style>
{% endblock %}

{% block cm_content %}
<div class="list-page-container">
    <div class="list-page-header">
        <h2 class="mb-0">商机列表</h2>
        <p class="text-muted mb-0 mt-1">查看和管理所有商机</p>
    </div>
    
    {% include "shared/_partials/_list_stats.html" %}
    {% block list_stats_content %}
    <div class="row g-3 mb-3">
      <div class="col-md-2">
        <div class="info-card">
          <div class="info-card-header">
            <span class="info-card-title">商机总数</span>
          </div>
          <div class="info-card-value">{{ total_opportunities|default:0 }}</div>
        </div>
      </div>
      ...
    </div>
    {% endblock %}
    
    {% include "shared/_partials/_list_filters.html" %}
    {% block filter_fields %}
    {# 筛选字段 #}
    {% endblock %}
    
    {% include "shared/_partials/_list_action_bar.html" with total_count=page_obj.paginator.count %}
    
    {% include "shared/_partials/_list_table.html" %}
    {% block list_table_headers %}
    {# 表头 #}
    {% endblock %}
    {% block list_table_rows %}
    {# 表格行 #}
    {% endblock %}
</div>
{% endblock %}
```

## 注意事项

1. 所有组件都支持block覆盖，可以根据需要自定义内容
2. 组件使用标准的Bootstrap样式类
3. 分页组件会自动保留所有GET参数
4. 空状态显示使用统一的样式
