/**
 * 法律风险信息获取器
 * 维海科技信息化管理平台
 * 版本: 1.0
 * 
 * 功能说明：
 * - 根据企业名称或统一社会信用代码自动获取法律风险信息
 * - 自动填充法律风险等级、司法案件数量等信息
 * 
 * 使用方法：
 * 1. 在页面中引入此文件：
 *    <script src="{% static 'js/legal-risk-fetcher.js' %}"></script>
 * 
 * 2. 初始化（自动监听企业名称和统一社会信用代码输入）：
 *    initLegalRiskFetcher({
 *        nameInputSelector: '[name="name"]',
 *        creditCodeInputSelector: '[name="unified_credit_code"]',
 *        initialCompanyName: '{{ client.name|default:"" }}',
 *        initialCreditCode: '{{ client.unified_credit_code|default:"" }}'
 *    });
 */

/**
 * 获取Cookie的工具函数
 * @param {string} name - Cookie名称
 * @returns {string|null} Cookie值
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 获取法律风险信息
 * @param {number|null} companyId - 企业ID
 * @param {string|null} creditCode - 统一社会信用代码
 * @param {string|null} companyName - 企业名称
 */
function fetchLegalRiskInfo(companyId, creditCode, companyName) {
    if (!companyId && !creditCode && !companyName) {
        return;
    }
    
    const params = new URLSearchParams();
    if (companyId) {
        params.append('company_id', companyId);
    }
    if (creditCode) {
        params.append('credit_code', creditCode);
    }
    if (companyName) {
        params.append('company_name', companyName);
    }
    
    const url = `/api/customer/get-legal-risk/?${params.toString()}`;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.data) {
            fillLegalRiskInfo(data.data);
        } else {
            console.warn('获取法律风险信息失败:', data.message || '未知错误');
        }
    })
    .catch(error => {
        console.error('获取法律风险信息异常:', error);
    });
}

/**
 * 填充法律风险信息到表单
 * @param {Object} riskData - 法律风险数据
 */
function fillLegalRiskInfo(riskData) {
    // 更新法律风险等级
    const riskLevelEl = document.getElementById('legalRiskLevel');
    const riskLevelHiddenEl = document.getElementById('legalRiskLevelHidden');
    if (riskLevelEl && riskLevelHiddenEl) {
        const riskLevel = riskData.risk_level || riskData.legal_risk_level || 'unknown';
        const riskLevelLabel = riskData.risk_level_label || 
            (riskLevel === 'low' ? '低风险' :
             riskLevel === 'medium_low' ? '中低风险' :
             riskLevel === 'medium' ? '中风险' :
             riskLevel === 'medium_high' ? '中高风险' :
             riskLevel === 'high' ? '高风险' : '未知');
        
        riskLevelEl.value = riskLevelLabel;
        riskLevelHiddenEl.value = riskLevel;
    }
    
    // 更新司法案件数量
    const litigationEl = document.getElementById('id_litigation_count');
    if (litigationEl && riskData.litigation_count !== undefined) {
        litigationEl.value = riskData.litigation_count || 0;
    }
    
    // 更新被执行人数量
    const executedEl = document.getElementById('id_executed_person_count');
    if (executedEl && riskData.executed_person_count !== undefined) {
        executedEl.value = riskData.executed_person_count || 0;
    }
    
    // 更新终本案件数量
    const finalCaseEl = document.getElementById('id_final_case_count');
    if (finalCaseEl && riskData.final_case_count !== undefined) {
        finalCaseEl.value = riskData.final_case_count || 0;
    }
    
    // 更新限制高消费数量
    const consumptionEl = document.getElementById('id_consumption_limit_count');
    if (consumptionEl && riskData.consumption_limit_count !== undefined) {
        consumptionEl.value = riskData.consumption_limit_count || 0;
    }
}

/**
 * 初始化法律风险信息获取器
 * @param {Object} options - 配置选项
 * @param {string} options.nameInputSelector - 企业名称输入框选择器（默认：'[name="name"]'）
 * @param {string} options.creditCodeInputSelector - 统一社会信用代码输入框选择器（默认：'[name="unified_credit_code"]'）
 * @param {string} options.initialCompanyName - 初始企业名称（用于编辑模式）
 * @param {string} options.initialCreditCode - 初始统一社会信用代码（用于编辑模式）
 * @param {number} options.debounceDelay - 防抖延迟时间（毫秒，默认：500）
 */
function initLegalRiskFetcher(options = {}) {
    const config = {
        nameInputSelector: options.nameInputSelector || '[name="name"]',
        creditCodeInputSelector: options.creditCodeInputSelector || '[name="unified_credit_code"]',
        initialCompanyName: options.initialCompanyName || '',
        initialCreditCode: options.initialCreditCode || '',
        debounceDelay: options.debounceDelay || 500
    };
    
    document.addEventListener('DOMContentLoaded', function() {
        const nameInput = document.querySelector(config.nameInputSelector);
        const creditCodeInput = document.querySelector(config.creditCodeInputSelector);
        
        function checkAndFetchRiskInfo() {
            const companyName = nameInput ? nameInput.value.trim() : '';
            const creditCode = creditCodeInput ? creditCodeInput.value.trim() : '';
            
            // 至少需要企业名称或统一社会信用代码
            if (companyName.length >= 2 || creditCode.length >= 2) {
                fetchLegalRiskInfo(null, creditCode, companyName);
            }
        }
        
        // 监听企业名称输入（延迟，避免频繁请求）
        if (nameInput) {
            let nameTimeout;
            nameInput.addEventListener('input', function() {
                clearTimeout(nameTimeout);
                nameTimeout = setTimeout(checkAndFetchRiskInfo, config.debounceDelay);
            });
        }
        
        // 监听统一社会信用代码输入（延迟）
        if (creditCodeInput) {
            let creditCodeTimeout;
            creditCodeInput.addEventListener('input', function() {
                clearTimeout(creditCodeTimeout);
                creditCodeTimeout = setTimeout(checkAndFetchRiskInfo, config.debounceDelay);
            });
        }
        
        // 如果是编辑模式，页面加载时自动获取
        if (config.initialCompanyName || config.initialCreditCode) {
            setTimeout(() => {
                fetchLegalRiskInfo(null, config.initialCreditCode, config.initialCompanyName);
            }, 1000);
        }
    });
}

// 导出函数（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCookie,
        fetchLegalRiskInfo,
        fillLegalRiskInfo,
        initLegalRiskFetcher
    };
}

