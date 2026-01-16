// 计划表单日期自动计算脚本
// 根据计划周期自动计算结束日期

(function() {
    'use strict';
    
    /**
     * 根据开始日期和计划周期计算结束日期
     * @param {string} startDateStr - 开始日期字符串 (YYYY-MM-DD)
     * @param {string} planPeriod - 计划周期 ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
     * @returns {string} 结束日期字符串 (YYYY-MM-DD)
     */
    function calculateEndDate(startDateStr, planPeriod) {
        if (!startDateStr || !planPeriod) {
            return '';
        }
        
        const startDate = new Date(startDateStr);
        if (isNaN(startDate.getTime())) {
            return '';
        }
        
        let endDate = new Date(startDate);
        
        switch(planPeriod) {
            case 'yearly':
                // 年计划：开始日期后1年减1天
                endDate.setFullYear(endDate.getFullYear() + 1);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case 'quarterly':
                // 季度计划：开始日期后3个月减1天
                endDate.setMonth(endDate.getMonth() + 3);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case 'monthly':
                // 月计划：开始日期后1个月减1天
                endDate.setMonth(endDate.getMonth() + 1);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case 'weekly':
                // 周计划：开始日期后7天减1天（即6天后）
                endDate.setDate(endDate.getDate() + 6);
                break;
            case 'daily':
                // 日计划：开始日期当天（即结束日期等于开始日期）
                // endDate 保持不变
                break;
            default:
                return '';
        }
        
        // 格式化为 YYYY-MM-DD
        const year = endDate.getFullYear();
        const month = String(endDate.getMonth() + 1).padStart(2, '0');
        const day = String(endDate.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    }
    
    /**
     * 更新结束日期
     */
    function updateEndDate() {
        const startDateInput = document.getElementById('id_start_time');
        const endDateInput = document.getElementById('id_end_time');
        const planPeriodSelect = document.getElementById('id_plan_period');
        
        if (!startDateInput || !endDateInput || !planPeriodSelect) {
            return;
        }
        
        const startDate = startDateInput.value;
        const planPeriod = planPeriodSelect.value;
        
        if (startDate && planPeriod) {
            const endDate = calculateEndDate(startDate, planPeriod);
            if (endDate) {
                endDateInput.value = endDate;
            }
        }
    }
    
    /**
     * 初始化
     */
    function init() {
        const startDateInput = document.getElementById('id_start_time');
        const planPeriodSelect = document.getElementById('id_plan_period');
        
        if (!startDateInput || !planPeriodSelect) {
            return;
        }
        
        // 监听开始日期和计划周期的变化
        startDateInput.addEventListener('change', updateEndDate);
        planPeriodSelect.addEventListener('change', updateEndDate);
        
        // 页面加载时，如果开始日期和计划周期都有值，自动计算结束日期
        if (startDateInput.value && planPeriodSelect.value) {
            updateEndDate();
        } else if (!startDateInput.value) {
            // 如果开始日期为空（新建时），设置为今天
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            startDateInput.value = `${year}-${month}-${day}`;
            
            // 设置开始日期后，如果计划周期已选择，自动计算结束日期
            if (planPeriodSelect.value) {
                updateEndDate();
            }
        }
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
