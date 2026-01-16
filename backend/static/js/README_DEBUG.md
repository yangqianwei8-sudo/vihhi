# 合同表单排查工具使用说明

## 方法一：在浏览器控制台直接运行（推荐）

### 步骤：

1. **打开合同表单页面**
   - 访问合同创建或编辑页面

2. **打开浏览器开发者工具**
   - 按 `F12` 或 `Ctrl+Shift+I` (Windows/Linux)
   - 或 `Cmd+Option+I` (Mac)

3. **切换到 Console 标签**

4. **运行排查脚本**
   - 方法 A：直接加载脚本文件
     ```javascript
     // 在控制台输入：
     const script = document.createElement('script');
     script.src = '/static/js/debug-contract-form-simple.js';
     document.head.appendChild(script);
     ```
   
   - 方法 B：复制完整脚本内容
     - 打开文件：`/static/js/debug-contract-form-simple.js`
     - 复制全部内容
     - 粘贴到控制台并回车执行

5. **查看排查结果**
   - 控制台会输出详细的排查信息
   - 包括：✅ 正常项、❌ 错误项、⚠️ 警告项

## 方法二：使用完整版排查脚本

### 加载完整版脚本：

```javascript
// 在控制台输入：
const script = document.createElement('script');
script.src = '/static/js/debug-contract-form.js';
document.head.appendChild(script);
```

完整版脚本会进行更详细的检查，包括：
- DOM 元素检查
- JavaScript 变量检查
- 事件绑定检查
- CSS 样式检查
- JavaScript 错误检查
- 页面加载状态检查
- 表单数据检查
- 添加行功能测试

## 排查内容说明

### 1. DOM 元素检查
检查以下关键元素是否存在：
- `contract-form`: 表单容器
- `parties-container`: 签约主体容器
- `payment-info-container`: 回款信息容器
- `service-contents-container`: 服务内容容器
- `fixed-total-container`: 总价包干容器
- `fixed-unit-container`: 包干单价容器
- 以及各种添加行按钮

### 2. JavaScript 变量检查
检查以下变量是否正确定义：
- `serviceTypeOptions`: 服务类型选项
- `ourUnits`: 我方单位列表
- 各种添加行函数

### 3. 事件绑定检查
检查按钮是否绑定了点击事件

### 4. CSS 样式检查
检查表单是否被隐藏或无法交互：
- `display: none`
- `visibility: hidden`
- `pointer-events: none`
- `z-index` 过低

### 5. JavaScript 错误检查
检查是否有未定义的函数或变量

### 6. 页面加载状态
检查页面是否完全加载

## 常见问题及解决方案

### 问题 1: 元素不存在
**错误信息**: `❌ XXX容器: 不存在`

**可能原因**:
- HTML 模板未正确渲染
- JavaScript 错误导致页面未完全加载
- 元素 ID 不匹配

**解决方案**:
1. 检查浏览器 Network 面板，确认 HTML 已加载
2. 检查控制台是否有 JavaScript 错误
3. 检查模板文件中的元素 ID 是否正确

### 问题 2: 变量未定义
**错误信息**: `❌ serviceTypeOptions: 未定义`

**可能原因**:
- JavaScript 文件未加载
- 变量作用域问题
- DOMContentLoaded 事件未触发

**解决方案**:
1. 检查 Network 面板，确认 JS 文件已加载
2. 检查变量是否在正确的作用域内定义
3. 检查 DOMContentLoaded 事件是否正确触发

### 问题 3: 按钮未绑定事件
**警告信息**: `⚠️ XXX按钮: 无事件`

**可能原因**:
- 事件绑定代码未执行
- 按钮在事件绑定后才创建
- DOMContentLoaded 事件未触发

**解决方案**:
1. 检查事件绑定代码是否在 DOMContentLoaded 内
2. 检查按钮是否在事件绑定代码执行前已存在
3. 手动触发按钮点击测试

### 问题 4: 表单无法交互
**错误信息**: `❌ pointer-events: none`

**可能原因**:
- CSS 样式问题
- 元素被其他元素遮挡

**解决方案**:
1. 检查 CSS 文件中的样式规则
2. 检查是否有其他元素覆盖了表单
3. 检查 z-index 设置

## 快速测试命令

在控制台运行以下命令进行快速测试：

```javascript
// 测试总价包干按钮
const btn = document.getElementById('add-fixed-total-btn');
if (btn) {
    console.log('按钮存在');
    btn.click(); // 尝试点击
} else {
    console.error('按钮不存在');
}

// 检查 serviceTypeOptions
console.log('serviceTypeOptions:', typeof serviceTypeOptions !== 'undefined' ? serviceTypeOptions : '未定义');

// 检查表单样式
const form = document.getElementById('contract-form');
if (form) {
    const styles = window.getComputedStyle(form);
    console.table({
        display: styles.display,
        visibility: styles.visibility,
        pointerEvents: styles.pointerEvents,
        zIndex: styles.zIndex
    });
}
```

## 输出结果说明

- ✅ **绿色对勾**: 检查通过，正常
- ❌ **红色叉号**: 发现错误，需要修复
- ⚠️ **黄色警告**: 发现警告，可能有问题

## 注意事项

1. **运行时机**: 建议在页面完全加载后运行排查脚本
2. **浏览器兼容性**: 脚本使用现代 JavaScript 语法，需要支持 ES6+
3. **控制台输出**: 所有结果都会输出到浏览器控制台
4. **不影响功能**: 排查脚本只读不写，不会影响表单的正常功能

## 反馈问题

如果排查脚本发现问题，请：
1. 截图控制台的完整输出
2. 记录具体的错误信息
3. 说明问题发生的步骤
4. 提供浏览器版本信息

