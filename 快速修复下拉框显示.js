/**
 * 快速修复下拉框显示问题
 * 在浏览器控制台运行此脚本
 */

(function() {
    console.log('🔧 开始修复下拉框显示问题...');
    
    const dropdown = document.getElementById('companyDropdown');
    const nameInput = document.querySelector('[name="name"]');
    
    if (!dropdown) {
        console.error('❌ 找不到下拉框元素');
        return;
    }
    
    if (!nameInput) {
        console.error('❌ 找不到输入框元素');
        return;
    }
    
    // 1. 检查当前样式
    const styles = window.getComputedStyle(dropdown);
    console.log('当前下拉框样式:', {
        display: styles.display,
        visibility: styles.visibility,
        opacity: styles.opacity,
        zIndex: styles.zIndex,
        position: styles.position,
        top: styles.top,
        left: styles.left,
        width: styles.width,
        height: dropdown.scrollHeight
    });
    
    // 2. 强制设置样式
    dropdown.style.cssText = `
        position: absolute !important;
        top: 100% !important;
        left: 0 !important;
        right: 0 !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 9999 !important;
        background: white !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
        max-height: 300px !important;
        overflow-y: auto !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        margin-top: 2px !important;
    `;
    
    // 3. 添加测试内容
    dropdown.innerHTML = `
        <div class="autocomplete-item" style="padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;">
            <div style="font-weight: 500; color: #333; margin-bottom: 4px;">测试企业1</div>
            <div style="font-size: 12px; color: #666;">统一信用代码: 测试123</div>
        </div>
        <div class="autocomplete-item" style="padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;">
            <div style="font-weight: 500; color: #333; margin-bottom: 4px;">测试企业2</div>
            <div style="font-size: 12px; color: #666;">统一信用代码: 测试456</div>
        </div>
        <div class="autocomplete-item" style="padding: 10px 15px; cursor: pointer;">
            <div style="font-weight: 500; color: #333; margin-bottom: 4px;">测试企业3</div>
            <div style="font-size: 12px; color: #666;">统一信用代码: 测试789</div>
        </div>
    `;
    
    dropdown.classList.add('show');
    
    console.log('✅ 下拉框样式已强制设置');
    console.log('✅ 已添加测试内容');
    console.log('');
    console.log('👀 请查看输入框下方是否显示下拉列表');
    console.log('');
    console.log('如果能看到测试内容，说明样式正常，问题在于：');
    console.log('  1. API数据渲染问题');
    console.log('  2. 数据格式问题');
    console.log('');
    console.log('如果看不到，请告诉我：');
    console.log('  1. 下拉框是否在其他位置（滚动页面查找）');
    console.log('  2. 是否有其他元素遮挡');
    console.log('  3. 是否被父元素overflow隐藏');
    
    // 4. 检查父元素
    const parent = dropdown.parentElement;
    if (parent) {
        const parentStyles = window.getComputedStyle(parent);
        console.log('');
        console.log('父元素样式:', {
            position: parentStyles.position,
            overflow: parentStyles.overflow,
            zIndex: parentStyles.zIndex
        });
        
        if (parentStyles.overflow === 'hidden') {
            console.warn('⚠️ 父元素设置了overflow: hidden，可能影响显示');
        }
    }
    
    // 5. 检查是否有遮挡
    const rect = dropdown.getBoundingClientRect();
    console.log('');
    console.log('下拉框位置:', {
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
        visible: rect.height > 0 && rect.width > 0
    });
    
})();

