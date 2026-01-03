/**
 * Bootstrap 5 模态框合规性检查工具
 * 独立工具文件，用于检查模态框是否符合 Bootstrap 5 标准
 */

(function() {
    'use strict';
    
    const DEBUG = window.DEBUG_MODE !== false;
    const log = {
        debug: DEBUG ? console.log.bind(console) : () => {},
        warn: DEBUG ? console.warn.bind(console) : () => {},
        error: console.error.bind(console)
    };
    
    function checkModalCompliance(modalId) {
        log.debug('='.repeat(60));
        log.debug('Bootstrap 5 模态框合规性检查:', modalId);
        log.debug('='.repeat(60));
        
        const modal = document.getElementById(modalId);
        if (!modal) {
            log.error('❌ 模态框元素未找到:', modalId);
            return false;
        }
        
        let isCompliant = true;
        const issues = [];
        
        // 1. 检查模态框容器
        log.debug('\n1. 检查模态框容器...');
        if (!modal.classList.contains('modal')) {
            issues.push('❌ 缺少 class="modal"');
            isCompliant = false;
        } else {
            log.debug('✅ 有 class="modal"');
        }
        
        if (!modal.hasAttribute('id')) {
            issues.push('❌ 缺少 id 属性');
            isCompliant = false;
        } else {
            log.debug('✅ 有 id 属性:', modal.id);
        }
        
        if (modal.getAttribute('tabindex') !== '-1') {
            issues.push('❌ tabindex 应该是 "-1"，当前:', modal.getAttribute('tabindex'));
            isCompliant = false;
        } else {
            log.debug('✅ tabindex="-1"');
        }
        
        const ariaLabelledby = modal.getAttribute('aria-labelledby');
        if (!ariaLabelledby) {
            issues.push('❌ 缺少 aria-labelledby 属性');
            isCompliant = false;
        } else {
            log.debug('✅ aria-labelledby:', ariaLabelledby);
            const titleElement = document.getElementById(ariaLabelledby);
            if (!titleElement) {
                issues.push('❌ aria-labelledby 指向的元素不存在:', ariaLabelledby);
                isCompliant = false;
            } else {
                log.debug('✅ 标题元素存在');
            }
        }
        
        // 2. 检查 modal-dialog
        log.debug('\n2. 检查 modal-dialog...');
        const dialog = modal.querySelector('.modal-dialog');
        if (!dialog) {
            issues.push('❌ 缺少 .modal-dialog 元素');
            isCompliant = false;
        } else {
            log.debug('✅ 找到 .modal-dialog');
        }
        
        // 3. 检查 modal-content
        log.debug('\n3. 检查 modal-content...');
        const content = modal.querySelector('.modal-content');
        if (!content) {
            issues.push('❌ 缺少 .modal-content 元素');
            isCompliant = false;
        } else {
            log.debug('✅ 找到 .modal-content');
        }
        
        // 4. 检查 modal-header
        log.debug('\n4. 检查 modal-header...');
        const header = modal.querySelector('.modal-header');
        if (!header) {
            issues.push('❌ 缺少 .modal-header 元素');
            isCompliant = false;
        } else {
            log.debug('✅ 找到 .modal-header');
            
            const title = header.querySelector('.modal-title');
            if (!title) {
                issues.push('❌ 缺少 .modal-title 元素');
                isCompliant = false;
            } else {
                log.debug('✅ 找到 .modal-title');
            }
            
            const closeBtn = header.querySelector('.btn-close');
            if (!closeBtn) {
                issues.push('❌ 缺少 .btn-close 关闭按钮');
                isCompliant = false;
            } else {
                log.debug('✅ 找到 .btn-close');
                if (closeBtn.getAttribute('data-bs-dismiss') !== 'modal') {
                    issues.push('❌ .btn-close 缺少 data-bs-dismiss="modal" 属性');
                    isCompliant = false;
                } else {
                    log.debug('✅ .btn-close 有 data-bs-dismiss="modal"');
                }
            }
        }
        
        // 5. 检查 modal-body
        log.debug('\n5. 检查 modal-body...');
        const body = modal.querySelector('.modal-body');
        if (!body) {
            issues.push('❌ 缺少 .modal-body 元素');
            isCompliant = false;
        } else {
            log.debug('✅ 找到 .modal-body');
        }
        
        // 6. 检查 Bootstrap 实例
        log.debug('\n6. 检查 Bootstrap Modal 实例...');
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                log.debug('✅ 找到 Bootstrap Modal 实例');
            } else {
                log.debug('⚠️  未找到 Bootstrap Modal 实例（可能需要初始化）');
            }
        } else {
            log.debug('❌ Bootstrap 未加载');
            isCompliant = false;
        }
        
        // 输出总结
        log.debug('\n' + '='.repeat(60));
        if (isCompliant && issues.length === 0) {
            log.debug('✅ 模态框符合 Bootstrap 5 标准！');
        } else {
            log.debug('❌ 发现以下问题：');
            issues.forEach(issue => log.debug('  ', issue));
        }
        log.debug('='.repeat(60));
        
        return isCompliant && issues.length === 0;
    }
    
    // 导出到全局
    window.checkBootstrap5ModalCompliance = checkModalCompliance;
    
    // 自动检查（延迟执行，确保DOM已加载）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                if (document.getElementById('filterFieldsSettingsModal')) {
                    log.debug('自动检查 filterFieldsSettingsModal 是否符合 Bootstrap 5 标准...');
                    checkModalCompliance('filterFieldsSettingsModal');
                }
            }, 2000);
        });
    } else {
        setTimeout(() => {
            if (document.getElementById('filterFieldsSettingsModal')) {
                log.debug('自动检查 filterFieldsSettingsModal 是否符合 Bootstrap 5 标准...');
                checkModalCompliance('filterFieldsSettingsModal');
            }
        }, 2000);
    }
})();

