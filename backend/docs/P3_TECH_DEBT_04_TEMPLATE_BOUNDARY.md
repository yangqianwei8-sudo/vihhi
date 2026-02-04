# P3 技术债 TD-04：Templates 职责边界写死

## 1. 结论

`backend/templates/` 为**展示层**，只负责结构、样式声明与数据渲染；**不得**承担裁决、业务规则与 UI 行为逻辑。

---

## 2. 允许（Allow）

- 使用 HTML 结构、`{% extends %}` / `{% include %}`
- 声明 `class`、`data-*` 属性，供 CSS 与 JS 选择器使用
- 使用 `{{ variable }}`、`{% for %}`、`{% if %}` 等渲染上下文变量与展示逻辑
- 引用 `{% static %}` 加载 CSS/JS 文件
- 使用 templatetags 输出展示用标记（如格式化日期、枚举标签）
- 少量 `{% if %}` 控制区块显隐（仅展示分叉，非权限/状态裁决）

---

## 3. 禁止（Forbid）

1. **禁止** UI 行为内联 `<script>`：confirm、modal、toggle、batch 操作、表格勾选逻辑等必须在 `ui.js` 或页面专用 JS 中实现。
2. **禁止** inline style（`style="..."`）；样式只能通过 `class` 引用 components/layouts/pages。
3. **禁止** 在模板中写权限裁决或业务规则分叉：如 `{% if user.has_perm %}` 决定是否显示按钮、`{% if status == X %}` 决定状态机推进逻辑——此类逻辑属于 views/services（Python）。
4. **禁止** 复制结构导致分叉：在同一业务内复制整段 HTML 结构到多处，形成“相似但不复用”的模板分叉；应提取 `{% include %}` 或共用基模。
5. **禁止** 把业务 JS 混进基模模板（`list_page_base.html`、`detail_base.html`、`create_form_base.html`）；基模只保留结构占位与 `data-*`，行为由 `ui.js` 统一接管。
6. **禁止** 绕过 `ui.js` 主权：新增页面级 UI 行为（如弹窗、批量操作）不得在模板中写 `<script>`，只能通过 `ui.js` 扩展或页面级 JS 模块注册。

---

## 4. 责任归属（Ownership）

| 责任 | 归属 | 依据 |
|------|------|------|
| UI 行为（confirm/modal/toggle/batch） | `ui.js`、页面级 JS | P2 第 11/12 条、宪法 |
| 权限裁决、业务规则、状态机 | views / services（Python） | 宪法第 12 条 |
| 样式 | components / layouts / pages CSS | P2 第 10 条、宪法 |
| 结构、class、data-*、渲染变量 | templates | 本边界 |

---

## 5. 违规处理（Enforcement）

- **新增违规**：按宪法第 13 条，必须回退，拒绝合并，不接受「先合再改」。
- **回流违规**：若治理完成后再次出现内联 script、inline style、复制结构，按宪法第 14 条视为破坏系统结构，必须立即清算。

---

## 6. 完成判定（用于销项）

- 仅新增该文档
- 文档含「禁止/不得/只能/回退/清算」等关键词
- `git diff --stat` 仅 1 个文件
