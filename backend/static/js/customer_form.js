/**
 * 客户表单通用功能
 * 支持弹窗表单和独立页面表单
 * 功能包括：客户名称自动搜索、查重、企业信息自动填充
 */

(function() {
    'use strict';

    // 工具函数：获取Cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 工具函数：转义HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 初始化客户表单功能
    function initCustomerForm(prefix = '') {
        // 根据前缀确定元素ID或选择器
        let customerNameInput, creditCodeInput;
        const dropdownId = prefix ? `modalCompanyDropdown` : `companyDropdown`;
        const nameStatusId = prefix ? `modalNameDuplicateStatus` : `nameDuplicateStatus`;
        const creditCodeStatusId = prefix ? `modalCreditCodeDuplicateStatus` : `creditCodeDuplicateStatus`;

        // 优先通过ID查找，如果找不到则通过name属性查找（兼容Django表单）
        if (prefix) {
            customerNameInput = document.getElementById(`modalCustomerName`) || document.querySelector('[name="name"]');
            creditCodeInput = document.getElementById(`modalUnifiedCreditCode`) || document.querySelector('[name="unified_credit_code"]');
        } else {
            customerNameInput = document.getElementById(`customerName`) || document.getElementById(`id_name`) || document.querySelector('[name="name"]');
            creditCodeInput = document.getElementById(`unifiedCreditCode`) || document.getElementById(`id_unified_credit_code`) || document.querySelector('[name="unified_credit_code"]');
        }
        
        const companyDropdown = document.getElementById(dropdownId);
        const nameDuplicateStatus = document.getElementById(nameStatusId);
        const creditCodeDuplicateStatus = document.getElementById(creditCodeStatusId);

        // 检查必要元素是否存在
        if (!customerNameInput || !companyDropdown) {
            // 静默跳过，不输出日志（弹窗可能还未显示）
            return;
        }
        
        // 标记已初始化，避免重复初始化
        if (customerNameInput.dataset.duplicateCheckInitialized === 'true') {
            return;
        }
        customerNameInput.dataset.duplicateCheckInitialized = 'true';

        // 查重相关变量
        let duplicateCheckTimeout = null;
        let hasDuplicate = false;

        // 客户名称输入时，如果同时有统一信用代码，实时检查重复
        customerNameInput.addEventListener('input', function() {
            const keyword = this.value.trim();
            
            // 清除查重状态
            if (nameDuplicateStatus) {
                nameDuplicateStatus.textContent = '';
                nameDuplicateStatus.className = 'duplicate-check-status';
            }
            hasDuplicate = false;
            
            // 如果同时有统一信用代码（18位），实时检查重复
            if (creditCodeInput) {
                const code = creditCodeInput.value.trim();
                if (code && code.length === 18 && keyword.length >= 2) {
                    // 清除之前的检查
                    if (duplicateCheckTimeout) {
                        clearTimeout(duplicateCheckTimeout);
                    }
                    duplicateCheckTimeout = setTimeout(function() {
                        checkDuplicate('both', keyword, code);
                    }, 500);
                }
            }
        });

        // 客户名称失焦时检查重复
        customerNameInput.addEventListener('blur', function() {
            const name = this.value.trim();
            if (name && name.length >= 2) {
                // 如果同时有统一信用代码，一起检查
                const code = creditCodeInput ? creditCodeInput.value.trim() : '';
                if (code && code.length === 18) {
                    checkDuplicate('both', name, code);
                } else {
                    checkDuplicate('name', name, null);
                }
            }
        });

        // 统一社会信用代码输入时检查重复
        if (creditCodeInput) {
            creditCodeInput.addEventListener('input', function() {
                const code = this.value.trim();
                // 清除查重状态
                if (creditCodeDuplicateStatus) {
                    creditCodeDuplicateStatus.textContent = '';
                    creditCodeDuplicateStatus.className = 'duplicate-check-status';
                }
                hasDuplicate = false;
                
                // 如果输入了18位统一社会信用代码，检查重复
                if (code.length === 18) {
                    // 防抖：延迟500ms后检查
                    if (duplicateCheckTimeout) {
                        clearTimeout(duplicateCheckTimeout);
                    }
                    duplicateCheckTimeout = setTimeout(function() {
                        // 如果同时有客户名称，一起检查
                        const name = customerNameInput ? customerNameInput.value.trim() : '';
                        if (name && name.length >= 2) {
                            checkDuplicate('both', name, code);
                        } else {
                            checkDuplicate('credit_code', null, code);
                        }
                    }, 500);
                }
            });

            // 统一社会信用代码失焦时检查重复
            creditCodeInput.addEventListener('blur', function() {
                const code = this.value.trim();
                if (code && code.length === 18) {
                    // 如果同时有客户名称，一起检查
                    const name = customerNameInput ? customerNameInput.value.trim() : '';
                    if (name && name.length >= 2) {
                        checkDuplicate('both', name, code);
                    } else {
                        checkDuplicate('credit_code', null, code);
                    }
                }
            });
        }

        // 监听输入框值的变化（包括QixinbaoAutofill自动填充）
        // 使用input事件和定时检查相结合的方式
        let lastCheckedName = '';
        let lastCheckedCode = '';
        
        // 定时检查输入框值的变化（用于检测自动填充）
        setInterval(function() {
            const currentName = customerNameInput ? customerNameInput.value.trim() : '';
            const currentCode = creditCodeInput ? creditCodeInput.value.trim() : '';
            
            // 如果值发生了变化，触发重复检查
            if (currentName !== lastCheckedName || currentCode !== lastCheckedCode) {
                if (currentName && currentName.length >= 2) {
                    if (currentCode && currentCode.length === 18) {
                        checkDuplicate('both', currentName, currentCode);
                    } else if (currentName !== lastCheckedName) {
                        // 只有名称变化时才检查名称
                        checkDuplicate('name', currentName, null);
                    }
                } else if (currentCode && currentCode.length === 18 && currentCode !== lastCheckedCode) {
                    // 只有统一信用代码变化时才检查
                    checkDuplicate('credit_code', null, currentCode);
                }
                
                lastCheckedName = currentName;
                lastCheckedCode = currentCode;
            }
        }, 500); // 每500ms检查一次
        
        // 检查客户是否重复
        function checkDuplicate(type, name, creditCode) {
            const params = new URLSearchParams();
            if (name) {
                params.append('name', name);
            }
            if (creditCode) {
                params.append('unified_credit_code', creditCode);
            }
            
            if (!name && !creditCode) {
                return;
            }
            
            const url = `/api/customer/check-duplicate/?${params.toString()}`;
            
            // 确定要更新的状态元素
            let statusElements = [];
            if (type === 'both') {
                // 同时检查两者时，更新两个状态元素
                if (nameDuplicateStatus) statusElements.push(nameDuplicateStatus);
                if (creditCodeDuplicateStatus) statusElements.push(creditCodeDuplicateStatus);
            } else {
                // 单独检查时，只更新对应的状态元素
                const statusElement = type === 'name' ? nameDuplicateStatus : creditCodeDuplicateStatus;
                if (statusElement) statusElements.push(statusElement);
            }
            
            // 显示检查状态
            statusElements.forEach(el => {
                el.className = 'duplicate-check-status checking';
                el.textContent = '检查中...';
            });
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                statusElements.forEach(el => {
                    if (data.success && data.is_duplicate) {
                        hasDuplicate = true;
                        el.className = 'duplicate-check-status error';
                        let message = `<i class="bi bi-exclamation-triangle"></i> ${data.message}`;
                        
                        // 如果存在已存在的客户，显示链接
                        if (data.existing_client) {
                            const clientUrl = `/customers/customers/${data.existing_client.id}/`;
                            message += ` <a href="${clientUrl}" target="_blank" class="text-decoration-underline">查看详情</a>`;
                        }
                        el.innerHTML = message;
                    } else {
                        hasDuplicate = false;
                        el.className = 'duplicate-check-status success';
                        el.textContent = '✓ 客户信息未重复，可以创建';
                    }
                });
            })
            .catch(error => {
                console.error('查重失败:', error);
                statusElements.forEach(el => {
                    el.className = 'duplicate-check-status error';
                    el.textContent = '查重失败，请稍后重试';
                });
            });
        }

    }

    // 页面加载完成后初始化
    function initializeForms() {
        // 初始化独立页面表单
        initCustomerForm('');
    }

    // 弹窗显示时初始化（Bootstrap Modal事件）
    function initializeModalForm() {
        // 延迟执行，确保弹窗DOM完全渲染
        setTimeout(function() {
            initCustomerForm('modal');
        }, 100);
    }

    // DOM加载完成后初始化独立页面表单
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeForms();
        });
    } else {
        initializeForms();
    }

    // 监听弹窗显示事件（Bootstrap Modal）
    document.addEventListener('DOMContentLoaded', function() {
        const createCustomerModal = document.getElementById('createCustomerModal');
        if (createCustomerModal) {
            // 使用 Bootstrap 5 的事件监听
            createCustomerModal.addEventListener('shown.bs.modal', function() {
                initializeModalForm();
            });
            
            // 兼容 Bootstrap 4 的事件名称
            createCustomerModal.addEventListener('shown', function() {
                initializeModalForm();
            });
        }
        
        // 也监听所有可能的弹窗（动态创建的弹窗）
        document.addEventListener('shown.bs.modal', function(e) {
            if (e.target.id === 'createCustomerModal') {
                initializeModalForm();
            }
        });
    });
})();

