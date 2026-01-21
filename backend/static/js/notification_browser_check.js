/**
 * 通知系统浏览器兼容性检查
 * 
 * 在浏览器控制台中运行此脚本来诊断浏览器兼容性问题
 */

(function() {
    'use strict';
    
    console.log('🔍 开始浏览器兼容性检查...\n');
    
    // 1. 浏览器信息
    console.log('【1. 浏览器信息】');
    const ua = navigator.userAgent;
    console.log('User Agent:', ua);
    
    // 检测浏览器类型
    let browserType = 'Unknown';
    if (ua.includes('Chrome') && !ua.includes('Edg') && !ua.includes('OPR')) {
        browserType = 'Chrome';
    } else if (ua.includes('Edg')) {
        browserType = 'Edge';
    } else if (ua.includes('Firefox')) {
        browserType = 'Firefox';
    } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
        browserType = 'Safari';
    } else if (ua.includes('360')) {
        browserType = '360 Browser';
    } else if (ua.includes('OPR')) {
        browserType = 'Opera';
    }
    console.log('浏览器类型:', browserType);
    console.log('');
    
    // 2. JavaScript特性支持检查
    console.log('【2. JavaScript特性支持】');
    const features = {
        'fetch': typeof fetch !== 'undefined',
        'Promise': typeof Promise !== 'undefined',
        'Array.isArray': typeof Array.isArray === 'function',
        'Array.map': typeof Array.prototype.map === 'function',
        'Array.filter': typeof Array.prototype.filter === 'function',
        'Arrow Functions': (() => true)(),
        'Template Literals': typeof `test` === 'string',
        'const/let': (function() { try { eval('const test = 1'); return true; } catch(e) { return false; } })(),
    };
    
    for (const [feature, supported] of Object.entries(features)) {
        console.log(`  ${supported ? '✓' : '❌'} ${feature}: ${supported}`);
    }
    console.log('');
    
    // 3. 检查通知组件是否加载
    console.log('【3. 通知组件检查】');
    const iconWrapper = document.getElementById('notificationIcon');
    const modal = document.getElementById('notificationModal');
    const badge = document.getElementById('notificationBadge');
    const list = document.getElementById('notificationList');
    
    console.log('  通知图标:', iconWrapper ? '✓ 存在' : '❌ 不存在');
    console.log('  通知模态框:', modal ? '✓ 存在' : '❌ 不存在');
    console.log('  通知徽章:', badge ? '✓ 存在' : '❌ 不存在');
    console.log('  通知列表:', list ? '✓ 存在' : '❌ 不存在');
    console.log('');
    
    // 4. 检查脚本是否加载
    console.log('【4. 脚本加载检查】');
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    const notificationScript = scripts.find(s => s.src.includes('notification_widget.js'));
    console.log('  notification_widget.js:', notificationScript ? '✓ 已加载' : '❌ 未加载');
    if (notificationScript) {
        console.log('  脚本路径:', notificationScript.src);
    }
    console.log('');
    
    // 5. 测试API调用
    console.log('【5. API调用测试】');
    const baseURL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8001/api' 
        : '/api';
    
    fetch(`${baseURL}/plan/notifications/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    })
    .then(response => {
        console.log('  状态码:', response.status);
        console.log('  状态文本:', response.statusText);
        console.log('  Content-Type:', response.headers.get('Content-Type'));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('  ✓ API调用成功');
        console.log('  响应数据类型:', typeof data);
        console.log('  是否有results字段:', !!data.results);
        console.log('  是否有notifications字段:', !!data.notifications);
        console.log('  是否为数组:', Array.isArray(data));
        
        let notificationCount = 0;
        if (data.results && Array.isArray(data.results)) {
            notificationCount = data.results.length;
        } else if (Array.isArray(data)) {
            notificationCount = data.length;
        } else if (data.notifications && Array.isArray(data.notifications)) {
            notificationCount = data.notifications.length;
        }
        console.log('  通知数量:', notificationCount);
        
        if (notificationCount > 0) {
            console.log('  第一条通知:', data.results?.[0] || data[0] || data.notifications?.[0]);
        }
    })
    .catch(error => {
        console.error('  ❌ API调用失败:', error);
        console.error('  错误详情:', error.message);
    });
    
    // 6. Cookie检查
    console.log('\n【6. Cookie/Session检查】');
    console.log('  document.cookie:', document.cookie ? '✓ 有Cookie' : '⚠️  无Cookie');
    if (document.cookie) {
        const cookies = document.cookie.split(';').map(c => c.trim());
        console.log('  Cookie数量:', cookies.length);
        // 检查sessionid
        const hasSession = cookies.some(c => c.startsWith('sessionid') || c.startsWith('csrftoken'));
        console.log('  有Session/CSRF Cookie:', hasSession ? '✓' : '⚠️');
    }
    console.log('');
    
    // 7. 控制台错误检查
    console.log('【7. 控制台错误】');
    console.log('  请检查控制台是否有红色错误信息');
    console.log('  如果有错误，请复制错误信息');
    console.log('');
    
    // 8. 网络请求检查
    console.log('【8. 网络请求检查】');
    console.log('  请打开开发者工具 -> Network 标签');
    console.log('  查找对 /api/plan/notifications/ 的请求');
    console.log('  检查：');
    console.log('    - 请求状态码（应该是200）');
    console.log('    - 请求头（是否有Cookie/Authorization）');
    console.log('    - 响应数据（是否包含通知）');
    console.log('');
    
    // 9. 浏览器特定问题
    console.log('【9. 浏览器特定问题排查】');
    if (browserType === 'Safari') {
        console.log('  ⚠️  Safari浏览器可能的问题：');
        console.log('    - 第三方Cookie被阻止');
        console.log('    - 需要启用"阻止跨站跟踪"');
    } else if (browserType === 'Firefox') {
        console.log('  ⚠️  Firefox浏览器可能的问题：');
        console.log('    - 严格隐私模式可能阻止Cookie');
        console.log('    - 需要检查Cookie设置');
    } else if (browserType === 'Edge') {
        console.log('  ⚠️  Edge浏览器可能的问题：');
        console.log('    - 跟踪防护可能影响请求');
        console.log('    - 需要检查隐私设置');
    }
    console.log('');
    
    console.log('✅ 检查完成！请根据上述信息排查问题。');
})();
