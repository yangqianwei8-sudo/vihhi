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
                // 日计划：开始日期后1天（今天开始，明天结束）
                endDate.setDate(endDate.getDate() + 1);
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
     * 更新结束日期（基本信息表单）
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
     * 更新 FormSet 中所有计划项的结束日期
     */
    function updateFormsetEndDates() {
        const planPeriodSelect = document.getElementById('id_plan_period');
        if (!planPeriodSelect) {
            return;
        }
        
        const planPeriod = planPeriodSelect.value;
        if (!planPeriod) {
            return;
        }
        
        // 查找所有 FormSet 中的开始时间和结束时间字段
        const formsetStartTimeInputs = document.querySelectorAll('input[name*="planitems"][name*="start_time"]');
        formsetStartTimeInputs.forEach(function(startInput) {
            const startDate = startInput.value;
            if (!startDate) {
                return;
            }
            
            // 找到对应的结束时间字段（同一卡片中）
            const card = startInput.closest('.plan-item-card');
            if (!card) {
                return;
            }
            
            const endInput = card.querySelector('input[name*="planitems"][name*="end_time"]');
            if (endInput) {
                const endDate = calculateEndDate(startDate, planPeriod);
                if (endDate) {
                    endInput.value = endDate;
                }
            }
        });
    }
    
    /**
     * 为 FormSet 中的字段添加事件监听
     */
    function setupFormsetListeners() {
        const planPeriodSelect = document.getElementById('id_plan_period');
        if (!planPeriodSelect) {
            return;
        }
        
        // 监听计划周期的变化，更新所有 FormSet 中的结束时间
        planPeriodSelect.addEventListener('change', function() {
            updateFormsetEndDates();
        });
        
        // 使用事件委托监听 FormSet 中开始时间的变化
        const planItemsContainer = document.getElementById('planItemsContainer');
        if (planItemsContainer) {
            planItemsContainer.addEventListener('change', function(e) {
                if (e.target && e.target.name && e.target.name.includes('start_time') && e.target.name.includes('planitems')) {
                    const startDate = e.target.value;
                    const planPeriod = planPeriodSelect.value;
                    
                    if (startDate && planPeriod) {
                        const card = e.target.closest('.plan-item-card');
                        if (card) {
                            const endInput = card.querySelector('input[name*="planitems"][name*="end_time"]');
                            if (endInput) {
                                const endDate = calculateEndDate(startDate, planPeriod);
                                if (endDate) {
                                    endInput.value = endDate;
                                }
                            }
                        }
                    }
                }
            });
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
        
        // 监听基本信息表单中开始日期和计划周期的变化
        startDateInput.addEventListener('change', function() {
            updateEndDate();
            updateFormsetEndDates();
        });
        planPeriodSelect.addEventListener('change', function() {
            updateEndDate();
            updateFormsetEndDates();
        });
        
        // 设置 FormSet 字段的监听器
        setupFormsetListeners();
        
        // 页面加载时，如果开始日期和计划周期都有值，自动计算结束日期
        if (startDateInput.value && planPeriodSelect.value) {
            updateEndDate();
            updateFormsetEndDates();
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
                updateFormsetEndDates();
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
