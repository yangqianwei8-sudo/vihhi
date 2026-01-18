# 列表页共享模板使用指南

## 📋 概述

`list_page_base.html` 是一个**共享的列表页模板**，继承自 `module_base.html`，用于各种列表页面（客户列表、联系人列表、商机列表等）。

## ✨ 特性

- ✅ 继承自 `module_base.html`，统一页面结构
- ✅ 简洁、整齐、美观、稳重的设计风格
- ✅ 灰色、黑色为主色调，卡片直角设计
- ✅ 完整的列表页功能：统计卡片、筛选、操作栏、表格、分页
- ✅ 响应式设计，支持移动端
- ✅ 灵活的可扩展性，所有区域都支持 block 覆盖

## 📝 使用方式

### 基础使用

```django
{% extends "shared/list_page_base.html" %}
{% load static %}

{% block list_page_title %}客户列表{% endblock %}
{% block list_page_subtitle_content %}查看和管理所有客户信息{% endblock %}

{% block list_page_actions %}
  <a href="{% url 'customer_create' %}" class="list-btn list-btn-primary">创建客户</a>
{% endblock %}

{% block list_table_headers %}
  <th>客户名称</th>
  <th>联系人</th>
  <th>电话</th>
  <th>状态</th>
  <th>操作</th>
{% endblock %}

{% block list_table_rows %}
  {% for customer in page_obj %}
  <tr>
    <td>{{ customer.name }}</td>
    <td>{{ customer.contact_name }}</td>
    <td>{{ customer.phone }}</td>
    <td>
      <span class="badge bg-secondary">{{ customer.get_status_display }}</span>
    </td>
    <td>
      <div class="btn-group btn-group-sm">
        <a href="{% url 'customer_detail' customer.id %}" class="btn btn-outline-primary" title="查看">
          <i class="bi bi-eye"></i>
        </a>
        <a href="{% url 'customer_edit' customer.id %}" class="btn btn-outline-secondary" title="编辑">
          <i class="bi bi-pencil"></i>
        </a>
      </div>
    </td>
  </tr>
  {% empty %}
  <tr>
    <td colspan="5" class="list-empty-state">
      <div class="list-empty-state-icon">📋</div>
      <div class="list-empty-state-text">暂无客户数据</div>
      <div class="list-empty-state-hint">请创建第一条客户记录开始使用</div>
    </td>
  </tr>
  {% endfor %}
{% endblock %}
```

### 完整示例（包含统计卡片和筛选）

```django
{% extends "shared/list_page_base.html" %}
{% load static %}

{% block list_page_title %}客户列表{% endblock %}
{% block list_page_subtitle_content %}查看和管理所有客户信息{% endblock %}

{% block list_page_actions %}
  <a href="{% url 'customer_create' %}" class="list-btn list-btn-primary">创建客户</a>
  <a href="{% url 'customer_export' %}" class="list-btn list-btn-outline">导出</a>
{% endblock %}

{% block list_stats_content %}
  <div class="row g-3">
    <div class="col-md-3">
      <div class="list-stat-card">
        <div class="list-stat-label">客户总数</div>
        <div class="list-stat-value">{{ total_count }}</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="list-stat-card">
        <div class="list-stat-label">活跃客户</div>
        <div class="list-stat-value">{{ active_count }}</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="list-stat-card">
        <div class="list-stat-label">本月新增</div>
        <div class="list-stat-value">{{ month_new_count }}</div>
      </div>
    </div>
    <div class="col-md-3">
      <div class="list-stat-card">
        <div class="list-stat-label">待跟进</div>
        <div class="list-stat-value">{{ follow_up_count }}</div>
      </div>
    </div>
  </div>
{% endblock %}

{% block list_filters_content %}
  <div class="col-md-3">
    <label class="form-label">客户名称</label>
    <input type="text" name="name" class="form-control" value="{{ request.GET.name }}" placeholder="请输入客户名称">
  </div>
  <div class="col-md-3">
    <label class="form-label">状态</label>
    <select name="status" class="form-select">
      <option value="">全部状态</option>
      {% for value, label in status_choices %}
      <option value="{{ value }}" {% if request.GET.status == value|stringformat:"s" %}selected{% endif %}>{{ label }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-3">
    <label class="form-label">创建时间</label>
    <input type="date" name="created_date" class="form-control" value="{{ request.GET.created_date }}">
  </div>
{% endblock %}

{% block list_table_headers %}
  <th>客户名称</th>
  <th>联系人</th>
  <th>电话</th>
  <th>邮箱</th>
  <th>状态</th>
  <th>创建时间</th>
  <th>操作</th>
{% endblock %}

{% block list_table_rows %}
  {% for customer in page_obj %}
  <tr>
    <td><strong>{{ customer.name }}</strong></td>
    <td>{{ customer.contact_name|default:"-" }}</td>
    <td>{{ customer.phone|default:"-" }}</td>
    <td>{{ customer.email|default:"-" }}</td>
    <td>
      <span class="badge bg-secondary">{{ customer.get_status_display }}</span>
    </td>
    <td>{{ customer.created_at|date:"Y-m-d H:i" }}</td>
    <td>
      <div class="btn-group btn-group-sm">
        <a href="{% url 'customer_detail' customer.id %}" class="btn btn-outline-primary" title="查看">
          <i class="bi bi-eye"></i>
        </a>
        <a href="{% url 'customer_edit' customer.id %}" class="btn btn-outline-secondary" title="编辑">
          <i class="bi bi-pencil"></i>
        </a>
        <a href="{% url 'customer_delete' customer.id %}" class="btn btn-outline-danger" title="删除" onclick="return confirm('确定要删除吗？')">
          <i class="bi bi-trash"></i>
        </a>
      </div>
    </td>
  </tr>
  {% empty %}
  <tr>
    <td colspan="7" class="list-empty-state">
      <div class="list-empty-state-icon">📋</div>
      <div class="list-empty-state-text">暂无客户数据</div>
      <div class="list-empty-state-hint">请创建第一条客户记录开始使用</div>
    </td>
  </tr>
  {% endfor %}
{% endblock %}
```

## 🎯 可用的 Block

### 页面标题区域

- `list_page_title` - 页面主标题（必需）
- `list_page_subtitle_content` - 页面副标题内容（可选）

### 统计卡片区域（可选）

- `list_stats_section` - 整个统计卡片区域（可完全覆盖）
- `list_stats_content` - 统计卡片内容

### 筛选区域（可选）

- `list_filters_section` - 整个筛选区域（可完全覆盖）
- `list_filters_content` - 筛选字段内容
- `list_filters_actions` - 筛选操作按钮（查询、重置）
- `list_filters_reset_url` - 重置按钮的 URL（默认：当前路径）

### 操作栏

- `list_action_bar_section` - 整个操作栏区域（可完全覆盖）
- `list_action_bar_count` - 记录数量（默认：`page_obj.paginator.count`）
- `list_page_actions` - 页面操作按钮（创建、导出等）

### 表格区域

- `list_table_section` - 整个表格区域（可完全覆盖）
- `list_table_headers` - 表格表头（必需）
- `list_table_rows` - 表格行内容（必需）

### 分页区域（可选）

- `list_pagination_section` - 整个分页区域（可完全覆盖）
- 分页会自动显示（当 `page_obj.has_other_pages` 为 True 时）

## 🎨 样式类

### 按钮样式

- `.list-btn` - 基础按钮样式
- `.list-btn-primary` - 主要按钮（黑色背景）
- `.list-btn-outline` - 次要按钮（白色背景，灰色边框）

### 统计卡片样式

- `.list-stat-card` - 统计卡片容器
- `.list-stat-label` - 统计标签
- `.list-stat-value` - 统计数值

### 表格样式

- `.list-table` - 表格样式
- `.list-empty-state` - 空状态样式

## 📱 响应式支持

模板已内置响应式支持：
- **桌面端（>768px）**: 完整布局
- **移动端（≤768px）**: 
  - 筛选字段垂直排列
  - 操作栏垂直排列
  - 表格横向滚动
  - 分页信息垂直排列

## 🔧 视图函数要求

视图函数需要提供以下变量：

```python
from django.core.paginator import Paginator
from django.shortcuts import render

def customer_list(request):
    # 获取查询参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # 查询数据
    queryset = Customer.objects.all()
    if search:
        queryset = queryset.filter(name__icontains=search)
    if status:
        queryset = queryset.filter(status=status)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # 统计信息（可选）
    total_count = Customer.objects.count()
    active_count = Customer.objects.filter(status='active').count()
    
    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        # ... 其他变量
    }
    
    return render(request, 'customer_management/customer_list.html', context)
```

## 📚 相关文件

- `shared/module_base.html` - 模块基础模板（父模板）
- `shared/_partials/_list_stats.html` - 统计卡片组件
- `shared/_partials/_list_filters.html` - 筛选组件
- `shared/_partials/_list_table.html` - 表格组件
- `static/css/components/list_layout.css` - 列表布局样式

## 💡 注意事项

1. **必需 Block**: `list_page_title`、`list_table_headers`、`list_table_rows` 是必需的
2. **分页对象**: 确保视图函数提供 `page_obj` 对象（Django Paginator）
3. **空状态**: 在 `list_table_rows` 中使用 `{% empty %}` 处理空数据
4. **筛选表单**: 筛选区域会自动保留 GET 参数，分页时会自动保留筛选条件
5. **样式覆盖**: 可以通过 `module_extra_css` block 添加自定义样式

## 🎨 设计风格

- **颜色方案**: 灰色（#F5F5F5, #E0E0E0, #666666）、黑色（#1A1A1A, #333333）
- **卡片样式**: 直角设计（无圆角）
- **字体大小**: 标题 20px，正文 13px，标签 12px
- **间距**: 统一使用 8px、12px、16px、20px、24px 的间距系统
