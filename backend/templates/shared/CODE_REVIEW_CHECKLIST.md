# 代码审查清单 - 表单页面

## 📋 卡片对齐规范检查

在审查表单页面代码时，请检查以下项目：

### ✅ DOM 结构检查

- [ ] **没有多余的 wrapper div**
  - 检查是否存在 `*-card-wrapper` 类的 div
  - 确认 `form-section` 是否直接存在，没有被无意义的容器包裹
  - 参考：`FORM_CARD_ALIGNMENT_GUIDE.md`

- [ ] **没有多余的闭合标签**
  - 检查 HTML 结构是否正确
  - 确认每个 `<div>` 都有对应的 `</div>`
  - 使用 HTML 验证工具检查

- [ ] **使用了正确的模板继承**
  - 确认继承自 `form_page_base.html`
  - 不要直接继承 `module_base.html`（除非有特殊原因）

### ✅ CSS 样式检查

- [ ] **没有重复定义对齐规则**
  - 检查是否定义了 `form-section` 的 `padding` 或 `margin-bottom`
  - 对齐规则应该统一由 `module_base.html` 管理
  - 如需自定义，只能添加额外属性，不能覆盖对齐规则

- [ ] **使用了统一的 CSS 类名**
  - `.form-section` - 表单分组卡片
  - `.card` - 通用卡片
  - `.info-card` - 信息卡片
  - 不要创建新的卡片类名（除非有特殊需求）

- [ ] **form-actions 对齐正确**
  - 检查是否使用了负 margin 抵消 padding
  - 确认响应式样式是否正确
  - 参考：`form_page_base.html` 中的实现

### ✅ 响应式设计检查

- [ ] **对齐规则支持响应式**
  - 桌面端：`padding: 20px 24px`
  - 平板端：`padding: 1rem` (16px)
  - 手机端：`padding: 12px`
  - 不要在具体页面中覆盖响应式规则

### ✅ 代码质量检查

- [ ] **代码注释清晰**
  - 关键部分有注释说明
  - 遵循项目的注释规范

- [ ] **代码格式统一**
  - 遵循项目的代码格式规范
  - 使用一致的缩进和换行

## 🔍 常见问题

### 问题1：多余的 wrapper div

**错误示例：**
```html
<div class="payment-info-card-wrapper">
    <div class="form-section">
        <!-- 内容 -->
    </div>
</div>
```

**正确示例：**
```html
<div class="form-section">
    <!-- 内容 -->
</div>
```

### 问题2：重复定义样式

**错误示例：**
```css
.form-section {
    padding: 24px;  /* 错误：覆盖了统一规则 */
}
```

**正确示例：**
```css
/* 不需要定义，使用 module_base.html 中的统一规则 */
```

### 问题3：form-actions 不对齐

**错误示例：**
```css
.form-actions {
    padding: 1rem;  /* 错误：没有处理 form-section 的 padding */
}
```

**正确示例：**
```css
.form-actions {
    margin-left: -24px !important;
    margin-right: -24px !important;
    padding: var(--form-spacing) 24px 0 !important;
}
```

## 📚 参考文档

- `FORM_CARD_ALIGNMENT_GUIDE.md` - 详细的对齐规范指南
- `module_base.html` - 统一的对齐规则定义
- `form_page_base.html` - 表单页面基模板
- `customer_management/contract_form.html` - 参考实现

## 🛠️ 工具

可以使用检查脚本验证模板：

```bash
python3 check_form_alignment.py <模板文件路径>
```

---

**最后更新：** 2024年
**维护者：** 开发团队

