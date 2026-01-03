# 统一模态框管理器 (Modal Manager)

## 概述

`modal-manager.js` 是一个统一的模态框管理工具，一次性解决了所有模态框遮罩层问题。

## 解决的问题

### 1. 多个遮罩层（backdrop）被重复创建
- **问题**：Bootstrap自动创建backdrop + 手动创建backdrop导致叠加
- **解决**：自动检测并清理多余的backdrop，确保backdrop数量与可见模态框数量一致

### 2. z-index层级冲突
- **问题**：自定义CSS覆盖了Bootstrap的z-index，导致遮罩层在模态框之上
- **解决**：统一设置z-index值（modal: 1055, backdrop: 1050），使用`!important`确保优先级

### 3. DOM结构问题
- **问题**：模态框被放在容器div内部而不是body下
- **解决**：自动检测并将模态框移动到body下

### 4. 模态框实例管理混乱
- **问题**：每次打开都创建新实例，没有复用
- **解决**：使用`getOrCreateInstance()`统一管理，复用实例

### 5. 事件绑定冲突
- **问题**：多次绑定事件监听器，导致重复执行
- **解决**：使用Set记录已绑定的模态框，确保每个模态框只绑定一次

## 使用方法

### 基本使用

```javascript
// 显示模态框
ModalManager.show('modalId');

// 隐藏模态框
ModalManager.hide('modalId');

// 获取或创建实例
const instance = ModalManager.getOrCreateInstance('modalId');
```

### 在模板中使用

```javascript
// 打开模态框
document.getElementById('openModalBtn').addEventListener('click', function() {
    ModalManager.show('myModal');
});

// 关闭模态框
document.getElementById('closeModalBtn').addEventListener('click', function() {
    ModalManager.hide('myModal');
});
```

### 与Bootstrap原生API兼容

如果ModalManager未加载，代码会自动降级到Bootstrap原生API：

```javascript
if (typeof window.ModalManager !== 'undefined') {
    window.ModalManager.show('modalId');
} else if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modalId'));
    modal.show();
}
```

## API 参考

### ModalManager.show(modalId)
显示指定的模态框。

**参数：**
- `modalId` (string): 模态框的ID

**示例：**
```javascript
ModalManager.show('columnSettingsModal');
```

### ModalManager.hide(modalId)
隐藏指定的模态框。

**参数：**
- `modalId` (string): 模态框的ID

**示例：**
```javascript
ModalManager.hide('columnSettingsModal');
```

### ModalManager.getOrCreateInstance(modalId)
获取或创建模态框实例。

**参数：**
- `modalId` (string): 模态框的ID

**返回值：**
- Bootstrap Modal实例

**示例：**
```javascript
const instance = ModalManager.getOrCreateInstance('myModal');
instance.show();
```

### ModalManager.cleanupBackdrops()
手动清理多余的backdrop（通常不需要手动调用）。

### ModalManager.ensureModalZIndex(modalElement)
确保模态框的z-index正确（通常不需要手动调用）。

## 自动功能

ModalManager会自动执行以下操作：

1. **初始化所有模态框**：页面加载时自动初始化所有`.modal`元素
2. **监听新模态框**：使用MutationObserver监听新添加的模态框并自动初始化
3. **清理多余backdrop**：自动检测并清理多余的backdrop
4. **确保z-index正确**：自动设置正确的z-index值
5. **确保DOM结构正确**：自动将模态框移动到body下

## 集成说明

### 在module_base.html中引入

```django
{% block extra_scripts %}
<script src="{% static 'js/modal-manager.js' %}"></script>
{% endblock %}
```

### 替换旧的修复脚本

已替换以下旧脚本：
- `modal-quick-fix.js`
- `modal-button-fix.js`
- `modal-zindex-fix-global.js`

新的`modal-manager.js`包含了所有这些功能，并且更加统一和可靠。

## 注意事项

1. **确保Bootstrap已加载**：ModalManager依赖Bootstrap 5，确保在引入ModalManager之前已加载Bootstrap
2. **模态框必须有ID**：ModalManager通过ID来管理模态框，确保每个模态框都有唯一的ID
3. **自动初始化**：页面加载时ModalManager会自动初始化，无需手动调用

## 调试

ModalManager会在控制台输出调试信息：

```
[ModalManager] 模态框管理器已初始化
[ModalManager] 初始化 3 个模态框
[ModalManager] 创建模态框实例: columnSettingsModal
[ModalManager] 已为模态框绑定事件: columnSettingsModal
```

如果遇到问题，可以查看控制台日志来诊断。

## 兼容性

- Bootstrap 5.x
- 现代浏览器（Chrome, Firefox, Safari, Edge）
- 支持降级到Bootstrap原生API（如果ModalManager未加载）

