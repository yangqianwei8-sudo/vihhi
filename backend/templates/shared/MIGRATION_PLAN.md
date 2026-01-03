# 方案二实施计划：组合模式 + 扁平继承

## 📊 修改量评估

### 需要修改的文件

**基础模板（3个文件）：**
- ✅ `detail_page_base.html` - 改为继承 `base.html`
- ✅ `list_page_base.html` - 改为继承 `base.html`
- ✅ `form_page_base.html` - 改为继承 `base.html`

**子页面（0个文件需要修改）：**
- ✅ 所有子页面**不需要修改**，因为块名称保持不变
- ✅ 继承关系自动更新（从4层变为3层）

**影响范围：**
- detail_page_base: 7 个页面（自动受益）
- list_page_base: 6 个页面（自动受益）
- form_page_base: 5 个页面（自动受益）

### 修改复杂度

**低复杂度：**
- 只需要修改 3 个基础模板
- 子页面完全不需要修改
- 块名称保持不变，向后兼容

---

## 🔧 实施步骤

### 步骤1：修改 detail_page_base.html

**变更：**
- `{% extends "shared/module_base.html" %}` → `{% extends "shared/base.html" %}`
- 添加 `{% include 'shared/_workspace_resources.html' %}` 到 `extra_css` 块
- 添加 `{% include 'shared/_workspace_scripts.html' %}` 到 `extra_scripts` 块
- 保持所有块名称不变（`detail_hero_icon`, `detail_content` 等）

**影响：** 7 个详情页面自动受益，无需修改

---

### 步骤2：修改 list_page_base.html

**变更：**
- `{% extends "shared/module_base.html" %}` → `{% extends "shared/base.html" %}`
- 添加 `{% include 'shared/_workspace_resources.html' %}` 到 `extra_css` 块
- 添加 `{% include 'shared/_workspace_scripts.html' %}` 到 `extra_scripts` 块
- 保持所有块名称不变（`list_page_title`, `list_page_table` 等）

**影响：** 6 个列表页面自动受益，无需修改

---

### 步骤3：修改 form_page_base.html

**变更：**
- `{% extends "shared/module_base.html" %}` → `{% extends "shared/base.html" %}`
- 添加 `{% include 'shared/_workspace_resources.html' %}` 到 `extra_css` 块
- 添加 `{% include 'shared/_workspace_scripts.html' %}` 到 `extra_scripts` 块
- 保持所有块名称不变（`form_page_title`, `form_page_content` 等）

**影响：** 5 个表单页面自动受益，无需修改

---

## ✅ 验证清单

修改后验证：

- [ ] detail_page_base.html 继承 base.html
- [ ] list_page_base.html 继承 base.html
- [ ] form_page_base.html 继承 base.html
- [ ] 所有资源（CSS/JS）正确加载
- [ ] 侧边栏功能正常
- [ ] 模态框功能正常
- [ ] 详情页面显示正常（7个页面）
- [ ] 列表页面显示正常（6个页面）
- [ ] 表单页面显示正常（5个页面）

---

## 🎯 预期效果

### 继承链变化

**之前（4层）：**
```
base.html -> module_base.html -> detail_page_base.html -> 具体页面
```

**之后（3层）：**
```
base.html -> detail_page_base.html -> 具体页面
```

### 优势

1. ✅ 继承链深度减少（4层 → 3层）
2. ✅ 子页面无需修改（向后兼容）
3. ✅ 块名称保持不变（无破坏性变更）
4. ✅ 资源通过 include 组合（易于维护）

---

## ⚠️ 注意事项

1. **资源加载顺序**
   - 确保 `_workspace_resources.html` 在 `extra_css` 块中
   - 确保 `_workspace_scripts.html` 在 `extra_scripts` 块中

2. **块覆盖**
   - 保持所有块名称不变
   - 子页面可以继续使用相同的块名称

3. **侧边栏支持**
   - 如果页面需要侧边栏，需要手动添加布局结构
   - 或者通过上下文变量 `module_sidebar_nav` 控制

---

## 📝 实施时间估算

- **步骤1-3（修改基础模板）：** 30-60 分钟
- **测试验证：** 30-60 分钟
- **总计：** 1-2 小时

---

## 🚀 开始实施

准备好后，我们可以立即开始修改这 3 个基础模板。

