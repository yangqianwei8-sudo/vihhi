/**
 * 启信宝自动填充功能 - 浏览器端快速测试脚本
 * 
 * 使用方法：
 * 1. 打开创建客户页面
 * 2. 按 F12 打开控制台
 * 3. 复制整个脚本粘贴到控制台并回车
 * 4. 查看输出结果
 */

(function() {
    console.log('╔════════════════════════════════════════════════════════════════════╗');
    console.log('║         启信宝自动填充功能 - 浏览器端诊断工具                    ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝');
    console.log('');
    
    // 步骤1: 检查DOM元素
    console.log('📋 [1/6] 检查DOM元素...');
    const nameInput = document.querySelector('[name="name"]');
    const creditCodeInput = document.querySelector('[name="unified_credit_code"]');
    const dropdown = document.getElementById('companyDropdown');
    const form = document.querySelector('form#customerForm');
    
    const elements = {
        '客户名称输入框': nameInput ? '✅ 存在' : '❌ 不存在',
        '统一信用代码输入框': creditCodeInput ? '✅ 存在' : '❌ 不存在',
        '下拉列表容器': dropdown ? '✅ 存在' : '❌ 不存在',
        '表单': form ? '✅ 存在' : '❌ 不存在'
    };
    
    console.table(elements);
    
    if (!nameInput || !dropdown) {
        console.error('❌ 缺少关键元素，无法继续测试');
        return;
    }
    
    // 步骤2: 检查下拉框样式
    console.log('');
    console.log('🎨 [2/6] 检查下拉框样式...');
    const dropdownStyles = window.getComputedStyle(dropdown);
    console.table({
        'display': dropdownStyles.display,
        'visibility': dropdownStyles.visibility,
        'opacity': dropdownStyles.opacity,
        'z-index': dropdownStyles.zIndex,
        'position': dropdownStyles.position,
        'width': dropdownStyles.width,
        'height': dropdownStyles.height
    });
    
    // 步骤3: 检查事件监听器
    console.log('');
    console.log('👂 [3/6] 检查事件监听器...');
    // 手动添加一个测试监听器
    let testEventFired = false;
    const testListener = function() {
        testEventFired = true;
        console.log('✅ 输入事件已触发');
    };
    nameInput.addEventListener('input', testListener, { once: true });
    console.log('✅ 已添加测试事件监听器');
    console.log('   请在输入框中输入任意字符测试...');
    
    // 步骤4: 测试API连接
    console.log('');
    console.log('🌐 [4/6] 测试API连接...');
    console.log('   正在调用搜索API（关键字：腾讯）...');
    
    fetch('/api/customer/search-company/?keyword=腾讯&match_type=ename', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('   状态码:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            console.log('   ✅ API调用成功');
            const items = data.data && data.data.items ? data.data.items : [];
            console.log(`   📊 找到 ${items.length} 个结果`);
            if (items.length > 0) {
                console.log(`   📝 第一个结果: ${items[0].name || '未知'}`);
            }
            return data;
        } else {
            throw new Error(data ? data.message : 'API返回失败');
        }
    })
    .then(apiData => {
        // 步骤5: 测试下拉框显示
        console.log('');
        console.log('🎯 [5/6] 测试下拉框显示...');
        
        // 手动填充下拉框
        if (apiData && apiData.data && apiData.data.items) {
            dropdown.innerHTML = '';
            const items = apiData.data.items.slice(0, 5); // 只显示前5个
            
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.innerHTML = `
                    <div class="autocomplete-item-name">${item.name || '未知企业'}</div>
                    <div class="autocomplete-item-meta">
                        <span>统一信用代码: ${item.credit_no || '—'}</span>
                        <span>法定代表人: ${item.oper_name || '—'}</span>
                    </div>
                `;
                dropdown.appendChild(div);
            });
            
            // 强制显示下拉框
            dropdown.style.display = 'block';
            dropdown.classList.add('show');
            dropdown.style.zIndex = '9999';
            
            console.log('   ✅ 下拉框已手动填充并显示');
            console.log(`   📋 显示了 ${items.length} 条结果`);
            console.log('   👀 请查看输入框下方是否出现下拉列表');
            
            // 步骤6: 最终检查
            console.log('');
            console.log('✅ [6/6] 诊断完成');
            console.log('');
            console.log('📊 诊断总结:');
            console.log('');
            
            const summary = {
                'DOM元素': '✅ 正常',
                '下拉框样式': dropdownStyles.display === 'none' ? '⚠️ 初始隐藏（正常）' : '✅ 可见',
                'API连接': '✅ 正常',
                '下拉框显示': '✅ 已手动显示',
                '事件监听': testEventFired ? '✅ 已触发' : '⏳ 等待测试'
            };
            
            console.table(summary);
            console.log('');
            console.log('💡 建议:');
            console.log('   1. 如果能看到下拉列表，说明功能正常，可能是事件绑定问题');
            console.log('   2. 如果看不到下拉列表，检查是否有CSS冲突');
            console.log('   3. 尝试刷新页面（Ctrl+F5）重新加载');
            console.log('   4. 在输入框中输入"腾讯"测试自动搜索');
            console.log('');
            
        } else {
            console.error('   ❌ API返回数据格式错误');
        }
    })
    .catch(error => {
        console.error('   ❌ API调用失败:', error.message);
        console.log('');
        console.log('🔧 可能的解决方案:');
        console.log('   1. 检查是否已登录系统');
        console.log('   2. 检查后端服务是否运行');
        console.log('   3. 检查网络连接');
        console.log('   4. 查看后端日志: tail -f /tmp/gunicorn_error.log');
    });
    
    // 提供手动测试函数
    window.testSearch = function(keyword) {
        keyword = keyword || '腾讯';
        console.log(`🔍 手动测试搜索: ${keyword}`);
        
        const dropdown = document.getElementById('companyDropdown');
        if (!dropdown) {
            console.error('❌ 下拉框不存在');
            return;
        }
        
        dropdown.innerHTML = '<div class="autocomplete-item"><div class="text-center text-muted">搜索中...</div></div>';
        dropdown.style.display = 'block';
        dropdown.classList.add('show');
        
        fetch(`/api/customer/search-company/?keyword=${encodeURIComponent(keyword)}&match_type=ename`)
            .then(r => r.json())
            .then(d => {
                if (d.success && d.data && d.data.items) {
                    dropdown.innerHTML = '';
                    d.data.items.slice(0, 10).forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'autocomplete-item';
                        div.innerHTML = `
                            <div class="autocomplete-item-name">${item.name || '未知'}</div>
                            <div class="autocomplete-item-meta">
                                <span>统一信用代码: ${item.credit_no || '—'}</span>
                                <span>法定代表人: ${item.oper_name || '—'}</span>
                            </div>
                        `;
                        dropdown.appendChild(div);
                    });
                    console.log(`✅ 显示了 ${d.data.items.length} 个结果`);
                } else {
                    dropdown.innerHTML = '<div class="autocomplete-item"><div class="text-center text-muted">未找到结果</div></div>';
                }
            })
            .catch(e => {
                console.error('❌ 搜索失败:', e);
                dropdown.innerHTML = '<div class="autocomplete-item"><div class="text-center text-muted">搜索失败</div></div>';
            });
    };
    
    console.log('');
    console.log('💡 提示: 您可以使用 testSearch("企业名称") 手动测试搜索功能');
    console.log('   例如: testSearch("腾讯")');
    console.log('');
    
})();

