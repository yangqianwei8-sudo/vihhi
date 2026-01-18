// 计划管理页面标题区域样式自动修复脚本
// 强制覆盖 Bootstrap RFS 响应式字体大小

(function() {
  function applyFixes() {
    const h1Elements = document.querySelectorAll('.plan-content .pm-page-header .pm-page-header-title-wrapper h1, .pm-page-header .pm-page-header-title-wrapper h1');
    
    h1Elements.forEach(function(h1) {
      // 直接设置内联样式（最高优先级）- 使用与用户测试相同的代码
      h1.style.setProperty('font-size', '24px', 'important');
      // 确保覆盖所有可能的RFS值
      if (window.getComputedStyle(h1).fontSize !== '24px') {
        h1.style.setProperty('font-size', '24px', 'important');
      }
    });
    
    const wrapper = document.querySelectorAll('.plan-content .pm-page-header .pm-page-header-title-wrapper, .pm-page-header-title-wrapper');
    wrapper.forEach(function(w) {
      w.style.setProperty('display', 'flex', 'important');
      w.style.setProperty('align-items', 'flex-end', 'important');
      w.style.setProperty('gap', '12px', 'important');
      w.style.setProperty('padding-bottom', '8px', 'important');
      w.style.setProperty('border-bottom', '1px solid #E0E0E0', 'important');
      w.style.setProperty('margin-bottom', '8px', 'important');
    });
    
    const subtitle = document.querySelectorAll('.plan-content .pm-page-header .pm-page-header-title-wrapper .pm-subtitle, .pm-page-header .pm-page-header-title-wrapper .pm-subtitle, .pm-subtitle');
    subtitle.forEach(function(s) {
      s.style.setProperty('display', 'inline-block', 'important');
      s.style.setProperty('margin', '0', 'important');
      s.style.setProperty('padding', '0 0 2px 0', 'important');
      s.style.setProperty('line-height', '1.2', 'important');
      s.style.setProperty('border-bottom', 'none', 'important');
      s.style.setProperty('border-bottom-width', '0', 'important');
      s.style.setProperty('border-bottom-style', 'none', 'important');
      s.style.setProperty('border-bottom-color', 'transparent', 'important');
      s.style.setProperty('text-decoration', 'none', 'important');
      s.style.setProperty('text-decoration-line', 'none', 'important');
      s.style.setProperty('text-decoration-style', 'none', 'important');
      s.style.setProperty('text-decoration-color', 'transparent', 'important');
      // 确保span标签内也没有下划线
      const spans = s.querySelectorAll('span');
      spans.forEach(function(span) {
        span.style.setProperty('border-bottom', 'none', 'important');
        span.style.setProperty('border-bottom-width', '0', 'important');
        span.style.setProperty('border-bottom-style', 'none', 'important');
        span.style.setProperty('border-bottom-color', 'transparent', 'important');
        span.style.setProperty('text-decoration', 'none', 'important');
        span.style.setProperty('text-decoration-line', 'none', 'important');
        span.style.setProperty('text-decoration-style', 'none', 'important');
        span.style.setProperty('text-decoration-color', 'transparent', 'important');
      });
    });
    
    const actions = document.querySelector('.pm-page-header .pm-actions');
    if (actions) {
      actions.style.setProperty('padding-bottom', '8px', 'important');
      actions.style.setProperty('border-bottom', '1px solid #E0E0E0', 'important');
      actions.style.setProperty('margin-bottom', '8px', 'important');
      actions.style.setProperty('align-self', 'flex-start', 'important');
    }
  }
  
  // 立即执行一次（如果DOM已加载）
  if (document.readyState !== 'loading') {
    applyFixes();
  }
  
  // DOM加载完成后执行
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      applyFixes();
      // 延迟执行，确保在Bootstrap RFS之后
      setTimeout(applyFixes, 100);
      setTimeout(applyFixes, 300);
      setTimeout(applyFixes, 500);
    });
  } else {
    // DOM已加载，立即执行并延迟执行
    setTimeout(applyFixes, 100);
    setTimeout(applyFixes, 300);
    setTimeout(applyFixes, 500);
  }
  
  // 页面完全加载后再执行
  window.addEventListener('load', function() {
    setTimeout(applyFixes, 100);
    setTimeout(applyFixes, 300);
    setTimeout(applyFixes, 500);
  });
  
  // 使用 MutationObserver 监听DOM变化，确保RFS修改后也能覆盖
  let observer = null;
  
  function setupObserver() {
    if (observer) {
      observer.disconnect();
    }
    
    observer = new MutationObserver(function(mutations) {
      let shouldFix = false;
      mutations.forEach(function(mutation) {
        if (mutation.type === 'attributes') {
          const target = mutation.target;
          if (target.tagName === 'H1' && target.closest('.pm-page-header-title-wrapper')) {
            const computedSize = window.getComputedStyle(target).fontSize;
            if (computedSize !== '24px') {
              shouldFix = true;
            }
          }
        }
      });
      
      if (shouldFix) {
        applyFixes();
      }
    });
    
    const h1Elements = document.querySelectorAll('.plan-content .pm-page-header .pm-page-header-title-wrapper h1, .pm-page-header .pm-page-header-title-wrapper h1');
    h1Elements.forEach(function(h1) {
      observer.observe(h1, {
        attributes: true,
        attributeFilter: ['style', 'class'],
        attributeOldValue: true
      });
      // 也观察父元素的变化
      const parent = h1.closest('.pm-page-header-title-wrapper');
      if (parent) {
        observer.observe(parent, {
          attributes: true,
          attributeFilter: ['style', 'class']
        });
      }
    });
  }
  
  // 延迟设置观察者，确保元素已存在
  setTimeout(function() {
    setupObserver();
  }, 500);
  
  // 窗口大小改变时也重新应用（RFS可能在窗口大小改变时重新计算）
  let resizeTimer = null;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
      applyFixes();
    }, 100);
  });
})();
