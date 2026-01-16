// 战略目标表单日期自动计算脚本
// 根据目标周期自动计算结束日期

(function() {
    'use strict';
    
    /**
     * 根据开始日期和目标周期计算结束日期
     * @param {string} startDateStr - 开始日期字符串 (YYYY-MM-DD)
     * @param {string} goalPeriod - 目标周期 ('annual', 'half_year', 'quarterly')
     * @returns {string} 结束日期字符串 (YYYY-MM-DD)
     */
    function calculateEndDate(startDateStr, goalPeriod) {
        if (!startDateStr || !goalPeriod) {
            return '';
        }
        
        const startDate = new Date(startDateStr);
        if (isNaN(startDate.getTime())) {
            return '';
        }
        
        let endDate = new Date(startDate);
        
        switch(goalPeriod) {
            case 'annual':
                // 年度目标：开始日期后1年减1天
                endDate.setFullYear(endDate.getFullYear() + 1);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case 'half_year':
                // 半年目标：开始日期后6个月减1天
                endDate.setMonth(endDate.getMonth() + 6);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case 'quarterly':
                // 季度目标：开始日期后3个月减1天
                endDate.setMonth(endDate.getMonth() + 3);
                endDate.setDate(endDate.getDate() - 1);
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
        const startDateInput = document.getElementById('id_start_date');
        const endDateInput = document.getElementById('id_end_date');
        const goalPeriodSelect = document.getElementById('id_goal_period');
        
        if (!startDateInput || !endDateInput || !goalPeriodSelect) {
            return;
        }
        
        const startDate = startDateInput.value;
        const goalPeriod = goalPeriodSelect.value;
        
        if (startDate && goalPeriod) {
            const endDate = calculateEndDate(startDate, goalPeriod);
            if (endDate) {
                endDateInput.value = endDate;
            }
        }
    }
    
    /**
     * 初始化
     */
    function init() {
        const startDateInput = document.getElementById('id_start_date');
        const goalPeriodSelect = document.getElementById('id_goal_period');
        
        if (!startDateInput || !goalPeriodSelect) {
            return;
        }
        
        // 监听开始日期和目标周期的变化
        startDateInput.addEventListener('change', updateEndDate);
        goalPeriodSelect.addEventListener('change', updateEndDate);
        
        // 页面加载时，如果开始日期和目标周期都有值，自动计算结束日期
        if (startDateInput.value && goalPeriodSelect.value) {
            updateEndDate();
        } else if (!startDateInput.value) {
            // 如果开始日期为空（新建时），设置为今天
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            startDateInput.value = `${year}-${month}-${day}`;
            
            // 设置开始日期后，如果目标周期已选择，自动计算结束日期
            if (goalPeriodSelect.value) {
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
