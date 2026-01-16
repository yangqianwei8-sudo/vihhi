/**
 * 合同表单排查脚本 - 简化版
 * 直接在浏览器控制台粘贴并执行
 * 
 * 使用方法：
 * 1. 打开合同表单页面
 * 2. 按 F12 打开开发者工具
 * 3. 切换到 Console 标签
 * 4. 复制下面的代码并粘贴到控制台，按回车执行
 */

// 快速排查函数
function debugContractForm() {
    console.clear();
    console.log('%c╔════════════════════════════════════════════════════════════════════╗', 'color: #0ea5e9; font-weight: bold');
    console.log('%c║         合同表单排查工具 - 错误日志输出                        ║', 'color: #0ea5e9; font-weight: bold');
    console.log('%c╚════════════════════════════════════════════════════════════════════╝', 'color: #0ea5e9; font-weight: bold');
    console.log('');
    
    const errors = [];
    const warnings = [];
    const info = [];
    
    // ========== 0. 检查当前页面 ==========
    console.log('%c[0/7] 检查当前页面...', 'color: #10b981; font-weight: bold');
    const currentUrl = window.location.href;
    const pageTitle = document.title;
    const currentPath = window.location.pathname;
    
    // 判断页面类型
    const isContractListPage = currentPath.includes('/management/') || 
                               currentPath.includes('/list') ||
                               currentPath.endsWith('/contracts/') ||
                               currentPath.endsWith('/contracts');
    
    const isContractFormPage = currentPath.includes('/create') || 
                               currentPath.includes('/edit/') ||
                               currentPath.includes('/add') ||
                               currentPath.match(/\/\d+\/edit/);
    
    const isContractPage = currentUrl.includes('contract') || 
                          currentUrl.includes('合同') || 
                          pageTitle.includes('合同') ||
                          pageTitle.includes('Contract');
    
    console.log(`  📄 当前 URL: ${currentUrl}`);
    console.log(`  📄 当前路径: ${currentPath}`);
    console.log(`  📄 页面标题: ${pageTitle}`);
    console.log(`  📄 是否合同相关页面: ${isContractPage ? '✅ 是' : '❌ 否'}`);
    console.log(`  📄 页面类型: ${isContractListPage ? '📋 列表页' : isContractFormPage ? '📝 表单页' : '❓ 未知'}`);
    
    if (isContractListPage) {
        console.error('%c❌ 错误：当前在合同管理列表页面！', 'color: #ef4444; font-weight: bold');
        console.error('  此脚本需要在合同创建或编辑表单页面运行');
        console.error('  请执行以下操作：');
        console.error('  1. 点击"创建合同"或"新建合同"按钮');
        console.error('  2. 或者点击某个合同的"编辑"按钮');
        console.error('  3. 进入表单页面后再运行此脚本');
        console.error('');
        console.error('  正确的表单页面 URL 应该类似：');
        console.error('    - /business/contracts/create/');
        console.error('    - /business/contracts/123/edit/');
        console.error('    - /contracts/add/');
        errors.push('当前在列表页面，需要在表单页面运行脚本');
        return { errors, warnings, info, pageType: 'list' };
    }
    
    if (!isContractFormPage && !isContractPage) {
        console.warn('%c⚠️ 警告：当前页面可能不是合同表单页面！', 'color: #f59e0b; font-weight: bold');
        console.warn('  请确保在合同创建或编辑页面运行此脚本');
        console.warn('  合同表单页面 URL 通常包含: /create/, /edit/, /add/');
        warnings.push('当前页面可能不是合同表单页面');
    }
    
    // 检查页面加载状态
    console.log(`  📄 页面加载状态: ${document.readyState}`);
    if (document.readyState === 'loading') {
        console.warn('  ⚠️ 页面仍在加载中，请等待页面完全加载后再运行脚本');
        warnings.push('页面可能未完全加载');
    }
    console.log('');
    
    // 1. 检查关键元素
    console.log('%c[1/7] 检查关键 DOM 元素...', 'color: #10b981; font-weight: bold');
    const elements = {
        'contract-form': '表单容器',
        'parties-container': '签约主体容器',
        'payment-info-container': '回款信息容器',
        'service-contents-container': '服务内容容器',
        'fixed-total-container': '总价包干容器',
        'fixed-unit-container': '包干单价容器',
    };
    
    for (const [id, name] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) {
            console.log(`  ✅ ${name} (${id}): 存在`);
        } else {
            console.error(`  ❌ ${name} (${id}): 不存在`);
            errors.push(`${name} (${id}) 不存在`);
        }
    }
    console.log('');
    
    // 2. 检查按钮
    console.log('%c[2/7] 检查添加行按钮...', 'color: #10b981; font-weight: bold');
    const buttons = {
        'add-fixed-total-btn': '总价包干',
        'add-fixed-unit-btn': '包干单价',
        'add-payment-info-btn': '回款信息',
        'add-service-content-btn': '服务内容',
        'add-cumulative-commission-btn': '累计提成',
        'add-segmented-commission-btn': '分段提成',
        'add-jump-point-commission-btn': '跳点提成',
    };
    
    for (const [id, name] of Object.entries(buttons)) {
        const btn = document.getElementById(id);
        if (btn) {
            const hasClick = btn.onclick !== null || btn.getAttribute('onclick');
            console.log(`  ✅ ${name}按钮 (${id}): 存在 ${hasClick ? '✓ 有事件' : '⚠ 无事件'}`);
            if (!hasClick) {
                warnings.push(`${name}按钮 (${id}) 可能未绑定事件`);
            }
        } else {
            console.warn(`  ⚠️ ${name}按钮 (${id}): 不存在`);
            warnings.push(`${name}按钮 (${id}) 不存在`);
        }
    }
    console.log('');
    
    // 3. 检查 JavaScript 变量
    console.log('%c[3/7] 检查 JavaScript 变量...', 'color: #10b981; font-weight: bold');
    try {
        if (typeof serviceTypeOptions !== 'undefined') {
            console.log(`  ✅ serviceTypeOptions: 已定义 (${serviceTypeOptions.length} 项)`);
        } else {
            console.error('  ❌ serviceTypeOptions: 未定义');
            errors.push('serviceTypeOptions 未定义');
        }
    } catch (e) {
        console.error(`  ❌ serviceTypeOptions: ${e.message}`);
        errors.push(`serviceTypeOptions 检查失败: ${e.message}`);
    }
    
    try {
        if (typeof ourUnits !== 'undefined') {
            console.log(`  ✅ ourUnits: 已定义 (${ourUnits.length} 项)`);
        } else {
            console.warn('  ⚠️ ourUnits: 未定义');
            warnings.push('ourUnits 未定义');
        }
    } catch (e) {
        console.warn(`  ⚠️ ourUnits: ${e.message}`);
    }
    console.log('');
    
    // 4. 检查表单样式
    console.log('%c[4/7] 检查表单样式...', 'color: #10b981; font-weight: bold');
    const form = document.getElementById('contract-form');
    if (form) {
        const styles = window.getComputedStyle(form);
        const styleInfo = {
            'display': styles.display,
            'visibility': styles.visibility,
            'pointer-events': styles.pointerEvents,
            'z-index': styles.zIndex,
            'opacity': styles.opacity,
        };
        
        console.table(styleInfo);
        
        if (styles.pointerEvents === 'none') {
            console.error('  ❌ pointer-events: none (表单无法交互)');
            errors.push('表单被设置为 pointer-events: none');
        }
        if (styles.display === 'none') {
            console.error('  ❌ display: none (表单被隐藏)');
            errors.push('表单被隐藏');
        }
        if (parseInt(styles.zIndex) < 0) {
            console.warn(`  ⚠️ z-index: ${styles.zIndex} (可能被遮挡)`);
            warnings.push('表单 z-index 可能过低');
        }
    } else {
        console.error('  ❌ 无法检查样式：表单元素不存在');
    }
    console.log('');
    
    // 5. 检查页面加载状态
    console.log('%c[5/7] 检查页面加载状态...', 'color: #10b981; font-weight: bold');
    console.log(`  📄 document.readyState: ${document.readyState}`);
    console.log(`  📄 DOMContentLoaded: ${document.readyState !== 'loading' ? '✅ 已触发' : '❌ 未触发'}`);
    console.log(`  📄 window.onload: ${document.readyState === 'complete' ? '✅ 已触发' : '⏳ 未触发'}`);
    console.log('');
    
    // 6. 检查所有表单元素（备用检查）
    console.log('%c[6/7] 检查页面中的表单元素...', 'color: #10b981; font-weight: bold');
    const allForms = document.querySelectorAll('form');
    console.log(`  📄 页面中的表单数量: ${allForms.length}`);
    if (allForms.length > 0) {
        allForms.forEach((form, index) => {
            const formId = form.id || '(无ID)';
            const formAction = form.action || '(无action)';
            const formMethod = form.method || '(无method)';
            const formStyle = window.getComputedStyle(form);
            console.log(`  📄 表单 ${index + 1}: id="${formId}", method="${formMethod}", action="${formAction}"`);
            console.log(`      display: ${formStyle.display}, visibility: ${formStyle.visibility}, pointer-events: ${formStyle.pointerEvents}`);
            
            // 检查表单内的所有元素
            const formElements = form.querySelectorAll('[id]');
            console.log(`      表单内包含ID的元素数量: ${formElements.length}`);
            if (formElements.length > 0) {
                const formElementIds = Array.from(formElements).slice(0, 10).map(el => el.id).join(', ');
                console.log(`      前10个元素ID: ${formElementIds}`);
            }
        });
    } else {
        console.warn('  ⚠️ 页面中没有任何表单元素');
        warnings.push('页面中未找到任何表单元素');
    }
    
    // 检查是否有任何包含 "contract" 的元素
    const contractElements = document.querySelectorAll('[id*="contract"], [class*="contract"], [name*="contract"]');
    console.log(`  📄 包含 "contract" 的元素数量: ${contractElements.length}`);
    if (contractElements.length > 0) {
        console.log('  📄 找到的合同相关元素:');
        contractElements.forEach((el, index) => {
            if (index < 10) {
                const tagName = el.tagName.toLowerCase();
                const elId = el.id || '(无ID)';
                const elClass = el.className || '(无class)';
                console.log(`    ${index + 1}. <${tagName}> id="${elId}" class="${elClass}"`);
            }
        });
        if (contractElements.length > 10) {
            console.log(`    ... 还有 ${contractElements.length - 10} 个元素`);
        }
    }
    
    // 检查是否有 iframe
    const iframes = document.querySelectorAll('iframe');
    if (iframes.length > 0) {
        console.warn(`  ⚠️ 页面中包含 ${iframes.length} 个 iframe，可能影响元素查找`);
        warnings.push(`页面包含 ${iframes.length} 个 iframe`);
        iframes.forEach((iframe, index) => {
            console.log(`    iframe ${index + 1}: src="${iframe.src || '(无src)'}"`);
        });
    }
    
    // 尝试在所有可能的容器中查找元素
    console.log('  📄 尝试在所有容器中查找目标元素...');
    const targetIds = ['contract-form', 'parties-container', 'payment-info-container', 'service-contents-container', 'fixed-total-container', 'fixed-unit-container'];
    targetIds.forEach(id => {
        // 尝试直接查找
        let el = document.getElementById(id);
        if (!el) {
            // 尝试在 iframe 中查找
            iframes.forEach(iframe => {
                try {
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    el = iframeDoc.getElementById(id);
                    if (el) {
                        console.log(`    ✅ 在 iframe 中找到: ${id}`);
                    }
                } catch (e) {
                    // 跨域 iframe 无法访问
                }
            });
        }
        if (!el) {
            // 尝试通过属性选择器查找
            el = document.querySelector(`[id="${id}"]`);
        }
        if (!el) {
            // 尝试查找包含该ID的字符串的元素
            const allElements = document.querySelectorAll('*');
            for (const elem of allElements) {
                if (elem.id && elem.id.includes(id.split('-')[0])) {
                    console.log(`    ⚠️ 找到相似ID: ${elem.id} (期望: ${id})`);
                    break;
                }
            }
        }
    });
    
    if (contractElements.length === 0 && allForms.length === 0) {
        console.error('  ❌ 页面中未找到任何合同相关的元素');
        errors.push('页面中未找到任何合同相关的元素，可能不在合同表单页面');
    }
    console.log('');
    
    // 7. 检查 JavaScript 错误
    console.log('%c[7/7] 检查 JavaScript 错误...', 'color: #10b981; font-weight: bold');
    
    // 检查常见的函数
    const functions = ['addPartyRow', 'addPaymentInfoRow', 'addServiceContent'];
    for (const funcName of functions) {
        try {
            const func = window[funcName];
            if (typeof func === 'function') {
                console.log(`  ✅ ${funcName}: 已定义`);
            } else {
                console.warn(`  ⚠️ ${funcName}: 未定义`);
                warnings.push(`函数未定义: ${funcName}`);
            }
        } catch (e) {
            console.warn(`  ⚠️ ${funcName}: ${e.message}`);
        }
    }
    console.log('');
    
    // 输出总结
    console.log('%c╔════════════════════════════════════════════════════════════════════╗', 'color: #0ea5e9; font-weight: bold');
    console.log('%c║                         排查结果总结                              ║', 'color: #0ea5e9; font-weight: bold');
    console.log('%c╚════════════════════════════════════════════════════════════════════╝', 'color: #0ea5e9; font-weight: bold');
    console.log('');
    
    if (errors.length > 0) {
        console.error(`%c❌ 发现错误 (${errors.length} 个):`, 'color: #ef4444; font-weight: bold');
        errors.forEach((error, index) => {
            console.error(`   ${index + 1}. ${error}`);
        });
        console.log('');
    } else {
        console.log('%c✅ 未发现严重错误', 'color: #10b981; font-weight: bold');
        console.log('');
    }
    
    if (warnings.length > 0) {
        console.warn(`%c⚠️ 发现警告 (${warnings.length} 个):`, 'color: #f59e0b; font-weight: bold');
        warnings.forEach((warning, index) => {
            console.warn(`   ${index + 1}. ${warning}`);
        });
        console.log('');
    }
    
    // 修复建议
    console.log('%c💡 修复建议:', 'color: #0ea5e9; font-weight: bold');
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
            console.log('      - 确认当前页面是合同表单页面（URL 应包含 contract 或 合同）');
            console.log('      - 等待页面完全加载后再运行脚本');
            console.log('      - 检查 HTML 模板是否正确渲染');
            console.log('      - 检查元素 ID 是否正确');
            console.log('      - 检查是否有 JavaScript 错误导致页面未完全加载');
            console.log('      - 尝试刷新页面（Ctrl+F5 强制刷新）');
        }
        
        if (errors.some(e => e.includes('未找到任何合同相关的元素'))) {
            console.log('   🔧 页面中未找到合同相关元素：');
            console.log('      - 确认当前页面是合同创建或编辑页面');
            console.log('      - 检查 URL 是否正确');
            console.log('      - 检查是否有权限访问该页面');
            console.log('      - 检查页面是否被重定向');
        }
        
        if (warnings.some(w => w.includes('未绑定'))) {
            console.log('   🔧 按钮事件未绑定：');
            console.log('      - 检查 DOMContentLoaded 事件是否正确触发');
            console.log('      - 检查事件绑定代码是否在正确的作用域内');
        }
    }
    
    console.log('');
    console.log('%c════════════════════════════════════════════════════════════════════', 'color: #6b7280');
    
    return {
        errors: errors,
        warnings: warnings,
        info: info
    };
}

// 自动执行
debugContractForm();

// 导出函数供后续使用
window.debugContractForm = debugContractForm;

