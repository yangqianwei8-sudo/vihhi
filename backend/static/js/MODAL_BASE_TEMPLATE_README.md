# 通用模态框基础模板使用指南

## 概述

我们创建了一个通用的模态框基础模板系统，自动集成ModalManager，避免遮罩层问题。

## 文件说明

### 1. **base_modal.html** - 基础模态框模板
提供标准化的模态框结构，自动集成ModalManager。

### 2. **modal-helpers.js** - JavaScript辅助函数
提供统一的模态框打开/关闭方法。

## 使用方法

### 方法一：使用基础模板创建新模态框

```django
{% include "shared/modals/base_modal.html" with 
    modal_id="myModal" 
    modal_title="我的模态框" 
    modal_size="lg"
    modal_centered=True
%}

{% block modal_body_content %}
<!-- 在这里放置模态框主体内容 -->
<div class="mb-3">
    <label class="form-label">输入框</label>
    <input type="text" class="form-control" id="myInput">
</div>
{% endblock %}

{% block modal_footer_content %}
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
<button type="button" class="btn btn-primary" onclick="saveData()">保存</button>
{% endblock %}
```

### 方法二：使用JavaScript辅助函数

```javascript
// 打开模态框
openModal('myModal');

// 关闭模态框
closeModal('myModal');

// 切换模态框显示状态
toggleModal('myModal');

// 获取模态框实例
const instance = getModalInstance('myModal');

// 检查模态框是否可见
if (isModalVisible('myModal')) {
    console.log('模态框已显示');
}

// 等待模态框显示完成
await waitForModalShown('myModal');

// 等待模态框隐藏完成
await waitForModalHidden('myModal');
```

### 方法三：使用ModalHelpers对象

```javascript
// 使用对象方法
ModalHelpers.open('myModal');
ModalHelpers.close('myModal');
ModalHelpers.toggle('myModal');
ModalHelpers.getInstance('myModal');
ModalHelpers.isVisible('myModal');
ModalHelpers.waitForShown('myModal');
ModalHelpers.waitForHidden('myModal');
```

## 基础模板参数

### 必需参数
- `modal_id`: 模态框的唯一ID
- `modal_title`: 模态框标题

### 可选参数
- `modal_title_icon`: 标题图标类（如 "bi-envelope"）
- `modal_size`: 模态框尺寸（sm, md, lg, xl，默认：md）
- `modal_centered`: 是否垂直居中（默认：True）
- `modal_scrollable`: 是否可滚动（默认：False）
- `modal_backdrop`: 是否显示遮罩层（默认：True）
- `modal_keyboard`: 是否允许ESC键关闭（默认：True）
- `modal_focus`: 是否自动聚焦（默认：True）
- `show_close_button`: 是否显示关闭按钮（默认：True）
- `close_button_text`: 关闭按钮文本（默认："关闭"）

## 可覆盖的模板块

### modal_body_content
模态框主体内容

```django
{% block modal_body_content %}
<!-- 你的内容 -->
{% endblock %}
```

### modal_footer_content
模态框底部内容（默认包含关闭按钮）

```django
{% block modal_footer_content %}
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
<button type="button" class="btn btn-primary">确认</button>
{% endblock %}
```

### modal_extra_attributes
额外的模态框属性

```django
{% block modal_extra_attributes %}
data-custom-attr="value"
{% endblock %}
```

## 已更新的模态框模板

以下模态框已更新为使用基础模板：

1. **confirm_action_modal.html** - 确认操作模态框
2. **email_config_modal.html** - 邮件配置模态框
3. **batch_action_modal.html** - 批量操作模态框
4. **batch_import_modal.html** - 批量导入模态框

## 优势

1. **自动集成ModalManager** - 所有模态框自动使用ModalManager，避免遮罩层问题
2. **统一的代码风格** - 所有模态框使用相同的结构和API
3. **易于维护** - 修改基础模板即可影响所有模态框
4. **向后兼容** - 支持降级到Bootstrap原生API
5. **类型安全** - 提供完整的参数说明和错误处理

## 迁移指南

### 从旧模态框迁移到新模板

1. **替换模态框HTML结构**
```django
<!-- 旧方式 -->
<div class="modal fade" id="myModal">
    <!-- ... -->
</div>

<!-- 新方式 -->
{% include "shared/modals/base_modal.html" with modal_id="myModal" modal_title="标题" %}
{% block modal_body_content %}...{% endblock %}
```

2. **更新JavaScript代码**
```javascript
// 旧方式
const modal = new bootstrap.Modal(document.getElementById('myModal'));
modal.show();

// 新方式
openModal('myModal');
```

3. **测试功能**
确保所有功能正常工作，特别是：
- 遮罩层显示正常
- 模态框可以正常打开/关闭
- z-index正确
- 没有多余的backdrop

## 注意事项

1. **确保引入脚本** - 确保`modal-manager.js`和`modal-helpers.js`已正确引入
2. **模态框ID唯一** - 确保每个模态框都有唯一的ID
3. **使用辅助函数** - 尽量使用`openModal()`和`closeModal()`而不是直接操作Bootstrap API
4. **测试兼容性** - 在多个浏览器中测试模态框功能

## 示例

### 完整示例

```django
{% include "shared/modals/base_modal.html" with 
    modal_id="createUserModal" 
    modal_title="创建用户" 
    modal_title_icon="bi-person-plus"
    modal_size="lg"
    modal_centered=True
%}

{% block modal_body_content %}
<form id="createUserForm">
    <div class="mb-3">
        <label class="form-label">用户名</label>
        <input type="text" class="form-control" name="username" required>
    </div>
    <div class="mb-3">
        <label class="form-label">邮箱</label>
        <input type="email" class="form-control" name="email" required>
    </div>
</form>
{% endblock %}

{% block modal_footer_content %}
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
<button type="button" class="btn btn-primary" onclick="submitForm()">创建</button>
{% endblock %}
```

```javascript
// 打开模态框
function showCreateUserModal() {
    openModal('createUserModal');
}

// 提交表单
function submitForm() {
    const form = document.getElementById('createUserForm');
    // 处理表单提交
    // ...
    // 关闭模态框
    closeModal('createUserModal');
}
```

## 故障排除

### 模态框没有遮罩层
- 检查`modal-manager.js`是否已加载
- 检查是否使用了`openModal()`函数
- 检查浏览器控制台是否有错误

### 模态框无法打开
- 检查模态框ID是否正确
- 检查是否在DOM加载完成后调用
- 检查是否有JavaScript错误

### z-index问题
- ModalManager会自动处理z-index
- 如果仍有问题，检查是否有自定义CSS覆盖

## 更多信息

- ModalManager文档：`MODAL_MANAGER_README.md`
- 基础模板源码：`templates/shared/modals/base_modal.html`
- 辅助函数源码：`static/js/modal-helpers.js`

