# 表单卡片对齐规范指南

## 📋 概述

本文档定义了表单页面中卡片对齐的规范和最佳实践，确保所有表单页面的卡片能够正确对齐。

## ⚠️ 核心原则

### 1. **禁止使用多余的 wrapper div**

❌ **错误示例：**
```html
<div class="payment-info-card-wrapper">
    <div class="form-section">
        <!-- 表单内容 -->
    </div>
</div>
```

✅ **正确示例：**
```html
<div class="form-section">
    <!-- 表单内容 -->
</div>
```

**原因：**
- 多余的 wrapper div 会增加 DOM 层级，影响 CSS 选择器匹配
- 可能导致样式继承问题
- 使统一的对齐规则无法正确应用

### 2. **卡片必须直接存在**

所有卡片（`.card`、`.form-section`、`.info-card`）必须直接存在于 `workspace-main` 或其直接子容器中，不要嵌套在无意义的容器中。

### 3. **禁止重复定义对齐规则**

❌ **错误示例：**
```css
/* 在具体页面中定义 */
.form-section {
    padding: 24px;  /* 错误：覆盖了统一规则 */
}
```

✅ **正确示例：**
```css
/* 在 module_base.html 中统一管理 */
.workspace-main .form-section {
    padding: 20px 24px !important;
    margin-bottom: 1rem !important;
}
```

### 4. **对齐规则的定义位置**

所有卡片的对齐规则（padding、margin-bottom）统一在 `module_base.html` 的 `extra_css` 块中定义：

```html
{% block extra_css %}
<style>
    /* 统一的对齐规则 */
    .workspace-main .card,
    .workspace-main .form-section,
    .workspace-main .info-card {
        padding: 20px 24px !important;
        margin-bottom: 1rem !important;
    }
</style>
{% endblock %}
```

### 5. **form-actions 的特殊处理**

`form-actions` 位于 `form-section` 内部，需要使用负 margin 抵消 `form-section` 的 padding：

```css
.form-actions {
    margin-left: -24px !important;
    margin-right: -24px !important;
    padding: var(--form-spacing) 24px 0 !important;
}
```

这样可以确保按钮栏与卡片内容区域对齐。

## 📐 对齐规则详情

### 桌面端（>768px）
- `padding: 20px 24px !important`
- `margin-bottom: 1rem !important`

### 平板端（≤768px）
- `padding: 1rem !important` (16px)
- `margin-bottom: 1rem !important`

### 手机端（≤576px）
- `padding: 12px !important`
- `margin-bottom: 1rem !important`

## ✅ 代码审查清单

在创建或修改表单页面时，请检查：

- [ ] 是否有多余的 wrapper div 包裹 `form-section`？
- [ ] `form-section` 是否直接存在？
- [ ] 是否有重复的 `padding` 或 `margin-bottom` 定义？
- [ ] 是否使用了正确的 base 模板（`form_page_base.html`）？
- [ ] `form-actions` 是否正确处理了对齐问题？
- [ ] 所有卡片是否都使用了统一的 CSS 类名？

## 🔍 常见错误

### 错误1：多余的 wrapper div
```html
<!-- ❌ 错误 -->
<div class="payment-info-card-wrapper">
    <div class="form-section">...</div>
</div>

<!-- ✅ 正确 -->
<div class="form-section">...</div>
```

### 错误2：多余的闭合标签
```html
<!-- ❌ 错误 -->
</div>  <!-- form-section结束 -->
</div>  <!-- 多余的 -->
</div>  <!-- 多余的 -->

<!-- ✅ 正确 -->
</div>  <!-- form-section结束 -->
```

### 错误3：重复定义样式
```css
/* ❌ 错误：在具体页面中定义 */
.form-section {
    padding: 24px;
}

/* ✅ 正确：使用统一的规则，只在 module_base.html 中定义 */
```

### 错误4：form-actions 不对齐
```css
/* ❌ 错误：没有处理 form-section 的 padding */
.form-actions {
    padding: 1rem;
}

/* ✅ 正确：使用负 margin 抵消 padding */
.form-actions {
    margin-left: -24px !important;
    margin-right: -24px !important;
    padding: var(--form-spacing) 24px 0 !important;
}
```

## 🛠️ 修复步骤

如果发现卡片对齐问题，按以下步骤修复：

1. **检查 DOM 结构**
   - 移除多余的 wrapper div
   - 修复多余的闭合标签
   - 确保 `form-section` 直接存在

2. **检查 CSS 定义**
   - 移除重复的 padding/margin 定义
   - 确保使用统一的对齐规则
   - 添加 `!important` 确保优先级

3. **检查 form-actions**
   - 确认使用负 margin 抵消 padding
   - 检查响应式样式是否正确

4. **验证修复**
   - 检查所有设备尺寸的对齐情况
   - 确保所有卡片都正确对齐

## 📚 相关文件

- `backend/templates/shared/module_base.html` - 统一的对齐规则定义
- `backend/templates/shared/form_page_base.html` - 表单页面基模板
- `backend/templates/customer_management/contract_form.html` - 参考实现

## 💡 最佳实践

1. **始终使用 base 模板**
   - 继承 `form_page_base.html` 而不是直接继承 `module_base.html`
   - 这样可以自动获得正确的对齐规则

2. **保持 DOM 结构简单**
   - 避免不必要的嵌套
   - 直接使用 `form-section` 类

3. **使用统一的 CSS 类名**
   - `.form-section` - 表单分组卡片
   - `.card` - 通用卡片
   - `.info-card` - 信息卡片

4. **遵循响应式设计**
   - 所有对齐规则都有响应式支持
   - 不要覆盖响应式规则

## 📞 问题反馈

如果发现对齐问题，请：
1. 检查是否符合本规范
2. 查看 `module_base.html` 中的统一规则
3. 参考 `contract_form.html` 的实现方式
4. 如有疑问，请咨询团队

---

**最后更新：** 2024年
**维护者：** 开发团队

