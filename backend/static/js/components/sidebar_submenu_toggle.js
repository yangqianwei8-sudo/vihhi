(function () {
  const STORAGE_KEY = 'vh-sb-open-keys';

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const arr = raw ? JSON.parse(raw) : [];
      return new Set(Array.isArray(arr) ? arr : []);
    } catch (e) {
      return new Set();
    }
  }

  function save(set) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set)));
  }

  const openKeys = load();

  function setOpen(parentEl, open) {
    if (!parentEl) return;
    
    const key = parentEl.getAttribute('data-sb-key') || '';
    parentEl.classList.toggle('is-open', open);

    const btn = parentEl.querySelector('[data-sb-toggle]');
    if (btn) {
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    const children = parentEl.querySelector('[data-sb-children]');
    if (children) {
      children.classList.toggle('is-open', open);
    }

    if (!key) return;
    if (open) {
      openKeys.add(key);
    } else {
      openKeys.delete(key);
    }
    save(openKeys);
  }

  function init() {
    // 初始化：localStorage 优先；其次如果子菜单内有 is-active，则默认展开
    const parents = document.querySelectorAll('[data-sb-parent]');
    parents.forEach((parentEl) => {
      const key = parentEl.getAttribute('data-sb-key') || '';
      const hasActiveChild = !!parentEl.querySelector('.vh-sb__child.is-active');
      const shouldOpen = (key && openKeys.has(key)) || hasActiveChild;
      setOpen(parentEl, shouldOpen);
    });
  }

  // 事件委托：保证点击一定生效
  function handleClick(e) {
    const btn = e.target.closest('[data-sb-toggle]');
    if (!btn) return;

    const parentEl = btn.closest('[data-sb-parent]');
    if (!parentEl) return;

    e.preventDefault();
    e.stopPropagation();

    const isOpen = parentEl.classList.contains('is-open');
    setOpen(parentEl, !isOpen);
  }

  // 等待 DOM 加载完成
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      init();
      document.addEventListener('click', handleClick);
    });
  } else {
    init();
    document.addEventListener('click', handleClick);
  }
})();