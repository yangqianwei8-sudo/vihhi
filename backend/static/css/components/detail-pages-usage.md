# 详情页面统一样式模板使用说明

## 概述

`detail-pages.css` 提供了详情页面的统一样式模板，包含页面标题区域、信息卡片、时间线、审核步骤等常用组件的样式。

## 自动加载

该样式文件已集成到 `common.css` 中，所有引入 `common.css` 的页面都会自动加载这些样式，无需额外引入。

## 组件使用示例

### 1. 页面标题区域（Hero区域）

```html
<div class="container-fluid py-4">
    <!-- 页面标题区域 -->
    <div class="center-hero">
        <div class="hero-icon">📋</div>
        <h1 class="hero-title">交付详情</h1>
        <p class="hero-subtitle">交付单号：{{ delivery.delivery_number }}</p>
    </div>
    
    <!-- 其他内容 -->
</div>
```

### 2. 信息卡片

#### 基础用法

```html
<div class="info-card">
    <div class="info-card-header">
        <h5 class="info-card-title">基本信息</h5>
    </div>
    <div class="info-card-body">
        <div class="info-grid info-grid-2">
            <div class="info-item">
                <span class="info-label">标签</span>
                <span class="info-value">值</span>
            </div>
        </div>
    </div>
</div>
```

#### 带淡入动画

```html
<div class="info-card info-card-fade-in">
    <!-- 内容 -->
</div>
```

#### 全宽信息项

```html
<div class="info-grid info-grid-2">
    <div class="info-item">
        <span class="info-label">普通项</span>
        <span class="info-value">值</span>
    </div>
    <div class="info-item info-item-full-width">
        <span class="info-label">全宽项（跨两列）</span>
        <span class="info-value">长文本内容</span>
    </div>
</div>
```

#### 信息值链接

```html
<div class="info-item">
    <span class="info-label">关联项目</span>
    <span class="info-value">
        <a href="#" class="info-value-link">项目名称</a>
    </span>
</div>
```

#### 数字值

```html
<div class="info-item">
    <span class="info-label">金额</span>
    <span class="info-value info-value-numeric">¥1,234.56</span>
</div>
```

### 3. 兼容旧版 info-row 布局

```html
<div class="info-card">
    <h5>基本信息</h5>
    <div class="info-row">
        <span class="info-label">标签1：</span>
        <span class="info-value">值1</span>
    </div>
    <div class="info-row">
        <span class="info-label">标签2：</span>
        <span class="info-value">值2</span>
    </div>
</div>
```

### 4. 时间线组件

#### 基础时间线

```html
<div class="info-card">
    <div class="info-card-header">
        <h5 class="info-card-title">跟踪记录</h5>
    </div>
    <div class="info-card-body">
        <div class="timeline">
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <h6>事件标题</h6>
                    <p>事件描述</p>
                    <small>2024-01-01 10:00</small>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <h6>另一个事件</h6>
                    <p>事件描述</p>
                    <small>2024-01-02 14:00</small>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 带状态的时间线

```html
<div class="timeline">
    <!-- 成功状态 -->
    <div class="timeline-item timeline-success">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
            <h6>已完成</h6>
            <p>操作成功完成</p>
        </div>
    </div>
    
    <!-- 警告状态 -->
    <div class="timeline-item timeline-warning">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
            <h6>待处理</h6>
            <p>需要进一步处理</p>
        </div>
    </div>
    
    <!-- 错误状态 -->
    <div class="timeline-item timeline-danger">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
            <h6>失败</h6>
            <p>操作失败</p>
        </div>
    </div>
</div>
```

### 5. 审核步骤组件

```html
<div class="info-card">
    <div class="info-card-header">
        <h5 class="info-card-title">审核流程</h5>
    </div>
    <div class="info-card-body">
        <div class="review-step completed">
            <h6>提交审核</h6>
            <p>已提交，等待审核</p>
            <small>2024-01-01 10:00</small>
        </div>
        <div class="review-step current">
            <h6>部门审核</h6>
            <p>正在审核中</p>
        </div>
        <div class="review-step pending">
            <h6>财务审核</h6>
            <p>等待审核</p>
        </div>
        <div class="review-step rejected">
            <h6>最终审批</h6>
            <p>已拒绝</p>
        </div>
    </div>
</div>
```

### 6. 记录项组件

```html
<div class="info-card">
    <div class="info-card-header">
        <h5 class="info-card-title">维护记录</h5>
    </div>
    <div class="info-card-body">
        <div class="record-item">
            <h6>维护记录 #1</h6>
            <p>维护内容描述</p>
            <small>2024-01-01</small>
        </div>
        <div class="record-item">
            <h6>维护记录 #2</h6>
            <p>维护内容描述</p>
            <small>2024-01-02</small>
        </div>
    </div>
</div>
```

### 7. 金额高亮

```html
<div class="info-item">
    <span class="info-label">总金额</span>
    <span class="info-value">
        <span class="amount-highlight">¥10,000.00</span>
    </span>
</div>

<!-- 收入（绿色） -->
<span class="amount-highlight income">¥5,000.00</span>

<!-- 支出（红色） -->
<span class="amount-highlight expense">-¥2,000.00</span>

<!-- 中性（蓝色） -->
<span class="amount-highlight neutral">¥0.00</span>
```

### 8. 状态徽章

```html
<!-- 使用 status-badge 类 -->
<span class="status-badge draft">草稿</span>
<span class="status-badge submitted">已提交</span>
<span class="status-badge approved">已审核</span>
<span class="status-badge posted">已过账</span>
<span class="status-badge rejected">已拒绝</span>
```

### 9. 操作按钮区域

```html
<!-- 右对齐（默认） -->
<div class="detail-actions">
    <a href="#" class="btn btn-outline-secondary">返回列表</a>
    <a href="#" class="btn btn-primary">编辑</a>
    <button class="btn btn-success">提交</button>
</div>

<!-- 左对齐 -->
<div class="detail-actions detail-actions-left">
    <!-- 按钮 -->
</div>

<!-- 居中 -->
<div class="detail-actions detail-actions-center">
    <!-- 按钮 -->
</div>

<!-- 两端对齐 -->
<div class="detail-actions detail-actions-between">
    <a href="#" class="btn btn-outline-secondary">返回</a>
    <div>
        <a href="#" class="btn btn-primary">编辑</a>
        <button class="btn btn-success">提交</button>
    </div>
</div>
```

## 完整示例

```html
{% extends "shared/module_base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/common.css' %}">
{% endblock %}

{% block module_content %}
<div class="container-fluid py-4">
    <!-- 页面标题区域 -->
    <div class="center-hero">
        <h1 class="hero-title">交付详情</h1>
        <p class="hero-subtitle">交付单号：{{ delivery.delivery_number }}</p>
    </div>

    <!-- 操作按钮 -->
    <div class="detail-actions">
        <a href="{% url 'delivery_pages:delivery_list' %}" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> 返回列表
        </a>
        <a href="{% url 'delivery_pages:delivery_edit' delivery.id %}" class="btn btn-primary">
            <i class="bi bi-pencil"></i> 编辑
        </a>
    </div>

    <!-- 基本信息卡片 -->
    <div class="info-card info-card-fade-in">
        <div class="info-card-header">
            <h5 class="info-card-title">基本信息</h5>
        </div>
        <div class="info-card-body">
            <div class="info-grid info-grid-2">
                <div class="info-item">
                    <span class="info-label">交付单号</span>
                    <span class="info-value info-value-bold">{{ delivery.delivery_number }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">交付状态</span>
                    <span class="info-value">
                        <span class="status-badge {{ delivery.status }}">
                            {{ delivery.get_status_display }}
                        </span>
                    </span>
                </div>
                <div class="info-item info-item-full-width">
                    <span class="info-label">交付说明</span>
                    <span class="info-value">{{ delivery.description|linebreaks }}</span>
                </div>
            </div>
        </div>
    </div>

    <!-- 时间线卡片 -->
    <div class="info-card info-card-fade-in">
        <div class="info-card-header">
            <h5 class="info-card-title">跟踪记录</h5>
        </div>
        <div class="info-card-body">
            <div class="timeline">
                {% for tracking in delivery.tracking_records.all %}
                <div class="timeline-item">
                    <div class="timeline-marker"></div>
                    <div class="timeline-content">
                        <h6>{{ tracking.get_event_type_display }}</h6>
                        <p>{{ tracking.event_description }}</p>
                        <small>{{ tracking.event_time|date:"Y-m-d H:i" }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 响应式支持

所有组件都支持响应式设计，在不同屏幕尺寸下会自动调整布局：

- **桌面端（>992px）**：完整布局，2列网格
- **平板端（768px-992px）**：单列布局，紧凑间距
- **移动端（<768px）**：单列布局，按钮全宽

## 注意事项

1. **自动加载**：样式已集成到 `common.css`，无需额外引入
2. **兼容性**：支持旧版的 `info-row` 布局方式
3. **扩展性**：可以通过 CSS 变量自定义颜色和间距
4. **打印样式**：已包含打印样式优化

## CSS 变量自定义

如果需要自定义样式，可以在模板中覆盖 CSS 变量：

```html
<style>
:root {
    --vh-primary: #your-color;
    --info-card-padding: 32px;
    --info-grid-gap: 24px;
}
</style>
```

## 迁移指南

如果现有详情页面使用了内联样式，可以按以下步骤迁移：

1. 移除模板中的 `<style>` 标签内的样式定义
2. 使用对应的 CSS 类名替换内联样式
3. 确保引入了 `common.css`（通常已包含）

例如，将：
```html
<style>
.center-hero { ... }
.info-row { ... }
</style>
```

替换为直接使用类名，因为样式已在 `detail-pages.css` 中定义。

