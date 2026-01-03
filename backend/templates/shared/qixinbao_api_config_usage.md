# 启信宝API配置共享模板使用说明

## 概述

`qixinbao_api_config_snippet.html` 是一个共享模板文件，提供了统一的启信宝API配置管理，避免了在多个页面中硬编码API路径的问题。

## 主要特性

1. **统一配置管理**：所有启信宝API URL集中管理
2. **使用Django URL Reverse**：避免硬编码，URL变更只需修改urls.py
3. **全局配置对象**：提供`window.QIXINBAO_API`全局对象
4. **便捷函数**：提供常用的辅助函数
5. **向后兼容**：支持逐步迁移现有代码

## 使用方法

### 1. 基础用法（推荐）

在页面头部引入（加载CSS和JS）：

```django
{% load static %}
{% include "shared/qixinbao_api_config_snippet.html" %}
```

在页面底部使用：

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 使用便捷函数初始化
    const autofill = initQixinbaoAutofill({
        nameInputSelector: '[name="name"]',
        creditCodeInputSelector: '[name="unified_credit_code"]',
        dropdownId: 'companyDropdown'
    });
});
</script>
```

### 2. 只加载配置（不加载CSS/JS）

```django
{% include "shared/qixinbao_api_config_snippet.html" with load_css=False load_js=False %}
```

### 3. 使用全局配置对象

```javascript
// 方式1：使用全局配置对象
const searchUrl = QIXINBAO_API.urls.searchCompany;
const detailUrl = QIXINBAO_API.urls.getCompanyDetail;

// 方式2：使用辅助函数构建URL
const searchUrl = QIXINBAO_API.getUrl('searchCompany', {
    keyword: '维海科技',
    match_type: 'ename'
});

// 方式3：在QixinbaoAutofill中使用
const autofill = new QixinbaoAutofill({
    searchApiUrl: QIXINBAO_API.urls.searchCompany,
    detailApiUrl: QIXINBAO_API.urls.getCompanyDetail,
    executionApiUrl: QIXINBAO_API.urls.getExecutionRecords
});
```

## API配置对象结构

```javascript
window.QIXINBAO_API = {
    urls: {
        searchCompany: '/api/customer/search-company/',
        getCompanyDetail: '/api/customer/get-company-detail/',
        getCompanyInfoByName: '/api/customer/get-company-info-by-name/',
        getLegalRisk: '/api/customer/get-legal-risk/',
        getExecutionRecords: '/api/customer/get-execution-records/',
        syncExecutionRecords: '/api/customer/sync-execution-records/',
        verifyCreditCode: '/api/customer/verify-credit-code/'
    },
    config: {
        namespace: 'QIXINBAO_API',
        version: '1.0.0',
        debug: false,
        defaultTimeout: 10000,
        defaultSearchDelay: 500,
        minSearchLength: 2
    },
    getUrl: function(endpoint, params) { /* ... */ },
    validate: function() { /* ... */ }
}
```

## 便捷函数

### 1. initQixinbaoAutofill(options)

初始化启信宝自动填充组件，自动使用全局API配置。

**参数：**
- `options.nameInputSelector` - 企业名称输入框选择器（必需）
- `options.creditCodeInputSelector` - 统一信用代码输入框选择器（必需）
- `options.dropdownId` - 下拉框ID（必需）
- `options.fieldSelectors` - 其他字段选择器（可选）
- `options.autoFillDetails` - 是否自动填充详细信息（可选，默认：true）
- `options.autoQueryExecution` - 是否自动查询被执行信息（可选，默认：true）
- `options.debug` - 是否启用调试模式（可选，默认：false）

**返回值：** QixinbaoAutofill实例或null

**示例：**
```javascript
const autofill = initQixinbaoAutofill({
    nameInputSelector: '[name="name"]',
    creditCodeInputSelector: '[name="unified_credit_code"]',
    dropdownId: 'companyDropdown',
    debug: true
});
```

### 2. fetchQixinbaoLegalRisk(params, callback)

获取法律风险信息。

**参数：**
- `params.company_id` - 企业ID（可选）
- `params.credit_code` - 统一社会信用代码（可选）
- `params.company_name` - 企业名称（可选）
- `callback` - 回调函数，参数为(data, error)

**示例：**
```javascript
fetchQixinbaoLegalRisk({
    credit_code: '91110000MA01234567',
    company_name: '北京维海科技有限公司'
}, function(data, error) {
    if (error) {
        console.error('获取失败:', error);
        return;
    }
    if (data.success) {
        console.log('法律风险信息:', data.data);
    }
});
```

### 3. verifyQixinbaoCreditCode(creditCode, companyName, callback)

验证统一社会信用代码。

**参数：**
- `creditCode` - 统一社会信用代码（必需）
- `companyName` - 公司名称（可选）
- `callback` - 回调函数，参数为(data, error)

**示例：**
```javascript
verifyQixinbaoCreditCode('91110000MA01234567', '北京维海科技有限公司', function(data, error) {
    if (error) {
        console.error('验证失败:', error);
        return;
    }
    if (data.valid) {
        console.log('验证通过:', data);
    } else {
        console.warn('验证失败:', data.message);
    }
});
```

## 完整示例

### 示例1：客户表单页面

```django
{% extends "shared/module_base.html" %}
{% load static %}

{% block extra_css %}
{% include "shared/qixinbao_api_config_snippet.html" with load_js=False %}
{% endblock %}

{% block module_content %}
<!-- 表单内容 -->
<div class="form-group">
    <label>客户名称</label>
    <input type="text" name="name" id="nameInput">
    <div id="companyDropdown" class="autocomplete-dropdown"></div>
</div>
<div class="form-group">
    <label>统一信用代码</label>
    <input type="text" name="unified_credit_code" id="creditCodeInput">
</div>
{% endblock %}

{% block module_extra_js %}
{% include "shared/qixinbao_api_config_snippet.html" with load_css=False load_js=True %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 初始化启信宝自动填充
    const autofill = initQixinbaoAutofill({
        nameInputSelector: '#nameInput',
        creditCodeInputSelector: '#creditCodeInput',
        dropdownId: 'companyDropdown',
        debug: true
    });
    
    if (!autofill) {
        console.error('启信宝自动填充初始化失败');
    }
});
</script>
{% endblock %}
```

### 示例2：直接使用API

```javascript
// 企业搜索
fetch(QIXINBAO_API.getUrl('searchCompany', {
    keyword: '维海科技',
    match_type: 'ename'
}), {
    method: 'GET',
    headers: {
        'Accept': 'application/json'
    },
    credentials: 'same-origin'
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('搜索结果:', data.data.items);
    }
});

// 获取法律风险信息
fetchQixinbaoLegalRisk({
    company_name: '北京维海科技有限公司'
}, function(data, error) {
    if (error) {
        console.error('获取失败:', error);
        return;
    }
    console.log('法律风险:', data.data);
});
```

## 迁移现有代码

### 步骤1：在页面中引入共享模板

```django
{% include "shared/qixinbao_api_config_snippet.html" %}
```

### 步骤2：替换硬编码的URL

**之前：**
```javascript
const url = `/api/customer/search-company/?keyword=${keyword}`;
```

**之后：**
```javascript
const url = QIXINBAO_API.getUrl('searchCompany', { keyword: keyword });
// 或
const url = QIXINBAO_API.urls.searchCompany + '?keyword=' + encodeURIComponent(keyword);
```

### 步骤3：使用便捷函数（可选）

**之前：**
```javascript
const autofill = new QixinbaoAutofill({
    searchApiUrl: '/api/customer/search-company/',
    detailApiUrl: '/api/customer/get-company-detail/',
    // ...
});
```

**之后：**
```javascript
const autofill = initQixinbaoAutofill({
    nameInputSelector: '[name="name"]',
    creditCodeInputSelector: '[name="unified_credit_code"]',
    dropdownId: 'companyDropdown'
    // API URL会自动使用全局配置
});
```

## 调试模式

启用调试模式可以看到详细的日志信息：

```javascript
// 全局启用
QIXINBAO_API.config.debug = true;

// 或在初始化时启用
const autofill = initQixinbaoAutofill({
    // ...
    debug: true
});
```

## 注意事项

1. **URL依赖**：确保`urls.py`中已正确定义所有API路由
2. **加载顺序**：如果使用便捷函数，确保在DOM加载完成后再调用
3. **向后兼容**：现有的硬编码URL代码仍然可以工作，可以逐步迁移
4. **命名空间**：可以通过`config_namespace`参数自定义命名空间名称

## 常见问题

### Q: 如果URL配置失败怎么办？

A: 配置对象会尝试验证，如果URL中包含'None'字符串，会在控制台输出警告。确保urls.py中已正确定义路由名称。

### Q: 可以在同一个页面多次引入吗？

A: 可以，但建议只引入一次。多次引入不会覆盖已有的配置对象。

### Q: 如何自定义配置？

A: 可以在引入模板后修改配置对象：
```javascript
QIXINBAO_API.config.debug = true;
QIXINBAO_API.config.defaultTimeout = 15000;
```

## 版本历史

- **v1.0.0** (2024-12-XX)
  - 初始版本
  - 提供基础API配置和便捷函数

