# 统一入口 CSS 治理销项记录

与 `static/css/common.css` 及“治理封账/禁止回流”规则配套的检查清单。

---

## CSS-01：确认生产环境是否合并/打包 @import

- **结论**：**否**
- **证据**：
  - 项目未使用 PostCSS/Webpack/Vite 等前端构建；Django 仅使用 `ManifestStaticFilesStorage`（或生产环境 `CompressedManifestStaticFilesStorage`）做静态文件收集与文件名哈希，**不解析、不合并** CSS 内的 `@import`。
  - 浏览器加载 `common.css` 后会对每个 `@import url(...)` 发起**串行请求**，首屏与弱网会受影响。
- **建议**：生产环境用构建把 core + components + layouts 合并为少量文件（如 `main.css` + `modules/*.css`）；开发可保留当前分拆结构。
- **入口说明**：已在 `common.css` 文件头注释中记录上述结论与建议。

---

## CSS-02：`components/pages.css` 职责审计并决定归属

- **结论**：已完成审计与拆分。
- **操作**：
  - **通用页面壳/内容组件**（form-page-title、pm-page-header、summary-card、modal-form-section、task-card、project-card、kanban、empty-state、activity-list、data-cards、forecast-*、filter-bar、list-table、key-clients-card 等）保留在 **components 层**，文件重命名为 **`components/page-shell.css`**，继续由 common.css 引入。
  - **页面特例**（隐藏 center-hero、表单卡片上边距、容器上边距调整）迁至 **`layouts/form-page-overrides.css`**，**不**放入 common.css；仅由 **`create_form_base.html`** 通过 `{% block base_extra_css %}` 按需引入，符合“组件主权/页面不覆盖 core class”的布局层特例。

---

## CSS-03：全局“交互修复”缩小作用域/找根因，禁止全局 z-index 兜底

- **结论**：已改为**仅对 modifier 生效**。
- **操作**：
  - 从 common.css 中移除对 `.workspace-content`、`.customer-content`、`.workspace-main`、`.form-section`、`form` 的全局 `position: relative; z-index: 1; pointer-events: auto`。
  - 改为仅对以下 **modifier class** 生效：
    - `.workspace-content--ensure-interactive`
    - `.customer-content--ensure-interactive`
    - `.workspace-main--ensure-interactive`
    - `.form-section--ensure-interactive`
    - `form.form--ensure-interactive`
  - 若某页出现点击穿透/被遮罩盖住，在对应容器上加上述 modifier 再生效，并排查根因（如 `navigation.css` 的 `.navbar::before`、modals 的 overlay 等 `pointer-events`/`z-index`）。

---

## CSS-04：`two_column_layout.css` 归位到 layouts（可选）

- **结论**：已归位。
- **操作**：
  - 文件从 `components/two_column_layout.css` 迁移至 **`layouts/two-column-layout.css`**（与 `three-column-layout.css` 命名一致）。
  - common.css 中 @import 已更新为 `layouts/two-column-layout.css`。
  - 原 `components/two_column_layout.css` 已删除。

---

## CSS-05：第三方/流程样式是否必须全站加载（可选）

- **结论**：已改为**按需引入**。
- **操作**：
  - **qixinbao-autofill.css**：从 common.css 全局 @import 中移除；仅在需要企信宝自动填充的页面（如 `contact_form.html`）通过模板 `extra_css`/单独 `<link>` 引入。
  - **approval_path.css**：从 common.css 全局 @import 中移除；仅在需要审批路径时间线的页面（如 `customer_detail.html`）通过模板单独 `<link>` 引入。
  - 上述两文件在 common.css 中已注释并注明“按需引入”。

---

## 无障碍 forced-colors

- 当前 `forced-colors` 与 `forced-color-adjust: auto` 写法保留。
- `.navbar, button, a` 使用 `preserve-parent` 可能导致部分主题下可读性下降；**建议后续只对确实需要保持品牌色的元素**使用 `preserve-parent`，不扩大范围。已在 common.css 中加注释提醒。

---

---

## 验收与证据（仅验证、未改代码）

### 风险点 A：pages.css 迁移完整性（450 行截断风险）

- **结论**：**已修复（CSS-02 最小修复）。**
- **证据**：
  - 已将 git 中原 `pages.css` 第 450–620 行（`.forecast-container` 完整规则体 + 预测/统计/筛选/表格/重点客户卡片段，**不含** 621+ 行 overrides）补回 `components/page-shell.css`，替换原截断的末行 `.forecast-container {`。
  - **`.forecast-container` 规则闭合**：`rg -n "\.forecast-container\s*\{"` → 第 **446** 行；规则体 446–453 行，含闭合 `}`。
  - **花括号自检**：`{` 与 `}` 数量均为 80，相等。
  - 本次修复**仅修改 1 个文件**：`backend/static/css/components/page-shell.css`；未改动 `layouts/form-page-overrides.css`、模板/JS/Python。

### 风险点 B：`base_extra_css` 位置与顺序

- **结论**：**符合要求。**
- **证据**：
  - `two_column_layout_base.html` 中 `{% block base_extra_css %}` 位于 **第 10 行**，在 `<head>` 内（`<head>` 自第 4 行起）。
  - 顺序：`common.css` → **base_extra_css** → `bootstrap.min.css` → 内联 `<style>` → `{% block extra_head %}`（其内为 `extra_css`、`module_base_styles`、`module_styles`、`module_extra_css` 等）。
  - `base_extra_css` 在 `extra_css` / `module_extra_css` **之前**，不会覆盖关系混乱；create_form_base 注入的 form-page-overrides.css 会先于各页的 extra_css 加载，顺序正确。

### 验收 1：全站 CSS 引用链

- **结论**：**common.css 所引路径均存在。**
- **证据**：
  - `components/page-shell.css`：存在。
  - `layouts/two-column-layout.css`：存在。
  - `layouts/form-page-overrides.css`：存在（由 create_form_base 的 base_extra_css 引入，非 common.css @import）。
  - common.css 中所有 @import 的 core/components/layouts 路径经 list_dir 核对均存在。

### 验收 2：按需 CSS 是否在需要处引入

- **结论**：**是，且使用合法 block。**
- **证据**：
  - **customer_detail.html**：在 `{% block extra_css %}` 内引入 `approval_path.css`（与 common.css 同 block），路径 `{% static 'css/approval_path.css' %}` 正确。
  - **contact_form.html**：在 `{% block extra_css %}` 内引入 `qixinbao-autofill.css`（与 common.css 同 block），路径 `{% static 'css/qixinbao-autofill.css' %}` 正确。
  - 两处均非内联、非乱放，符合「合法 CSS block」约定。

### 验收 3：交互修复 modifier 落点与 smoke test 建议

- **结论**：**当前未在任何页面加 `--ensure-interactive`，需按主流程验证后再按需加。**
- **建议策略**：先不加任何 modifier → 跑一遍 Top 流程 → 仅在复现「不可点击/穿透」的页面给对应容器加 modifier，并记录根因与证据。
- **建议 smoke test 清单（5 个页面）**：
  1. 列表页（如计划列表/客户列表）— 筛选、分页、行操作按钮可点。
  2. 详情页（如客户详情/计划详情）—  Tab、按钮、审批路径区域可点。
  3. 创建/编辑表单页（如新建计划/新建客户）— 表单控件、提交/取消可点。
  4. 带 modal 的页面（如删除确认、筛选设置）— 打开/关闭、确定/取消可点。
  5. 两栏布局首页（如计划首页）— 侧栏、主区、标题区可点。
- 若上述任一处出现不可点击，再在该页对应容器上加 `--ensure-interactive` 并排查根因（如遮罩 z-index/pointer-events）。

---

## 任务单销项状态

| 项 | 状态 | 说明 |
|----|------|------|
| CSS-01 | ✅ | 生产未合并 @import，证据与建议已写入 common.css 与本文档 |
| CSS-02 | ✅ 通过 | pages.css → page-shell.css + form-page-overrides.css；**验收：page-shell 截断已修复，缺失段已补回，语法闭合，仅改 1 文件** |
| CSS-03 | ✅ 需验收 | 交互修复仅 modifier 生效；**验收：主流程是否出现不可点击 / 是否需 ensure modifier → 建议按 smoke test 清单验证后再按需加** |
| CSS-04 | ✅ 需验收 | two_column_layout 归位 layouts；**验收：base_extra_css 是否在 head 内且顺序正确 → 已确认在 head 内、顺序正确** |
| CSS-05 | ✅ 需验收 | qixinbao/approval_path 按需引入；**验收：customer_detail/contact_form 是否仍正确引入且路径正确 → 已确认使用 extra_css block、路径正确** |
