# 模板代码暴露问题修复指南

## 🔍 问题描述

代码暴露在列表页面上，通常表现为：
- JavaScript代码直接显示在HTML中
- CSS代码直接显示在HTML中
- Django模板标签（如 `{% if %}`, `{{ variable }}`）显示在页面上
- HTML标签（如 `<script>`, `<style>`）显示为文本

## ⚠️ 常见原因

### 1. `<script>` 标签未正确闭合

**问题：**
```html
<script>
    // JavaScript代码
    // ... 缺少 </script>
```

**影响：** 所有后续内容（包括HTML）都会被当作JavaScript代码，导致页面显示异常。

**解决方法：** 确保每个 `<script>` 都有对应的 `</script>` 关闭标签。

### 2. `<style>` 标签未正确闭合

**问题：**
```html
<style>
    /* CSS代码 */
    /* ... 缺少 </style> */
```

**影响：** CSS代码会显示在页面上。

**解决方法：** 确保每个 `<style>` 都有对应的 `</style>` 关闭标签。

### 3. Django模板标签未正确闭合

**问题：**
```django
{% if condition %}
    <!-- 内容 -->
<!-- 缺少 {% endif %} -->
```

**影响：** 模板标签会显示在页面上，页面可能无法正常渲染。

**解决方法：** 确保所有模板标签都正确配对：
- `{% if %}` ... `{% endif %}`
- `{% for %}` ... `{% endfor %}`
- `{% block %}` ... `{% endblock %}`
- `{% comment %}` ... `{% endcomment %}`

### 4. HTML实体编码问题

**问题：**
```html
<!-- 在HTML内容中直接使用 < 和 > -->
<p>使用 <script> 标签时要注意</p>
```

**影响：** 浏览器会尝试解析这些标签，导致显示异常。

**解决方法：** 使用HTML实体编码：
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`

或者在Django模板中使用 `|safe` filter时要小心。

### 5. 模板继承问题

**问题：**
```django
<!-- 子模板 -->
{% block wrong_block_name %}
    <!-- 内容 -->
{% endblock %}
```

**影响：** block内容可能无法正确插入，导致代码暴露。

**解决方法：** 确保block名称匹配，extends路径正确。

## 🔧 检查方法

### 方法1：使用浏览器开发者工具

1. 打开页面，按 `F12` 打开开发者工具
2. 查看 **Console** 标签，检查是否有JavaScript错误
3. 查看 **Elements** 标签，检查HTML结构是否正确
4. 查看页面源代码（右键 → 查看页面源代码），检查是否有未闭合的标签

### 方法2：使用Python脚本检查

```python
import re

def check_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查script标签
    script_open = len(re.findall(r'<script(?![^>]*>.*</script>)', content, re.IGNORECASE))
    script_close = len(re.findall(r'</script>', content, re.IGNORECASE))
    
    # 检查style标签
    style_open = len(re.findall(r'<style(?![^>]*>.*</style>)', content, re.IGNORECASE))
    style_close = len(re.findall(r'</style>', content, re.IGNORECASE))
    
    # 检查Django模板标签
    if_count = len(re.findall(r'{%\s*if\s+', content))
    endif_count = len(re.findall(r'{%\s*endif\s*%}', content))
    
    issues = []
    if script_open != script_close:
        issues.append(f'script标签不匹配: {script_open} 打开, {script_close} 关闭')
    if style_open != style_close:
        issues.append(f'style标签不匹配: {style_open} 打开, {style_close} 关闭')
    if if_count != endif_count:
        issues.append(f'if/endif不匹配: {if_count} if, {endif_count} endif')
    
    return issues
```

### 方法3：使用Django模板语法检查

```bash
# 在Django项目中运行
python manage.py check --deploy
```

## ✅ 修复步骤

### 步骤1：定位问题

1. 查看浏览器控制台错误信息
2. 查看页面源代码，找到显示代码的位置
3. 检查对应的模板文件

### 步骤2：修复问题

1. **修复未闭合的标签**
   - 添加缺失的关闭标签
   - 确保标签正确配对

2. **修复模板语法错误**
   - 检查Django模板标签是否正确配对
   - 检查block名称是否匹配

3. **修复HTML实体编码**
   - 在需要显示 `<`, `>`, `&` 的地方使用实体编码
   - 或者在模板中使用 `|escape` filter

### 步骤3：验证修复

1. 刷新页面，检查代码是否还显示
2. 检查浏览器控制台，确认没有错误
3. 检查页面功能是否正常

## 🛡️ 预防措施

### 1. 使用代码编辑器

- 使用支持HTML/Django模板语法的编辑器（如VS Code、PyCharm）
- 安装语法检查插件
- 启用标签自动闭合功能

### 2. 代码审查

- 在提交代码前检查所有标签是否正确闭合
- 使用自动化工具检查模板语法
- 进行代码审查

### 3. 测试

- 在开发环境测试所有页面
- 检查浏览器控制台是否有错误
- 使用自动化测试工具

### 4. 使用模板lint工具

```bash
# 安装django-extensions（如果还没有）
pip install django-extensions

# 使用validate_templates管理命令
python manage.py validate_templates
```

## 📝 最佳实践

1. **总是闭合标签**
   - 每打开一个标签，立即添加对应的关闭标签
   - 使用编辑器的标签配对功能

2. **使用注释标记**
   - 在复杂的模板结构中添加注释
   - 标记block的开始和结束

3. **保持模板简洁**
   - 避免过深的嵌套
   - 将复杂逻辑移到视图或模板标签中

4. **使用模板片段**
   - 将重复的代码提取为模板片段
   - 使用 `{% include %}` 复用代码

5. **测试所有页面**
   - 定期检查所有模板页面
   - 确保没有代码暴露问题

## 🔗 相关文档

- [Django模板语言文档](https://docs.djangoproject.com/en/stable/topics/templates/)
- [HTML标签参考](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element)
- [模板代码规范](./FORM_CARD_ALIGNMENT_GUIDE.md)

---

**最后更新：** 2024年
**维护者：** 开发团队

