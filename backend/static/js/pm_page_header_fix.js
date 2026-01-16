// 计划管理页面标题区域样式自动修复脚本
// 简化版本，避免性能问题

(function() {
  function applyFixes() {
    const h1Elements = document.querySelectorAll('.plan-content .pm-page-header .pm-page-header-title-wrapper h1');
    
    h1Elements.forEach(function(h1) {
      // 直接设置内联样式（最高优先级）
      h1.style.fontSize = '24px';
      h1.style.setProperty('font-size', '24px', 'important');
    });
    
    const wrapper = document.querySelector('.pm-page-header-title-wrapper');
    if (wrapper) {
      wrapper.style.setProperty('display', 'flex', 'important');
      wrapper.style.setProperty('align-items', 'flex-end', 'important');
      wrapper.style.setProperty('gap', '12px', 'important');
      wrapper.style.setProperty('padding-bottom', '8px', 'important');
      wrapper.style.setProperty('border-bottom', '1px solid #E0E0E0', 'important');
      wrapper.style.setProperty('margin-bottom', '8px', 'important');
    }
    
    const subtitle = document.querySelector('.pm-subtitle');
    if (subtitle) {
      subtitle.style.setProperty('display', 'inline-block', 'important');
      subtitle.style.setProperty('margin', '0', 'important');
      subtitle.style.setProperty('padding', '0', 'important');
      subtitle.style.setProperty('line-height', '1.2', 'important');
    }
    
    const actions = document.querySelector('.pm-page-header .pm-actions');
    if (actions) {
      actions.style.setProperty('padding-bottom', '8px', 'important');
      actions.style.setProperty('border-bottom', '1px solid #E0E0E0', 'important');
      actions.style.setProperty('margin-bottom', '8px', 'important');
      actions.style.setProperty('align-self', 'flex-start', 'important');
    }
  }
  
  // DOM加载完成后执行一次
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyFixes);
  } else {
    applyFixes();
  }
  
  // 只在页面完全加载后再执行一次
  window.addEventListener('load', function() {
    setTimeout(applyFixes, 50);
  });
})();
