# 详情页容器管理规范

## 📋 概述

本文档定义了详情页系统中容器的命名规范、使用方式和样式管理规则，确保容器样式的一致性和可维护性。

## 🎯 容器分类

### 1. 布局容器（Layout Containers）

用于组织页面结构和排列子元素，通常**不可见**（无背景、边框、阴影）。

#### 详情页专用容器（使用 `detail-` 前缀）

| 类名 | 用途 | 文件位置 |
|------|------|----------|
| `.detail-layout` | 最外层布局容器 | `_layout.css` |
| `.detail-content` | 内容区域容器，管理所有区块的垂直排列 | `_layout.css` |
| `.detail-tabs-container` | 标签页容器 | `_layout.css` |
| `.detail-actions` | 操作按钮容器 | `_layout.css` |

#### 通用容器（使用 `info-` 前缀）

| 类名 | 用途 | 文件位置 |
|------|------|----------|
| `.info-grid` | 网格布局容器 | `_components.css` (详情页) / `cards.css` (通用) |
| `.info-list` | 列表布局容器 | `_components.css` |

### 2. 卡片容器（Card Containers）

用于承载内容区块，**可见**（有背景、边框、阴影）。

| 类名 | 用途 | 文件位置 |
|------|------|----------|
| `.detail-section` | 详情区块卡片 | `_components.css` |
| `.info-card` | 通用信息卡片 | `cards.css` |

## 📐 容器层次结构

```
.detail-layout (最外层布局容器)
  └── .detail-actions (操作按钮容器)
  └── .detail-content (内容区域容器)
      └── .detail-section (区块卡片)
          └── .info-card-body (卡片内容)
              └── .info-grid / .info-list (字段容器)
                  └── 字段组件
```

## 🎨 样式规范

### 1. 变量使用

详情页容器统一使用详情页专用变量：

```css
/* ✅ 正确：使用详情页变量 */
.detail-content {
    gap: var(--detail-section-gap);  /* 32px */
}

.detail-section .info-grid {
    gap: var(--detail-field-gap);    /* 16px */
}

/* ❌ 错误：直接使用基础变量 */
.detail-content {
    gap: var(--spacing-xl);  /* 应该使用 --detail-section-gap */
}
```

### 2. 响应式断点

统一使用详情页断点变量：

```css
/* ✅ 正确：使用详情页断点 */
@media (max-width: 768px) {  /* --detail-breakpoint-md */
    /* 样式 */
}

/* ❌ 错误：使用硬编码值 */
@media (max-width: 767px) {  /* 应该使用 768px */
    /* 样式 */
}
```

### 3. 选择器优先级

详情页中的容器样式使用更具体的选择器，确保覆盖通用样式：

```css
/* ✅ 正确：使用具体选择器 */
.detail-section .info-grid {
    gap: var(--detail-field-gap);
}

/* ❌ 错误：可能被通用样式覆盖 */
.info-grid {
    gap: var(--detail-field-gap);
}
```

## 📝 使用示例

### 标准布局

```html
<div class="detail-layout">
    <!-- 操作按钮 -->
    <div class="detail-actions">
        <button class="btn">编辑</button>
    </div>
    
    <!-- 内容区域 -->
    <div class="detail-content">
        <!-- 区块卡片 -->
        <div class="info-card detail-section">
            <div class="info-card-header">
                <h5 class="info-card-title">基本信息</h5>
            </div>
            <div class="info-card-body">
                <!-- 网格容器 -->
                <div class="info-grid info-grid-2">
                    <div>字段1</div>
                    <div>字段2</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 标签页布局

```html
<div class="detail-layout detail-layout-tabbed">
    <div class="detail-tabs-container">
        <ul class="nav nav-tabs">...</ul>
        <div class="tab-content">
            <div class="detail-content">
                <!-- 区块内容 -->
            </div>
        </div>
    </div>
</div>
```

## ⚠️ 注意事项

1. **不要混用变量**：详情页容器必须使用 `--detail-*` 变量，不要使用 `--info-grid-gap` 或 `--spacing-*`
2. **必须指定列数**：使用 `.info-grid` 时必须显式指定 `.info-grid-2`、`.info-grid-3` 或 `.info-grid-4`
3. **保持层次结构**：遵循容器层次结构，不要跳过层级
4. **响应式一致性**：统一使用详情页断点变量，保持响应式行为一致

## 🔄 与通用样式的区别

| 特性 | 详情页容器 | 通用容器 |
|------|-----------|---------|
| 变量前缀 | `--detail-*` | `--info-*` 或 `--spacing-*` |
| 文件位置 | `details/_components.css` | `components/cards.css` |
| 选择器 | `.detail-section .info-grid` | `.info-grid` |
| 响应式断点 | `--detail-breakpoint-*` | 通用断点 |

## 📚 相关文件

- `details/_layout.css` - 布局容器样式
- `details/_components.css` - 组件容器样式
- `details/_variables.css` - 详情页变量定义
- `components/cards.css` - 通用容器样式

