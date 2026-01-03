/**
 * 启信宝自动填充功能
 * 一个可复用的企业信息自动填充组件
 * 
 * 使用方法：
 * ```javascript
 * const autofill = new QixinbaoAutofill({
 *     nameInputSelector: '[name="name"]',
 *     creditCodeInputSelector: '[name="unified_credit_code"]',
 *     dropdownId: 'companyDropdown',
 *     // ... 其他配置
 * });
 * autofill.init();
 * ```
 */

(function(window) {
    'use strict';

    /**
     * 工具函数：HTML转义，防止XSS攻击
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 工具函数：获取Cookie
     */
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

    /**
     * 启信宝自动填充类
     */
    class QixinbaoAutofill {
        constructor(options = {}) {
            // 默认配置
            this.config = {
                // 输入框选择器
                nameInputSelector: '[name="name"]',
                creditCodeInputSelector: '[name="unified_credit_code"]',
                
                // 下拉框ID
                dropdownId: 'companyDropdown',
                
                // API端点
                searchApiUrl: '/api/customer/search-company/',
                detailApiUrl: '/api/customer/get-company-detail/',
                executionApiUrl: '/api/customer/get-execution-records/',
                
                // 其他字段选择器（用于自动填充）
                fieldSelectors: {
                    legalRepresentative: '[name="legal_representative"]',
                    establishedDate: '[name="established_date"]',
                    registeredCapital: '[name="registered_capital"]',
                    companyPhone: '[name="company_phone"]',
                    companyEmail: '[name="company_email"]',
                    companyAddress: '[name="company_address"]'
                },
                
                // 被执行信息相关元素ID
                executionSectionId: 'executionSection',
                executionTableContainerId: 'executionTableContainer',
                executionCountBadgeId: 'executionCountBadge',
                
                // 搜索延迟时间（毫秒）
                searchDelay: 500,
                
                // 最小搜索字符数
                minSearchLength: 2,
                
                // 是否自动填充详细信息
                autoFillDetails: true,
                
                // 是否自动查询被执行信息
                autoQueryExecution: true,
                
                // 是否显示成功提示
                showSuccessAlert: true,
                
                // 调试模式
                debug: true  // 启用调试模式，便于排查API调用问题
            };

            // 合并用户配置
            Object.assign(this.config, options);

            // DOM元素引用
            this.elements = {
                nameInput: null,
                creditCodeInput: null,
                dropdown: null
            };

            // 状态变量
            this.searchTimeout = null;
            this.scrollTimeout = null;
            this.searchResults = [];
        }

        /**
         * 初始化组件
         */
        init() {
            if (this.config.debug) {
                console.log('🚀 启信宝自动填充功能初始化开始...', this.config);
            }

            // 查找DOM元素
            this._findElements();

            // 检查必需元素
            if (!this._validateElements()) {
                return false;
            }

            // 绑定事件
            this._bindEvents();

            if (this.config.debug) {
                console.log('✅ 启信宝自动填充功能初始化完成');
            }

            return true;
        }

        /**
         * 查找DOM元素
         */
        _findElements() {
            // 尝试多种方式查找名称输入框
            this.elements.nameInput = document.querySelector(this.config.nameInputSelector);
            if (!this.elements.nameInput) {
                this.elements.nameInput = document.querySelector('input[type="text"][id*="name"]');
            }
            if (!this.elements.nameInput) {
                this.elements.nameInput = document.querySelector('input[type="text"][id*="Name"]');
            }

            // 查找其他元素
            this.elements.creditCodeInput = document.querySelector(this.config.creditCodeInputSelector);
            this.elements.dropdown = document.getElementById(this.config.dropdownId);

            if (this.config.debug) {
                console.log('📝 元素查找结果:', {
                    nameInput: this.elements.nameInput ? '✓ 找到' : '✗ 未找到',
                    creditCodeInput: this.elements.creditCodeInput ? '✓ 找到' : '✗ 未找到',
                    dropdown: this.elements.dropdown ? '✓ 找到' : '✗ 未找到'
                });
            }
        }

        /**
         * 验证必需元素是否存在
         */
        _validateElements() {
            if (!this.elements.nameInput) {
                if (this.config.debug) {
                    console.error('❌ 无法找到名称输入框！选择器:', this.config.nameInputSelector);
                }
                return false;
            }

            if (!this.elements.dropdown) {
                if (this.config.debug) {
                    console.error('❌ 无法找到下拉框元素！ID:', this.config.dropdownId);
                }
                return false;
            }

            return true;
        }

        /**
         * 绑定事件监听器
         */
        _bindEvents() {
            // 输入框输入事件
            this.elements.nameInput.addEventListener('input', (e) => {
                this._handleInput(e);
            });

            // 输入框失去焦点事件
            this.elements.nameInput.addEventListener('blur', (e) => {
                this._handleBlur(e);
            });

            // 点击外部关闭下拉框
            document.addEventListener('click', (e) => {
                this._handleDocumentClick(e);
            });

            // 窗口滚动时更新下拉框位置
            window.addEventListener('scroll', () => {
                this._handleScroll();
            }, true);

            // 页面卸载时清理定时器
            window.addEventListener('beforeunload', () => {
                this._cleanup();
            });

            if (this.config.debug) {
                console.log('✅ 事件监听器已绑定');
            }
        }

        /**
         * 处理输入事件
         */
        _handleInput(e) {
            const keyword = this.elements.nameInput.value.trim();

            if (this.config.debug) {
                console.log('📝 输入事件触发，当前值:', keyword, '长度:', keyword.length);
            }

            // 至少需要N个字符才触发搜索
            if (keyword.length < this.config.minSearchLength) {
                if (this.config.debug) {
                    console.log(`⏸️ 字符数不足，需要至少${this.config.minSearchLength}个字符，当前: ${keyword.length}`);
                }
                this._hideDropdown();
                return;
            }

            // 清除之前的搜索定时器
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
                if (this.config.debug) {
                    console.log('🔄 清除之前的搜索定时器');
                }
            }

            // 延迟搜索
            if (this.config.debug) {
                console.log(`⏱️ 将在 ${this.config.searchDelay}ms 后开始搜索`);
            }
            this.searchTimeout = setTimeout(() => {
                if (this.config.debug) {
                    console.log('🚀 开始执行搜索，关键词:', keyword);
                }
                this._searchCompany(keyword);
            }, this.config.searchDelay);
        }

        /**
         * 处理输入框失去焦点
         */
        _handleBlur(e) {
            // 延迟执行，以便点击下拉项时不会立即关闭
            setTimeout(() => {
                if (!this.elements.dropdown.contains(document.activeElement)) {
                    this._hideDropdown();
                }
            }, 200);
        }

        /**
         * 处理文档点击事件
         */
        _handleDocumentClick(e) {
            if (!this.elements.dropdown.contains(e.target) &&
                e.target !== this.elements.nameInput &&
                !this.elements.nameInput.contains(e.target)) {
                this._hideDropdown();
            }
        }

        /**
         * 处理窗口滚动事件
         */
        _handleScroll() {
            if (this.elements.dropdown.classList.contains('show') &&
                this.elements.dropdown.style.display !== 'none') {
                // 防抖处理
                if (this.scrollTimeout) {
                    clearTimeout(this.scrollTimeout);
                }
                this.scrollTimeout = setTimeout(() => {
                    this._updateDropdownPosition();
                }, 50);
            }
        }

        /**
         * 搜索企业
         */
        _searchCompany(keyword) {
            if (this.config.debug) {
                console.log('🔍 开始搜索:', keyword);
            }

            // 显示加载状态
            this._showLoading();

            // 构建API URL
            const url = `${this.config.searchApiUrl}?keyword=${encodeURIComponent(keyword)}&match_type=ename`;

            // 发送请求
            if (this.config.debug) {
                console.log('🌐 发送API请求:', url);
            }
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (this.config.debug) {
                    console.log('📥 API响应状态:', response.status, response.statusText);
                }
                
                if (!response.ok) {
                    // 尝试获取错误信息
                    return response.text().then(text => {
                        try {
                            const errorData = JSON.parse(text);
                            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
                        } catch (e) {
                            throw new Error(`HTTP error! status: ${response.status}, message: ${text || response.statusText}`);
                        }
                    });
                }
                return response.json();
            })
            .then(data => {
                if (this.config.debug) {
                    console.log('📦 API响应数据:', data);
                }
                
                if (!data || !data.success) {
                    const errorMsg = data ? (data.message || '未知错误') : '响应数据为空';
                    if (this.config.debug) {
                        console.error('❌ API返回错误:', errorMsg);
                    }
                    this._showError(errorMsg);
                    return;
                }

                const items = data.data && data.data.items ? data.data.items : (data.data && Array.isArray(data.data) ? data.data : []);

                if (items.length > 0) {
                    this.searchResults = items;
                    this._renderDropdown(items);
                } else {
                    this._showMessage('未找到相关企业');
                }
            })
            .catch(error => {
                if (this.config.debug) {
                    console.error('❌ 搜索异常:', error);
                }
                this._showError('搜索失败：' + error.message);
            });
        }

        /**
         * 显示加载状态
         */
        _showLoading() {
            this.elements.dropdown.innerHTML = '<div class="autocomplete-item"><div class="text-center text-muted">搜索中...</div></div>';
            this._showDropdown();
        }

        /**
         * 显示错误信息
         */
        _showError(message) {
            this.elements.dropdown.innerHTML = `<div class="autocomplete-item"><div class="text-center text-muted">${escapeHtml(message)}</div></div>`;
            this._showDropdown();
        }

        /**
         * 显示消息
         */
        _showMessage(message) {
            this.elements.dropdown.innerHTML = `<div class="autocomplete-item"><div class="text-center text-muted">${escapeHtml(message)}</div></div>`;
            this._showDropdown();
        }

        /**
         * 显示下拉框
         */
        _showDropdown() {
            this._updateDropdownPosition();
            this.elements.dropdown.style.display = 'block';
            this.elements.dropdown.style.visibility = 'visible';
            this.elements.dropdown.style.opacity = '1';
            this.elements.dropdown.style.zIndex = '9999';
            this.elements.dropdown.classList.add('show');
        }

        /**
         * 隐藏下拉框
         */
        _hideDropdown() {
            this.elements.dropdown.classList.remove('show');
            this.elements.dropdown.style.display = 'none';
        }

        /**
         * 更新下拉框位置
         */
        _updateDropdownPosition() {
            const inputRect = this.elements.nameInput.getBoundingClientRect();
            const dropdownParent = this.elements.dropdown.parentElement;
            const parentRect = dropdownParent.getBoundingClientRect();

            const topPosition = inputRect.bottom - parentRect.top + 4;
            const leftPosition = inputRect.left - parentRect.left;
            const width = inputRect.width;

            this.elements.dropdown.style.position = 'absolute';
            this.elements.dropdown.style.top = topPosition + 'px';
            this.elements.dropdown.style.left = leftPosition + 'px';
            this.elements.dropdown.style.width = width + 'px';
        }

        /**
         * 渲染下拉列表
         */
        _renderDropdown(results) {
            this.elements.dropdown.innerHTML = '';

            results.forEach((item) => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';

                // 安全地处理文本内容，防止XSS
                const companyName = escapeHtml(item.name || '—');
                const creditCode = escapeHtml(item.creditCode || item.credit_no || item.credit_code || '—');
                const legalRep = escapeHtml(item.legalRepresentative || item.oper_name || item.operName || '—');

                div.innerHTML = `
                    <div class="autocomplete-item-name">${companyName}</div>
                    <div class="autocomplete-item-meta">
                        <span>统一信用代码: ${creditCode}</span>
                        <span>法定代表人: ${legalRep}</span>
                    </div>
                `;
                div.addEventListener('click', () => {
                    this._selectCompany(item);
                });
                this.elements.dropdown.appendChild(div);
            });

            this._showDropdown();
        }

        /**
         * 选择企业
         */
        _selectCompany(company) {
            if (this.config.debug) {
                console.log('✅ 选择公司:', company);
            }

            // 填充基本信息
            this.elements.nameInput.value = company.name || '';

            const creditCode = company.credit_no || company.creditCode || company.credit_code || '';
            if (this.elements.creditCodeInput && creditCode) {
                this.elements.creditCodeInput.value = creditCode;
            }

            // 填充从搜索结果直接获取的信息
            this._fillBasicInfo(company);

            // 隐藏下拉框
            this._hideDropdown();

            // 获取详细信息和失信信息
            if (this.config.autoFillDetails && (company.id || creditCode || company.name)) {
                this._fetchCompanyDetail(company.id, creditCode, company.name);
            }

            if (this.config.autoQueryExecution && (creditCode || company.name)) {
                this._fetchExecutionRecords(creditCode, company.name);
            }
        }

        /**
         * 填充基本信息
         */
        _fillBasicInfo(company) {
            // 填充法定代表人
            const legalRepInput = document.querySelector(this.config.fieldSelectors.legalRepresentative);
            if (legalRepInput && company.oper_name) {
                legalRepInput.value = company.oper_name;
            }

            // 填充成立日期
            const establishedDateInput = document.querySelector(this.config.fieldSelectors.establishedDate);
            if (establishedDateInput && company.start_date) {
                establishedDateInput.value = company.start_date.split(' ')[0].split('T')[0];
            }
        }

        /**
         * 获取企业详细信息
         */
        _fetchCompanyDetail(companyId, creditCode, companyName) {
            if (!companyId && !creditCode && !companyName) {
                return;
            }

            const params = new URLSearchParams();
            if (companyId) params.append('company_id', companyId);
            if (creditCode) params.append('credit_code', creditCode);
            if (companyName) params.append('company_name', companyName);

            const url = `${this.config.detailApiUrl}?${params.toString()}`;

            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data) {
                    this._fillCompanyDetails(data.data);
                }
            })
            .catch(error => {
                if (this.config.debug) {
                    console.error('获取企业详情错误:', error);
                }
            });
        }

        /**
         * 填充企业详细信息
         */
        _fillCompanyDetails(details) {
            let filledCount = 0;

            // 填充法定代表人（如果还没有填充）
            const legalRepInput = document.querySelector(this.config.fieldSelectors.legalRepresentative);
            if (legalRepInput && !legalRepInput.value) {
                const legalRep = details.legal_representative || details.oper_name || details.operName || '';
                if (legalRep) {
                    legalRepInput.value = legalRep;
                    filledCount++;
                }
            }

            // 填充成立日期（如果还没有填充）
            const establishedDateInput = document.querySelector(this.config.fieldSelectors.establishedDate);
            if (establishedDateInput && !establishedDateInput.value) {
                const date = details.established_date || details.start_date || details.startDate || '';
                if (date) {
                    establishedDateInput.value = date.split(' ')[0].split('T')[0];
                    filledCount++;
                }
            }

            // 填充注册资本
            const registeredCapitalInput = document.querySelector(this.config.fieldSelectors.registeredCapital);
            if (registeredCapitalInput) {
                if (details.reg_capital_value !== undefined && details.reg_capital_value !== null) {
                    registeredCapitalInput.value = parseFloat(details.reg_capital_value).toFixed(2);
                    filledCount++;
                } else if (details.reg_capital) {
                    let capital = parseFloat(details.reg_capital) || 0;
                    if (capital > 10000) {
                        capital = capital / 10000;
                    }
                    registeredCapitalInput.value = capital.toFixed(2);
                    filledCount++;
                }
            }

            // 填充联系电话
            const companyPhoneInput = document.querySelector(this.config.fieldSelectors.companyPhone);
            if (companyPhoneInput && details.phone) {
                companyPhoneInput.value = details.phone;
                filledCount++;
            }

            // 填充邮箱
            const companyEmailInput = document.querySelector(this.config.fieldSelectors.companyEmail);
            if (companyEmailInput && details.email) {
                companyEmailInput.value = details.email;
                filledCount++;
            }

            // 填充地址
            const companyAddressInput = document.querySelector(this.config.fieldSelectors.companyAddress);
            if (companyAddressInput && details.address) {
                companyAddressInput.value = details.address;
                filledCount++;
            }

            // 显示成功提示
            if (this.config.showSuccessAlert && filledCount > 0) {
                this._showSuccessAlert(filledCount);
            }
        }

        /**
         * 显示成功提示
         */
        _showSuccessAlert(filledCount) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show mt-2';
            alertDiv.innerHTML = `
                <strong>成功！</strong> 已自动填充 ${filledCount} 个企业信息字段。
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            this.elements.nameInput.parentElement.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        }

        /**
         * 获取被执行信息
         */
        _fetchExecutionRecords(creditCode, companyName) {
            const executionSection = document.getElementById(this.config.executionSectionId);
            const executionTableContainer = document.getElementById(this.config.executionTableContainerId);
            const executionCountBadge = document.getElementById(this.config.executionCountBadgeId);

            if (!executionSection || !executionTableContainer) {
                return;
            }

            // 显示加载状态
            executionSection.style.display = 'block';
            executionTableContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div> 正在查询被执行信息...</div>';
            if (executionCountBadge) {
                executionCountBadge.innerHTML = '';
            }

            const params = new URLSearchParams();
            if (creditCode) params.append('credit_code', creditCode);
            if (companyName) params.append('company_name', companyName);

            const url = `${this.config.executionApiUrl}?${params.toString()}`;

            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data) {
                    const records = data.data.records || [];
                    const count = records.length;
                    const totalAmount = data.data.total_amount || '0';

                    // 更新徽章
                    if (executionCountBadge) {
                        if (count > 0) {
                            let badgeHtml = `<span class="badge bg-danger ms-2">${count} 条记录</span>`;
                            if (totalAmount && parseFloat(totalAmount) > 0) {
                                badgeHtml += `<span class="badge bg-warning ms-2">执行总金额: ¥${parseFloat(totalAmount).toFixed(2)}</span>`;
                            }
                            executionCountBadge.innerHTML = badgeHtml;
                        } else {
                            executionCountBadge.innerHTML = `<span class="badge bg-success ms-2">无记录</span>`;
                        }
                    }

                    // 更新表格
                    if (count > 0) {
                        this._renderExecutionTable(records, executionTableContainer);
                    } else {
                        executionTableContainer.innerHTML = '<div class="alert alert-info mb-0"><i class="bi bi-info-circle me-2"></i>暂无被执行记录</div>';
                    }
                } else {
                    const errorMsg = data ? (data.message || '查询失败') : '响应数据为空';
                    executionTableContainer.innerHTML = `<div class="alert alert-warning mb-0"><i class="bi bi-exclamation-triangle me-2"></i>查询被执行信息失败: ${errorMsg}</div>`;
                }
            })
            .catch(error => {
                executionTableContainer.innerHTML = `<div class="alert alert-warning mb-0"><i class="bi bi-exclamation-triangle me-2"></i>查询被执行信息失败: ${error.message || '网络错误'}</div>`;
            });
        }

        /**
         * 渲染被执行记录表格
         */
        _renderExecutionTable(records, container) {
            let tableHtml = `
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>案号</th>
                                <th>执行状态</th>
                                <th>执行法院</th>
                                <th>立案日期</th>
                                <th>执行金额</th>
                            </tr>
                        </thead>
                        <tbody>`;

            records.forEach(record => {
                const caseNumber = escapeHtml(record.case_number || '未填写');
                const executionStatus = escapeHtml(record.execution_status_display || record.execution_status || '未填写');
                const executionCourt = escapeHtml(record.execution_court || '未填写');
                const filingDate = escapeHtml(record.filing_date || '未填写');
                const executionAmount = record.execution_amount ? parseFloat(record.execution_amount).toFixed(2) : '0.00';

                tableHtml += `
                    <tr>
                        <td>${caseNumber}</td>
                        <td>${executionStatus}</td>
                        <td>${executionCourt}</td>
                        <td>${filingDate}</td>
                        <td>¥${executionAmount}</td>
                    </tr>`;
            });

            tableHtml += `
                        </tbody>
                    </table>
                </div>`;
            container.innerHTML = tableHtml;
        }

        /**
         * 清理资源
         */
        _cleanup() {
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = null;
            }
            if (this.scrollTimeout) {
                clearTimeout(this.scrollTimeout);
                this.scrollTimeout = null;
            }
        }

        /**
         * 销毁组件
         */
        destroy() {
            this._cleanup();
            // 移除事件监听器等清理工作
        }
    }

    // 导出到全局作用域
    window.QixinbaoAutofill = QixinbaoAutofill;

})(window);

