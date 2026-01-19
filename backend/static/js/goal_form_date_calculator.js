// 战略目标表单日期自动计算脚本
// 根据目标周期自动计算结束日期

(function() {
    'use strict';
    
    /**
     * 获取指定年月的最大天数
     */
    function getMaxDay(year, month) {
        return new Date(year, month, 0).getDate();
    }
    
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
        
        const startDate = new Date(startDateStr + 'T00:00:00'); // 添加时间避免时区问题
        if (isNaN(startDate.getTime())) {
            return '';
        }
        
        const startYear = startDate.getFullYear();
        const startMonth = startDate.getMonth() + 1; // getMonth() 返回 0-11
        const startDay = startDate.getDate();
        
        let endYear, endMonth, endDay;
        
        switch(goalPeriod) {
            case 'annual':
                // 年度目标：开始日期后1年减1天
                endYear = startYear + 1;
                endMonth = startMonth;
                endDay = startDay;
                // 处理2月29日的情况
                if (endMonth === 2 && endDay === 29) {
                    endDay = 28;
                }
                break;
            case 'half_year':
                // 半年目标：开始日期后6个月减1天
                endYear = startYear;
                endMonth = startMonth + 6;
                if (endMonth > 12) {
                    endYear += 1;
                    endMonth -= 12;
                }
                // 确保日期有效（处理月末日期）
                const maxDayHalf = getMaxDay(endYear, endMonth);
                endDay = Math.min(startDay, maxDayHalf);
                break;
            case 'quarterly':
                // 季度目标：开始日期后3个月减1天
                endYear = startYear;
                endMonth = startMonth + 3;
                if (endMonth > 12) {
                    endYear += 1;
                    endMonth -= 12;
                }
                // 确保日期有效（处理月末日期）
                const maxDayQuarter = getMaxDay(endYear, endMonth);
                endDay = Math.min(startDay, maxDayQuarter);
                break;
            default:
                return '';
        }
        
        // 创建结束日期并减1天
        const endDate = new Date(endYear, endMonth - 1, endDay); // month 参数是 0-11
        endDate.setDate(endDate.getDate() - 1);
        
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
        // 等待DOM完全加载，确保所有字段都已渲染
        const startDateInput = document.getElementById('id_start_date');
        const endDateInput = document.getElementById('id_end_date');
        const goalPeriodSelect = document.getElementById('id_goal_period');
        
        if (!startDateInput || !goalPeriodSelect || !endDateInput) {
            // 如果字段还没加载，延迟重试
            setTimeout(init, 100);
            return;
        }
        
        // 监听开始日期和目标周期的变化
        startDateInput.addEventListener('change', updateEndDate);
        startDateInput.addEventListener('input', updateEndDate); // 也监听input事件
        goalPeriodSelect.addEventListener('change', updateEndDate);
        
        // 表单加载时，自动设置开始日期为当天（新建表单时）
        // 确保开始日期字段始终有默认值（新建时），编辑时保持原值
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;
        
        // 检查是否是新建表单（通过检查字段是否有值，或者检查是否有其他标识）
        // 如果开始日期字段为空、没有值、或者值为空字符串，自动设置为当天日期
        const currentValue = startDateInput.value;
        if (!currentValue || currentValue.trim() === '' || currentValue === 'None') {
            // 新建表单：强制设置为当天日期
            startDateInput.value = todayStr;
            // 触发 input 事件，确保其他监听器也能收到通知
            startDateInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // 页面加载时，如果开始日期和目标周期都有值，自动计算结束日期
        if (startDateInput.value && goalPeriodSelect.value) {
            updateEndDate();
        } else if (goalPeriodSelect.value && startDateInput.value) {
            // 如果只有目标周期有值，也尝试计算结束日期（使用默认的开始日期）
            updateEndDate();
        }
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // 延迟一点时间确保所有动态内容都已加载
            setTimeout(init, 50);
        });
    } else {
        // 如果DOM已经加载完成，延迟一点时间再初始化
        setTimeout(init, 50);
    }
})();
