/**
 * 合同表单排查脚本
 * 在浏览器控制台运行此脚本，检查表单初始化问题
 * 使用方法：复制整个脚本到浏览器控制台并执行
 */

(function() {
    'use strict';
    
    console.log('╔════════════════════════════════════════════════════════════════════╗');
    console.log('║         合同表单排查工具 - 错误日志输出                        ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝');
    console.log('');
    
    const errors = [];
    const warnings = [];
    const info = [];
    
    // ========== 1. 检查 DOM 元素 ==========
    console.log('📋 [1/8] 检查关键 DOM 元素...');
    const criticalElements = {
        '表单容器': document.getElementById('contract-form'),
        '签约主体容器': document.getElementById('parties-container'),
        '回款信息容器': document.getElementById('payment-info-container'),
        '服务内容容器': document.getElementById('service-contents-container'),
        '总价包干容器': document.getElementById('fixed-total-container'),
        '包干单价容器': document.getElementById('fixed-unit-container'),
        '累计提成容器': document.getElementById('cumulative-commission-container'),
        '分段提成容器': document.getElementById('segmented-commission-container'),
        '跳点提成容器': document.getElementById('jump-point-commission-container'),
    };
    
    const buttons = {
        '添加签约主体按钮': document.getElementById('add-party-btn'),
        '添加回款信息按钮': document.getElementById('add-payment-info-btn'),
        '添加服务内容按钮': document.getElementById('add-service-content-btn'),
        '总价包干添加按钮': document.getElementById('add-fixed-total-btn'),
        '包干单价添加按钮': document.getElementById('add-fixed-unit-btn'),
        '累计提成添加按钮': document.getElementById('add-cumulative-commission-btn'),
        '分段提成添加按钮': document.getElementById('add-segmented-commission-btn'),
        '跳点提成添加按钮': document.getElementById('add-jump-point-commission-btn'),
    };
    
    const elementStatus = {};
    for (const [name, element] of Object.entries(criticalElements)) {
        const exists = element !== null;
        elementStatus[name] = exists ? '✅ 存在' : '❌ 不存在';
        if (!exists) {
            errors.push(`关键元素缺失: ${name}`);
        }
    }
    
    const buttonStatus = {};
    for (const [name, button] of Object.entries(buttons)) {
        const exists = button !== null;
        buttonStatus[name] = exists ? '✅ 存在' : '❌ 不存在';
        if (!exists) {
            warnings.push(`按钮缺失: ${name}`);
        }
    }
    
    console.table(elementStatus);
    console.table(buttonStatus);
    
    // ========== 2. 检查 JavaScript 变量 ==========
    console.log('');
    console.log('📋 [2/8] 检查 JavaScript 变量...');
    const variables = {
        'serviceTypeOptions': typeof serviceTypeOptions !== 'undefined' ? serviceTypeOptions : undefined,
        'ourUnits': typeof ourUnits !== 'undefined' ? ourUnits : undefined,
        'addPartyRow': typeof addPartyRow !== 'undefined' ? typeof addPartyRow : undefined,
        'addPaymentInfoRow': typeof addPaymentInfoRow !== 'undefined' ? typeof addPaymentInfoRow : undefined,
        'addServiceContent': typeof addServiceContent !== 'undefined' ? typeof addServiceContent : undefined,
    };
    
    const varStatus = {};
    for (const [name, value] of Object.entries(variables)) {
        if (value === undefined) {
            varStatus[name] = '❌ 未定义';
            errors.push(`变量未定义: ${name}`);
        } else {
            varStatus[name] = value instanceof Array ? `✅ 数组 (${value.length}项)` : `✅ ${typeof value}`;
        }
    }
    console.table(varStatus);
    
    // ========== 3. 检查事件绑定 ==========
    console.log('');
    console.log('📋 [3/8] 检查按钮事件绑定...');
    const eventBindings = {};
    
    for (const [name, button] of Object.entries(buttons)) {
        if (button) {
            // 检查是否有事件监听器（通过克隆元素检查）
            const clone = button.cloneNode(true);
            const hasListeners = button.onclick !== null || 
                                button.getAttribute('onclick') !== null ||
                                (button._listeners && button._listeners.length > 0);
            
            // 尝试触发点击事件看是否有响应
            let hasResponse = false;
            const testHandler = () => { hasResponse = true; };
            button.addEventListener('test', testHandler);
            button.dispatchEvent(new Event('test'));
            button.removeEventListener('test', testHandler);
            
            eventBindings[name] = hasResponse ? '✅ 已绑定' : '⚠️ 可能未绑定';
            if (!hasResponse && !hasListeners) {
                warnings.push(`按钮可能未绑定事件: ${name}`);
            }
        } else {
            eventBindings[name] = '❌ 按钮不存在';
        }
    }
    console.table(eventBindings);
    
    // ========== 4. 检查 CSS 样式 ==========
    console.log('');
    console.log('📋 [4/8] 检查 CSS 样式...');
    const formElement = document.getElementById('contract-form');
    if (formElement) {
        const styles = window.getComputedStyle(formElement);
        const styleIssues = [];
        
        if (styles.pointerEvents === 'none') {
            styleIssues.push('pointer-events: none (表单无法交互)');
            errors.push('表单被设置为 pointer-events: none');
        }
        
        if (styles.display === 'none') {
            styleIssues.push('display: none (表单被隐藏)');
            errors.push('表单被隐藏');
        }
        
        if (styles.visibility === 'hidden') {
            styleIssues.push('visibility: hidden (表单不可见)');
            errors.push('表单不可见');
        }
        
        if (styles.zIndex && parseInt(styles.zIndex) < 0) {
            styleIssues.push(`z-index: ${styles.zIndex} (可能被遮挡)`);
            warnings.push('表单 z-index 可能过低');
        }
        
        const styleInfo = {
            'display': styles.display,
            'visibility': styles.visibility,
            'pointer-events': styles.pointerEvents,
            'z-index': styles.zIndex,
            'position': styles.position,
            'opacity': styles.opacity,
        };
        
        console.table(styleInfo);
        if (styleIssues.length > 0) {
            console.warn('⚠️ 样式问题:', styleIssues);
        }
    } else {
        errors.push('无法检查样式：表单元素不存在');
    }
    
    // ========== 5. 检查 JavaScript 错误 ==========
    console.log('');
    console.log('📋 [5/8] 检查 JavaScript 错误...');
    
    // 捕获未处理的错误
    const originalError = console.error;
    const jsErrors = [];
    window.addEventListener('error', function(e) {
        jsErrors.push({
            message: e.message,
            filename: e.filename,
            lineno: e.lineno,
            colno: e.colno,
            error: e.error
        });
    });
    
    // 检查常见的函数是否存在
    const functions = ['addPartyRow', 'addPaymentInfoRow', 'addServiceContent', 'updateRowNumbers'];
    const functionStatus = {};
    for (const funcName of functions) {
        try {
            const func = window[funcName] || eval(funcName);
            functionStatus[funcName] = typeof func === 'function' ? '✅ 已定义' : '❌ 未定义';
            if (typeof func !== 'function') {
                errors.push(`函数未定义: ${funcName}`);
            }
        } catch (e) {
            functionStatus[funcName] = '❌ 未定义';
            errors.push(`函数未定义: ${funcName}`);
        }
    }
    console.table(functionStatus);
    
    // ========== 6. 检查 DOMContentLoaded 状态 ==========
    console.log('');
    console.log('📋 [6/8] 检查页面加载状态...');
    const loadStatus = {
        'document.readyState': document.readyState,
        'DOMContentLoaded 已触发': document.readyState !== 'loading',
        'window.onload 已触发': document.readyState === 'complete',
    };
    console.table(loadStatus);
    
    // ========== 7. 检查表单数据 ==========
    console.log('');
    console.log('📋 [7/8] 检查表单数据...');
    if (formElement) {
        const formData = new FormData(formElement);
        const formFields = {};
        for (const [key, value] of formData.entries()) {
            if (!formFields[key]) {
                formFields[key] = [];
            }
            formFields[key].push(value);
        }
        
        info.push(`表单字段数量: ${Object.keys(formFields).length}`);
        console.log(`表单包含 ${Object.keys(formFields).length} 个字段`);
        
        // 检查关键字段
        const criticalFields = ['client', 'contract_name', 'contract_amount'];
        const fieldStatus = {};
        for (const field of criticalFields) {
            const input = formElement.querySelector(`[name="${field}"]`);
            fieldStatus[field] = input ? '✅ 存在' : '❌ 不存在';
        }
        console.table(fieldStatus);
    }
    
    // ========== 8. 测试添加行功能 ==========
    console.log('');
    console.log('📋 [8/8] 测试添加行功能...');
    const testResults = {};
    
    // 测试总价包干添加按钮
    const addFixedTotalBtn = document.getElementById('add-fixed-total-btn');
    if (addFixedTotalBtn) {
        try {
            // 检查是否有点击事件
            const hasClickHandler = addFixedTotalBtn.onclick !== null;
            testResults['总价包干按钮'] = hasClickHandler ? '✅ 有事件处理器' : '⚠️ 无事件处理器';
            
            // 尝试手动触发（不实际执行，只检查）
            const container = document.getElementById('fixed-total-container');
            if (container) {
                testResults['总价包干容器'] = '✅ 存在';
            } else {
                testResults['总价包干容器'] = '❌ 不存在';
                errors.push('总价包干容器不存在');
            }
        } catch (e) {
            testResults['总价包干按钮'] = `❌ 错误: ${e.message}`;
            errors.push(`测试总价包干按钮失败: ${e.message}`);
        }
    } else {
        testResults['总价包干按钮'] = '❌ 按钮不存在';
    }
    
    // 测试其他按钮
    const otherButtons = ['add-fixed-unit-btn', 'add-payment-info-btn', 'add-service-content-btn'];
    for (const btnId of otherButtons) {
        const btn = document.getElementById(btnId);
        if (btn) {
            testResults[btnId] = '✅ 存在';
        } else {
            testResults[btnId] = '❌ 不存在';
            warnings.push(`按钮不存在: ${btnId}`);
        }
    }
    
    console.table(testResults);
    
    // ========== 输出总结 ==========
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════════════╗');
    console.log('║                         排查结果总结                              ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝');
    console.log('');
    
    if (errors.length > 0) {
        console.error('❌ 发现错误 (' + errors.length + ' 个):');
        errors.forEach((error, index) => {
            console.error(`   ${index + 1}. ${error}`);
        });
        console.log('');
    } else {
        console.log('✅ 未发现严重错误');
        console.log('');
    }
    
    if (warnings.length > 0) {
        console.warn('⚠️ 发现警告 (' + warnings.length + ' 个):');
        warnings.forEach((warning, index) => {
            console.warn(`   ${index + 1}. ${warning}`);
        });
        console.log('');
    }
    
    if (info.length > 0) {
        console.info('ℹ️ 信息:');
        info.forEach((item, index) => {
            console.info(`   ${index + 1}. ${item}`);
        });
        console.log('');
    }
    
    // ========== 提供修复建议 ==========
    console.log('💡 修复建议:');
    if (errors.length === 0 && warnings.length === 0) {
        console.log('   ✅ 未发现明显问题，表单应该可以正常工作');
        console.log('   💡 如果表单仍无法打开，请检查：');
        console.log('      1. 浏览器控制台是否有其他 JavaScript 错误');
        console.log('      2. 网络请求是否都成功（查看 Network 面板）');
        console.log('      3. 是否有浏览器扩展干扰');
    } else {
        if (errors.some(e => e.includes('未定义'))) {
            console.log('   🔧 变量或函数未定义：');
            console.log('      - 检查 JavaScript 文件是否正确加载');
            console.log('      - 检查变量作用域是否正确');
            console.log('      - 检查 DOMContentLoaded 事件是否正确触发');
        }
        
        if (errors.some(e => e.includes('不存在'))) {
            console.log('   🔧 DOM 元素不存在：');
            console.log('      - 检查 HTML 模板是否正确渲染');
            console.log('      - 检查元素 ID 是否正确');
            console.log('      - 检查是否有 JavaScript 错误导致页面未完全加载');
        }
        
        if (warnings.some(w => w.includes('未绑定'))) {
            console.log('   🔧 按钮事件未绑定：');
            console.log('      - 检查 DOMContentLoaded 事件是否正确触发');
            console.log('      - 检查事件绑定代码是否在正确的作用域内');
            console.log('      - 检查按钮是否在事件绑定代码执行后才创建');
        }
    }
    
    console.log('');
    console.log('════════════════════════════════════════════════════════════════════');
    
    // 返回结果对象供进一步分析
    return {
        errors: errors,
        warnings: warnings,
        info: info,
        elements: elementStatus,
        buttons: buttonStatus,
        variables: varStatus,
        eventBindings: eventBindings,
        testResults: testResults
    };
})();

