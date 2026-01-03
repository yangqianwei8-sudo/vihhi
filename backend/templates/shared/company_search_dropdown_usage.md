# 公司名称搜索下拉组件使用说明

## 概述

`company_search_dropdown_snippet.html` 是一个可复用的共享模板组件，提供企业名称输入框和实时搜索下拉功能。用户输入公司名称（如"四川维海"）后，系统会自动调用启信宝API搜索匹配的企业，并在下拉框中显示供用户选择。

## 主要特性

1. **实时搜索**：输入关键词后自动搜索匹配的企业
2. **智能匹配**：支持模糊搜索，输入部分关键词即可找到相关企业
3. **自动填充**：选择企业后自动填充统一信用代码、法定代表人等信息
4. **易于集成**：简单的模板引入即可使用
5. **高度可配置**：支持自定义字段映射和功能开关

## 使用方法

### 1. 基础用法（最简单）

```django
{% load static %}
{% include "shared/qixinbao_api_config_snippet.html" %}
{% include "shared/company_search_dropdown_snippet.html" with 
    input_id="companyName"
    dropdown_id="companyDropdown"
    credit_code_input_id="creditCode"
    label="公司名称"
    required=True
%}

<script>
document.addEventListener('DOMContentLoaded', function() {
    initCompanySearchDropdown({
        inputId: 'companyName',
        dropdownId: 'companyDropdown',
        creditCodeInputId: 'creditCode'
    });
});
</script>
```

### 2. 完整配置示例

```django
{% include "shared/company_search_dropdown_snippet.html" with 
    input_id="clientName"
    input_name="client_name"
    dropdown_id="clientSearchDropdown"
    credit_code_input_id="clientCreditCode"
    credit_code_input_name="unified_credit_code"
    legal_rep_input_id="legalRep"
    legal_rep_input_name="legal_representative"
    established_date_input_id="establishedDate"
    established_date_input_name="established_date"
    registered_capital_input_id="regCapital"
    registered_capital_input_name="registered_capital"
    label="客户名称"
    placeholder="输入客户名称，如：四川维海科技有限公司"
    required=True
    auto_fill_details=True
    auto_query_execution=False
    min_search_length=2
    search_delay=500
    debug=False
%}
```

### 3. 与其他表单字段配合使用

```django
<form method="post">
    {% csrf_token %}
    
    <!-- 公司名称搜索下拉 -->
    {% include "shared/company_search_dropdown_snippet.html" with 
        input_id="companyName"
        dropdown_id="companyDropdown"
        credit_code_input_id="creditCode"
        label="公司名称"
    %}
    
    <!-- 统一信用代码（会自动填充） -->
    <div class="form-group">
        <label>统一社会信用代码</label>
        <input type="text" id="creditCode" name="unified_credit_code" class="form-control" readonly>
    </div>
    
    <!-- 法定代表人（会自动填充） -->
    <div class="form-group">
        <label>法定代表人</label>
        <input type="text" name="legal_representative" class="form-control">
    </div>
    
    <!-- 其他字段... -->
</form>
```

## 参数说明

### 必需参数

- `input_id` - 输入框ID（字符串）
- `dropdown_id` - 下拉框ID（字符串）

### 可选参数

#### 输入框相关
- `input_name` - 输入框name属性（默认：使用input_id）
- `label` - 标签文本（默认："公司名称"）
- `placeholder` - 占位符文本（默认："输入公司名称，如：四川维海"）
- `required` - 是否必填（默认：False）

#### 字段映射
- `credit_code_input_id` - 统一信用代码输入框ID
- `credit_code_input_name` - 统一信用代码输入框name属性
- `legal_rep_input_id` - 法定代表人输入框ID
- `legal_rep_input_name` - 法定代表人输入框name属性
- `established_date_input_id` - 成立日期输入框ID
- `established_date_input_name` - 成立日期输入框name属性
- `registered_capital_input_id` - 注册资本输入框ID
- `registered_capital_input_name` - 注册资本输入框name属性

#### 功能配置
- `auto_fill_details` - 是否自动填充详细信息（默认：True）
  - 包括：注册资本、联系电话、邮箱、地址等
- `auto_query_execution` - 是否自动查询被执行信息（默认：False）
- `min_search_length` - 最小搜索字符数（默认：2）
- `search_delay` - 搜索延迟时间，毫秒（默认：500）
- `debug` - 是否启用调试模式（默认：False）

## JavaScript初始化

### 基础初始化

```javascript
initCompanySearchDropdown({
    inputId: 'companyName',
    dropdownId: 'companyDropdown',
    creditCodeInputId: 'creditCode'
});
```

### 完整配置初始化

```javascript
initCompanySearchDropdown({
    inputId: 'companyName',
    dropdownId: 'companyDropdown',
    creditCodeInputId: 'creditCode',
    legalRepInputId: 'legalRep',
    establishedDateInputId: 'establishedDate',
    registeredCapitalInputId: 'regCapital',
    autoFillDetails: true,
    autoQueryExecution: false,
    minSearchLength: 2,
    searchDelay: 500,
    debug: false
});
```

### 自动字段发现

如果不提供字段ID，组件会尝试自动查找：

```javascript
// 只指定输入框和下拉框，其他字段自动查找
initCompanySearchDropdown({
    inputId: 'companyName',
    dropdownId: 'companyDropdown'
});
// 会自动查找 name 属性包含以下关键词的输入框：
// - unified_credit_code, credit_code (统一信用代码)
// - legal_representative (法定代表人)
// - established_date, start_date (成立日期)
// - registered_capital, reg_capital (注册资本)
```

## 使用示例

### 示例1：客户表单

```django
{% extends "shared/module_base.html" %}
{% load static %}

{% block extra_css %}
{% include "shared/qixinbao_api_config_snippet.html" with load_js=False %}
{% endblock %}

{% block module_content %}
<form method="post">
    {% csrf_token %}
    
    <div class="form-section">
        <h5>基本信息</h5>
        
        {% include "shared/company_search_dropdown_snippet.html" with 
            input_id="clientName"
            dropdown_id="clientDropdown"
            credit_code_input_id="creditCode"
            label="客户名称"
            required=True
        %}
        
        <div class="form-group">
            <label>统一社会信用代码</label>
            <input type="text" id="creditCode" name="unified_credit_code" class="form-control">
        </div>
        
        <div class="form-group">
            <label>法定代表人</label>
            <input type="text" name="legal_representative" class="form-control">
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary">保存</button>
</form>
{% endblock %}

{% block module_extra_js %}
{% include "shared/qixinbao_api_config_snippet.html" with load_css=False load_js=True %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    initCompanySearchDropdown({
        inputId: 'clientName',
        dropdownId: 'clientDropdown',
        creditCodeInputId: 'creditCode',
        autoFillDetails: true,
        debug: false
    });
});
</script>
{% endblock %}
```

### 示例2：联系人职业信息

```django
<!-- 在联系人表单的职业信息部分 -->
<div class="career-form-item" data-form-index="0">
    <div class="form-group">
        {% include "shared/company_search_dropdown_snippet.html" with 
            input_id="career_company_0"
            dropdown_id="careerDropdown_0"
            credit_code_input_id="career_credit_code_0"
            label="就职公司"
            placeholder="输入公司名称"
            min_search_length=2
        %}
    </div>
    
    <div class="form-group">
        <label>统一信用代码</label>
        <input type="text" id="career_credit_code_0" name="careers-0-unified_credit_code" class="form-control">
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    initCompanySearchDropdown({
        inputId: 'career_company_0',
        dropdownId: 'careerDropdown_0',
        creditCodeInputId: 'career_credit_code_0',
        autoFillDetails: false,  // 职业信息不需要填充详细信息
        debug: false
    });
});
</script>
```

## 搜索结果展示

下拉框中每个企业项显示：

- **企业名称**（粗体显示）
- **统一信用代码**
- **法定代表人**

示例：
```
┌─────────────────────────────────────────┐
│ 四川维海科技有限公司                      │
│ 统一信用代码: 91510000MA6XXX1234         │
│ 法定代表人: 张三                          │
├─────────────────────────────────────────┤
│ 四川维海贸易有限公司                      │
│ 统一信用代码: 91510000MA6XXX5678         │
│ 法定代表人: 李四                          │
└─────────────────────────────────────────┘
```

## 自动填充功能

选择企业后，如果启用了 `autoFillDetails`，会自动填充以下字段：

- ✅ 统一社会信用代码
- ✅ 法定代表人
- ✅ 成立日期
- ✅ 注册资本（自动转换为万元）
- ✅ 联系电话（如果有）
- ✅ 邮箱（如果有）
- ✅ 地址（如果有）

## 注意事项

1. **依赖关系**：使用前必须先引入 `qixinbao_api_config_snippet.html`
2. **加载顺序**：JavaScript初始化代码应该在DOM加载完成后执行
3. **API配置**：确保启信宝API已正确配置
4. **字符数限制**：默认至少需要输入2个字符才会触发搜索
5. **搜索延迟**：默认500ms延迟，避免频繁请求

## 常见问题

### Q: 下拉框不显示怎么办？

A: 检查以下几点：
1. 是否引入了 `qixinbao_api_config_snippet.html`
2. 是否引入了 `qixinbao-autofill.js`
3. 是否正确调用了初始化函数
4. 检查浏览器控制台是否有错误信息

### Q: 搜索没有结果？

A: 可能的原因：
1. 输入的字符数少于最小搜索字符数（默认2个）
2. 启信宝API配置错误或未配置
3. 网络连接问题
4. 企业名称确实不存在

### Q: 如何自定义下拉框样式？

A: 修改 `qixinbao-autofill.css` 文件，或添加自定义CSS覆盖样式。

### Q: 可以选择多个企业吗？

A: 当前版本只支持单选，选择后输入框会被填充。如需多选，需要自定义实现。

## 版本历史

- **v1.0.0** (2024-12-XX)
  - 初始版本
  - 支持企业名称搜索和自动填充

