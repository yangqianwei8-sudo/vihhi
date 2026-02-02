# list-layout.css 与通用样式重复定义检查报告

**已执行（按建议修改）：**  
- 已移除 list_page_base.html、plan_decompose.html、strategic_goal_decompose.html 对 list_page_base_v2.css 的引用。  
- 已删除 components/list_page_base_v2.css 文件，列表/分解页样式仅由 common.css → list-layout.css 提供。  
- tables.css 中 `.list-empty-state*` 保留（模板中仍大量使用该类名，与 list-layout 的 `.list-page-empty*` 并存）。  

---

## 一、重复定义概览

| 类型 | 通用样式文件 | 与 list-layout.css 的关系 |
|------|--------------|---------------------------|
| **大量重复** | `components/list_page_base_v2.css` | 整文件与 list-layout.css 末尾「兼容旧类名」块几乎一致 |
| **覆盖关系** | `core/base.css` | 仅覆盖部分属性的 border-color，非整块重复 |
| **部分重叠** | `components/tables.css` | `.list-empty-state*` 与 list_page_base_v2 重复；表格相关与 list-layout 互补 |

---

## 二、详细重复内容

### 1. list_page_base_v2.css 与 list-layout.css（大量重复）

**list-layout.css 第 2160–2389 行** 注释写明：

```css
/* 兼容旧类名样式（原 list_page_base_v2.css）
   所有样式已从 list_page_base_v2.css 迁移并统一管理
   文件已删除，兼容样式保留在此处 */
```

但 **list_page_base_v2.css 仍存在且被 list_page_base.html 单独引入**，导致同一套选择器被两处定义，属于重复定义。

**重复的选择器与规则（两文件内容高度一致）：**

| 选择器/区块 | list_page_base_v2.css | list-layout.css |
|-------------|------------------------|------------------|
| 通用直角 | `.list-stats-section *`, `.list-filters-section *`, `.list-table-section *`, `.list-pagination-section *`, `.list-btn`, `.list-stat-card` 等 `border-radius: 0 !important` | 同上，并多了 `[class*="card"]` |
| `.list-stats-section` 及 `.row` | 统计区域 margin、flex、col 布局 | 同上（含变量 fallback） |
| `.list-filters-section` | 筛选区 margin、padding、背景、边框、栅格、表单项 | 同上 |
| `.list-filters-section .col-md-auto .list-btn` | 筛选区按钮高度、对齐 | 同上 |
| `.list-filters-section .form-label` / `.form-control` / `.form-select` | 字体、边框、padding、focus | 同上 |
| `.list-table-section` | `margin-bottom: 16px` | 同上 |
| `.list-btn` / `.list-btn-primary` / `.list-btn-outline` | 按钮基础、主色、描边及 hover | 同上（v2 用硬编码色，list-layout 用 CSS 变量） |
| `.list-pagination-section` / `.list-pagination` / `.list-pagination-info` | 分页区域、布局、文字样式 | 同上（细节略有差异，如 list-layout 多 `gap`） |
| `.list-pagination-controls .pagination` / `.page-link` / `.page-item.active` / `.page-item.disabled` | 分页控件、链接、当前页、禁用态 | 同上 |
| `.btn-group` 及 `.btn-group .btn:not(:last-child)` | 按钮组间距 | 同上 |
| `@media (max-width: 768px)` | 筛选栅格 50%、分页纵向排列 | 同上 |

**结论：**  
list_page_base_v2.css 与 list-layout.css 中「兼容旧类名」段落为同一套列表页样式，属于**整块重复**。list-layout 已写明“从 list_page_base_v2 迁移”，但 v2 文件未下线且仍被引用。

---

### 2. core/base.css 与 list-layout.css（覆盖关系，非整块重复）

base.css 中以下规则**只覆盖边框颜色**（`border-bottom-color` / `border-top-color`），注释写明用于覆盖 list-layout：

| 位置 | 选择器 | 作用 |
|------|--------|------|
| 845–857 | `.list-page-table thead th`, `.list-page-table tbody td` 等 | 列表表格分隔线颜色 |
| 855–857 | `.group-header td` | 分组表头分隔线 |
| 914–916 | `.list-page-filters-header` | 筛选区标题分隔线 |
| 969–971 | `.list-page-header` | 列表页标题分隔线 |
| 973–975 | `.list-page-tabs-section` | 标签页区域分隔线 |
| 979–989 | `.nav-tabs`, `.nav-tabs .nav-link` 等 | 标签页导航分隔线 |

list-layout.css 中对上述选择器有**完整定义**（display、padding、border、margin 等）；base.css 仅用 `!important` 统一分隔线颜色，属于**有意覆盖**，不是“同一段样式写两遍”的重复定义。

---

### 3. components/tables.css 与 list-layout / list_page_base_v2

**3.1 与 list_page_base_v2.css 的重复**

tables.css 第 556–577 行：

- `.list-empty-state`
- `.list-empty-state-icon`
- `.list-empty-state-text`
- `.list-empty-state-hint`

与 **list_page_base_v2.css 第 143–164 行** 的同一组选择器**语义和规则一致**（空状态居中、图标、文案、提示），仅 tables 使用变量、v2 使用硬编码色，属于**重复定义**。

list-layout.css 使用的是另一套类名：`.list-page-empty` / `.list-page-empty-icon` / `.list-page-empty-text` / `.list-page-empty-actions`，与 `.list-empty-state*` 不是同一选择器，但用途相同（列表空状态）。

**3.2 与 list-layout.css 的关系**

- tables.css 中 `.list-page-table-container`、`.list-page-table` 等为**列表表格主定义**。
- list-layout.css 仅对 `.list-page-container.view-card .list-page-table-container` 做 `display: none`，二者为**互补**，不是重复。

---

## 三、总结与建议

| 序号 | 重复/重叠项 | 建议 |
|------|-------------|------|
| 1 | **list_page_base_v2.css 整文件** 与 list-layout.css「兼容旧类名」块 | 二选一保留一处：要么在 list_page_base.html 中**移除对 list_page_base_v2.css 的引用**，仅依赖 common.css → list-layout.css；要么从 list-layout.css 中**删除该兼容块**，仅保留 list_page_base_v2.css。推荐保留 list-layout 并停用 v2 文件，避免双份加载。 |
| 2 | **base.css** 对 list 相关选择器的 border-color 覆盖 | 保留，属于设计上的统一分隔线颜色，非重复定义。 |
| 3 | **tables.css** 与 **list_page_base_v2.css** 中的 `.list-empty-state*` | 保留一处即可：若保留 list_page_base_v2.css，可删 tables.css 中该段；若废弃 v2，保留 tables.css 或统一改为 list-layout 的 `.list-page-empty*` 并只在一处定义。 |

**优先建议：**  
- 在 `list_page_base.html` 中**去掉**对 `list_page_base_v2.css` 的 `<link>`，仅通过 common.css 引入 list-layout.css。  
- 确认无其他模板单独引用 list_page_base_v2.css 后，可将 list_page_base_v2.css 中与 list-layout 重复的段落删除或整文件废弃，并统一空状态类名（.list-page-empty* 或 .list-empty-state*）只在一处定义。
