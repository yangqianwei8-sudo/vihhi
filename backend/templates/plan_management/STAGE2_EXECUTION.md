# Stage 2 执行清单：断开旧侧边栏引用

## 🎯 目标
彻底移除旧侧边栏的 DOM 渲染，只保留新侧边栏 `.vh-sb`

## ⚠️ 边界（绝不触碰）
- ✅ 只删旧 include / 旧 aside 输出
- ✅ 新侧边栏输出点保持不变（`.vh-sb` 的 include 不动）
- ❌ 不改菜单数据源（`plan_menu` / `module_sidebar_nav`）
- ❌ 不动业务 view
- ❌ 不做"统一 layout 重构"

## 📋 执行清单

### 1. 更新仍使用旧 `base.html` 的模板

以下模板需要改为使用 `_base.html`：

- [ ] `plan_complete.html` - 改为 `{% extends "plan_management/_base.html" %}`
- [ ] `plan_decompose.html` - 改为 `{% extends "plan_management/_base.html" %}`
- [ ] `plan_decompose_entry.html` - 改为 `{% extends "plan_management/_base.html" %}`
- [ ] `plan_execution_track.html` - 改为 `{% extends "plan_management/_base.html" %}`

**注意**：检查这些模板的 block 名称是否与 `_base.html` 匹配（`pm_title`, `pm_subtitle`, `pm_content`）

### 2. 检查并清理 `base.html`（可选）

如果所有模板都已迁移到 `_base.html`，可以考虑：
- [ ] 备份 `base.html` 为 `base.html.legacy`
- [ ] 或直接删除（如果确认不再使用）

### 3. 全局搜索其他可能的旧侧边栏引用

- [ ] 搜索 `shared/sidebar_nav.html` 的引用
- [ ] 搜索 `.workspace-nav` 的直接输出
- [ ] 搜索 `.sidenav` 的直接输出

### 4. 验证 Stage 2 完成

执行以下检查：
```js
// 在浏览器 Console 中执行
document.querySelectorAll('.sidenav').length  // 必须 = 0
document.querySelectorAll('.workspace-nav').length  // 必须 = 0（或只包含新侧栏的容器）
document.querySelectorAll('.vh-sb').length  // 必须 = 1
```

## ✅ 完成标准

- [ ] 所有计划管理页面都使用 `_base.html`
- [ ] HTML 源码中不再出现 `.sidenav` 或 `.workspace-nav`（除非包含 `.vh-sb`）
- [ ] 新侧边栏在所有页面正常显示
- [ ] 页面布局正常，无挤压
