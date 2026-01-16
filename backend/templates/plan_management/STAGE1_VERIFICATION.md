# Stage 1 验收清单

## ✅ 必须检查的 5 个点

### 1. 页面上旧侧栏是否彻底不可见
- [ ] 打开计划管理任意页面（如 home.html）
- [ ] 检查左侧：不应看到 `.sidenav` 相关的菜单
- [ ] 不应看到 emoji 图标 + `href="#"` 的旧菜单样式
- [ ] 在浏览器开发者工具中检查：`document.querySelectorAll('.sidenav').length` 可能 >0（DOM 还在，但应不可见）

### 2. 新侧栏是否完全正常
- [ ] `.vh-sb` 必须可见
- [ ] 菜单项可点击
- [ ] Active 高亮正确（当前页面菜单项高亮）
- [ ] 子菜单展开/收起功能正常
- [ ] 检查：`document.querySelectorAll('.vh-sb').length` 必须 = 1

### 3. HTML 源码里是否仍渲染旧侧栏（允许，但要知道事实）
- [ ] 打开页面源码（Ctrl+U）
- [ ] 搜索 `class="sidenav"` 或 `class="workspace-nav"`
- [ ] 如果存在：这是正常的（Stage 1 只是隐藏，Stage 2 才清除 DOM）
- [ ] 记录：是否仍存在旧侧栏 DOM

### 4. 双 aside 挤压是否消失
- [ ] 检查页面主体宽度是否正常
- [ ] 不应出现左侧空白带（旧侧栏占位）
- [ ] 滚动条正常
- [ ] 布局不应异常收窄

### 5. 兼容性回退是否生效（可选）
- [ ] 在不支持 `:has()` 的浏览器中测试（如旧版 Firefox）
- [ ] 旧侧栏仍应消失
- [ ] 新侧栏仍应显示

## ⚠️ 已知问题

### 问题1：部分模板仍使用旧的 `base.html`
以下模板仍在使用 `base.html`（包含旧侧边栏）：
- plan_complete.html
- plan_decompose.html
- plan_decompose_entry.html
- plan_execution_track.html

**影响**：这些页面可能仍显示旧侧边栏（即使有 CSS 屏蔽）

**解决方案**：Stage 2 需要将这些模板改为使用 `_base.html`

## 📝 验证结果记录

- [ ] Stage 1 验证通过
- [ ] 发现问题：_____________
- [ ] 准备进入 Stage 2：是/否
