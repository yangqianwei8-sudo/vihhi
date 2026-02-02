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
    // 初始化：localStorage 优先；其次子菜单内有 is-active 或模板已带 is-open（当前页为父级）则展开
    const parents = document.querySelectorAll('[data-sb-parent]');
    parents.forEach((parentEl) => {
      const key = parentEl.getAttribute('data-sb-key') || '';
      const hasActiveChild = !!parentEl.querySelector('.vh-sb__child.is-active');
      const alreadyOpenInTemplate = parentEl.classList.contains('is-open');
      const shouldOpen = (key && openKeys.has(key)) || hasActiveChild || alreadyOpenInTemplate;
      setOpen(parentEl, shouldOpen);
    });
  }

  // 事件委托：在捕获阶段处理，避免被其他脚本或链接拦截
  function handleClick(e) {
    // 如果点击的是子菜单项（.vh-sb__child），不处理折叠逻辑，允许正常跳转
    if (e.target.closest('.vh-sb__child')) {
      return;
    }

    const btn = e.target.closest('[data-sb-toggle]');
    if (!btn) return;

    const parentEl = btn.closest('[data-sb-parent]');
    if (!parentEl) return;

    // 检查点击是否发生在子菜单容器内
    const children = parentEl.querySelector('[data-sb-children]');
    if (children && children.contains(e.target)) {
      return; // 点击在子菜单内，不处理折叠
    }

    e.preventDefault();
    e.stopPropagation();

    const isOpen = parentEl.classList.contains('is-open');
    setOpen(parentEl, !isOpen);
    updateExpandAllButton();
  }

  function expandCollapseAll(expand) {
    const parents = document.querySelectorAll('.vh-sb [data-sb-parent]');
    parents.forEach(function (p) { setOpen(p, expand); });
    updateExpandAllButton();
  }

  function updateExpandAllButton() {
    const btn = document.querySelector('.vh-sb [data-sb-expand-all]');
    if (!btn) return;
    const icon = btn.querySelector('.vh-sb__expandAll-icon');
    const parents = document.querySelectorAll('.vh-sb [data-sb-parent]');
    if (parents.length === 0) {
      btn.style.display = 'none';
      return;
    }
    btn.style.display = '';
    const allOpen = Array.from(parents).every(function (p) { return p.classList.contains('is-open'); });
    btn.classList.toggle('is-collapsed', allOpen);
    btn.title = allOpen ? '收起全部菜单' : '展开全部菜单';
    if (icon) icon.textContent = allOpen ? '\u229F' : '\u229E';  // ⊟ / ⊞
  }

  function handleExpandAllClick(e) {
    const btn = e.target.closest('[data-sb-expand-all]');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const parents = document.querySelectorAll('.vh-sb [data-sb-parent]');
    if (parents.length === 0) return;
    const allOpen = Array.from(parents).every(function (p) { return p.classList.contains('is-open'); });
    expandCollapseAll(!allOpen);
  }

  function attachListener() {
    init();
    updateExpandAllButton();
    // 使用捕获阶段，确保在其它点击处理之前执行，避免“点击无法展开”的问题
    document.addEventListener('click', handleClick, true);
    document.addEventListener('click', handleExpandAllClick, true);
  }

  // 等待 DOM 加载完成
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachListener);
  } else {
    attachListener();
  }
})();