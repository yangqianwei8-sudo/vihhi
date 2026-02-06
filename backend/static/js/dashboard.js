/**
 * 工作台 dashboard 图表与统计逻辑（由模板内联脚本外迁）
 * 依赖：Chart (chart.umd.min.js)、模板中的 type="application/json" 数据块
 */
(function () {
  'use strict';

  function getJsonScript(id) {
    var el = document.getElementById(id);
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      console.warn('dashboard.js: invalid JSON in #' + id, e);
      return null;
    }
  }

  function renderRiskChart() {
    var ctx = document.getElementById('employeeRiskChart');
    if (!ctx) return;
    var employeeData = getJsonScript('dashboard-employee-risk-data');
    if (!employeeData || !Array.isArray(employeeData)) return;

    var highRiskCount = 0, totalRiskCount = 0, totalRiskScore = 0;
    employeeData.forEach(function (emp) {
      if (emp.total_risk_score >= 20) highRiskCount++;
      totalRiskCount += (emp.total_risk_count || 0);
      totalRiskScore += (emp.total_risk_score || 0);
    });
    var highEl = document.getElementById('high-risk-count');
    var totalEl = document.getElementById('total-risk-count');
    var scoreEl = document.getElementById('total-risk-score');
    if (highEl) highEl.textContent = highRiskCount;
    if (totalEl) totalEl.textContent = totalRiskCount;
    if (scoreEl) scoreEl.textContent = Math.round(totalRiskScore);

    var labels = employeeData.map(function (e) { return e.user_name; });
    var goalRiskData = employeeData.map(function (e) { return e.goal_risk_count || 0; });
    var planRiskData = employeeData.map(function (e) { return e.plan_risk_count || 0; });
    var totalRiskData = employeeData.map(function (e) { return e.total_risk_count || 0; });
    var riskScoreData = employeeData.map(function (e) { return e.total_risk_score || 0; });

    new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: '风险目标数', data: goalRiskData, backgroundColor: 'rgba(220, 53, 69, 0.8)', borderColor: 'rgba(220, 53, 69, 1)', borderWidth: 1 },
          { label: '风险计划数', data: planRiskData, backgroundColor: 'rgba(255, 193, 7, 0.8)', borderColor: 'rgba(255, 193, 7, 1)', borderWidth: 1 },
          { label: '总风险数', data: totalRiskData, backgroundColor: 'rgba(255, 87, 34, 0.8)', borderColor: 'rgba(255, 87, 34, 1)', borderWidth: 1 },
          { label: '风险分数', data: riskScoreData, backgroundColor: 'rgba(156, 39, 176, 0.8)', borderColor: 'rgba(156, 39, 176, 1)', borderWidth: 2, type: 'line', tension: 0.4, yAxisID: 'y1' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: '员工风险指标对比图', font: { size: 16, weight: 'bold' } },
          legend: { display: true, position: 'top' },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              afterLabel: function (context) {
                var emp = employeeData[context.dataIndex];
                return ['部门: ' + emp.department, '总风险: ' + (emp.total_risk_count || 0), '平均逾期: ' + (emp.avg_days_overdue || 0) + '天', '平均进度差距: ' + (emp.avg_progress_gap || 0) + '%'];
              }
            }
          }
        },
        scales: {
          x: { stacked: false, ticks: { maxRotation: 0, minRotation: 0 } },
          y: { beginAtZero: true, position: 'left', title: { display: true, text: '风险数量' } },
          y1: { beginAtZero: true, position: 'right', title: { display: true, text: '风险分数' }, grid: { drawOnChartArea: false } }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  function renderTodoChart() {
    var ctx = document.getElementById('employeeTodoChart');
    if (!ctx) return;
    var employeeData = getJsonScript('dashboard-employee-todo-data');
    if (!employeeData || !Array.isArray(employeeData)) return;

    var highTodoCount = 0, totalTodoCount = 0, totalOverdueCount = 0;
    employeeData.forEach(function (emp) {
      if (emp.todo_score >= 100) highTodoCount++;
      totalTodoCount += (emp.total_todos || 0);
      totalOverdueCount += (emp.overdue_count || 0);
    });
    var highEl = document.getElementById('high-todo-count');
    var totalEl = document.getElementById('total-todo-count');
    var overdueEl = document.getElementById('total-overdue-count');
    if (highEl) highEl.textContent = highTodoCount;
    if (totalEl) totalEl.textContent = totalTodoCount;
    if (overdueEl) overdueEl.textContent = totalOverdueCount;

    var labels = employeeData.map(function (e) { return e.user_name; });
    var totalTodosData = employeeData.map(function (e) { return e.total_todos || 0; });
    var highPriorityData = employeeData.map(function (e) { return e.high_priority_count || 0; });
    var overdueData = employeeData.map(function (e) { return e.overdue_count || 0; });
    var todoScoreData = employeeData.map(function (e) { return e.todo_score || 0; });

    new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: '总待办数', data: totalTodosData, backgroundColor: 'rgba(13, 110, 253, 0.8)', borderColor: 'rgba(13, 110, 253, 1)', borderWidth: 1 },
          { label: '高优先级', data: highPriorityData, backgroundColor: 'rgba(220, 53, 69, 0.8)', borderColor: 'rgba(220, 53, 69, 1)', borderWidth: 1 },
          { label: '逾期数', data: overdueData, backgroundColor: 'rgba(255, 193, 7, 0.8)', borderColor: 'rgba(255, 193, 7, 1)', borderWidth: 1 },
          { label: '待办分数', data: todoScoreData, backgroundColor: 'rgba(156, 39, 176, 0.8)', borderColor: 'rgba(156, 39, 176, 1)', borderWidth: 2, type: 'line', tension: 0.4, yAxisID: 'y1' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: '员工待办事项对比图', font: { size: 16, weight: 'bold' } },
          legend: { display: true, position: 'top' },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              afterLabel: function (context) {
                var emp = employeeData[context.dataIndex];
                return ['部门: ' + emp.department, '总待办: ' + (emp.total_todos || 0), '高优先级: ' + (emp.high_priority_count || 0), '中优先级: ' + (emp.medium_priority_count || 0), '低优先级: ' + (emp.low_priority_count || 0), '逾期: ' + (emp.overdue_count || 0), '平均逾期: ' + (emp.avg_days_overdue || 0) + '天'];
              }
            }
          }
        },
        scales: {
          x: { stacked: false, ticks: { maxRotation: 0, minRotation: 0 } },
          y: { beginAtZero: true, position: 'left', title: { display: true, text: '待办数量' } },
          y1: { beginAtZero: true, position: 'right', title: { display: true, text: '待办分数' }, grid: { drawOnChartArea: false } }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  function renderPlanChart() {
    var ctx = document.getElementById('employeePlanChart');
    if (!ctx) return;
    var employeeData = getJsonScript('dashboard-employee-plan-data');
    if (!employeeData || !Array.isArray(employeeData)) return;

    var highPlanCount = 0, totalPlanCount = 0, totalOverduePlanCount = 0;
    employeeData.forEach(function (emp) {
      if (emp.plan_score >= 50) highPlanCount++;
      totalPlanCount += (emp.total_plans || 0);
      totalOverduePlanCount += (emp.overdue_count || 0);
    });
    var highEl = document.getElementById('high-plan-count');
    var totalEl = document.getElementById('total-plan-count');
    var overdueEl = document.getElementById('total-overdue-plan-count');
    if (highEl) highEl.textContent = highPlanCount;
    if (totalEl) totalEl.textContent = totalPlanCount;
    if (overdueEl) overdueEl.textContent = totalOverduePlanCount;

    var labels = employeeData.map(function (e) { return e.user_name; });
    var totalPlansData = employeeData.map(function (e) { return e.total_plans || 0; });
    var inProgressData = employeeData.map(function (e) { return e.in_progress_count || 0; });
    var overdueData = employeeData.map(function (e) { return e.overdue_count || 0; });
    var todayData = employeeData.map(function (e) { return e.today_count || 0; });
    var planScoreData = employeeData.map(function (e) { return e.plan_score || 0; });

    new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: '总计划数', data: totalPlansData, backgroundColor: 'rgba(25, 135, 84, 0.8)', borderColor: 'rgba(25, 135, 84, 1)', borderWidth: 1 },
          { label: '执行中', data: inProgressData, backgroundColor: 'rgba(13, 110, 253, 0.8)', borderColor: 'rgba(13, 110, 253, 1)', borderWidth: 1 },
          { label: '逾期数', data: overdueData, backgroundColor: 'rgba(255, 193, 7, 0.8)', borderColor: 'rgba(255, 193, 7, 1)', borderWidth: 1 },
          { label: '今日应执行', data: todayData, backgroundColor: 'rgba(220, 53, 69, 0.8)', borderColor: 'rgba(220, 53, 69, 1)', borderWidth: 1 },
          { label: '计划分数', data: planScoreData, backgroundColor: 'rgba(156, 39, 176, 0.8)', borderColor: 'rgba(156, 39, 176, 1)', borderWidth: 2, type: 'line', tension: 0.4, yAxisID: 'y1' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: '员工工作计划对比图', font: { size: 16, weight: 'bold' } },
          legend: { display: true, position: 'top' },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              afterLabel: function (context) {
                var emp = employeeData[context.dataIndex];
                return ['部门: ' + emp.department, '总计划: ' + (emp.total_plans || 0), '草稿: ' + (emp.draft_count || 0), '已发布: ' + (emp.published_count || 0), '已接受: ' + (emp.accepted_count || 0), '执行中: ' + (emp.in_progress_count || 0), '已完成: ' + (emp.completed_count || 0), '逾期: ' + (emp.overdue_count || 0), '平均逾期: ' + (emp.avg_days_overdue || 0) + '天', '平均进度: ' + (emp.avg_progress || 0) + '%'];
              }
            }
          }
        },
        scales: {
          x: { stacked: false, ticks: { maxRotation: 0, minRotation: 0 } },
          y: { beginAtZero: true, position: 'left', title: { display: true, text: '计划数量' } },
          y1: { beginAtZero: true, position: 'right', title: { display: true, text: '计划分数' }, grid: { drawOnChartArea: false } }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  function renderGoalChart() {
    var ctx = document.getElementById('employeeGoalChart');
    if (!ctx) return;
    var employeeData = getJsonScript('dashboard-employee-goal-data');
    if (!employeeData || !Array.isArray(employeeData)) return;

    var highGoalCount = 0, totalGoalCount = 0, totalOverdueGoalCount = 0;
    employeeData.forEach(function (emp) {
      if (emp.goal_score >= 50) highGoalCount++;
      totalGoalCount += (emp.total_goals || 0);
      totalOverdueGoalCount += (emp.overdue_count || 0);
    });
    var highEl = document.getElementById('high-goal-count');
    var totalEl = document.getElementById('total-goal-count');
    var overdueEl = document.getElementById('total-overdue-goal-count');
    if (highEl) highEl.textContent = highGoalCount;
    if (totalEl) totalEl.textContent = totalGoalCount;
    if (overdueEl) overdueEl.textContent = totalOverdueGoalCount;

    var labels = employeeData.map(function (e) { return e.user_name; });
    var totalGoalsData = employeeData.map(function (e) { return e.total_goals || 0; });
    var inProgressData = employeeData.map(function (e) { return e.in_progress_count || 0; });
    var overdueData = employeeData.map(function (e) { return e.overdue_count || 0; });
    var thisMonthData = employeeData.map(function (e) { return e.this_month_count || 0; });
    var goalScoreData = employeeData.map(function (e) { return e.goal_score || 0; });

    new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: '总目标数', data: totalGoalsData, backgroundColor: 'rgba(13, 202, 240, 0.8)', borderColor: 'rgba(13, 202, 240, 1)', borderWidth: 1 },
          { label: '执行中', data: inProgressData, backgroundColor: 'rgba(13, 110, 253, 0.8)', borderColor: 'rgba(13, 110, 253, 1)', borderWidth: 1 },
          { label: '逾期数', data: overdueData, backgroundColor: 'rgba(255, 193, 7, 0.8)', borderColor: 'rgba(255, 193, 7, 1)', borderWidth: 1 },
          { label: '本月需完成', data: thisMonthData, backgroundColor: 'rgba(220, 53, 69, 0.8)', borderColor: 'rgba(220, 53, 69, 1)', borderWidth: 1 },
          { label: '目标分数', data: goalScoreData, backgroundColor: 'rgba(156, 39, 176, 0.8)', borderColor: 'rgba(156, 39, 176, 1)', borderWidth: 2, type: 'line', tension: 0.4, yAxisID: 'y1' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: '员工战略目标对比图', font: { size: 16, weight: 'bold' } },
          legend: { display: true, position: 'top' },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              afterLabel: function (context) {
                var emp = employeeData[context.dataIndex];
                return ['部门: ' + emp.department, '总目标: ' + (emp.total_goals || 0), '草稿: ' + (emp.draft_count || 0), '已发布: ' + (emp.published_count || 0), '已接受: ' + (emp.accepted_count || 0), '执行中: ' + (emp.in_progress_count || 0), '已完成: ' + (emp.completed_count || 0), '逾期: ' + (emp.overdue_count || 0), '平均逾期: ' + (emp.avg_days_overdue || 0) + '天', '本月需完成: ' + (emp.this_month_count || 0), '平均完成率: ' + (emp.avg_completion || 0) + '%'];
              }
            }
          }
        },
        scales: {
          x: { stacked: false, ticks: { maxRotation: 0, minRotation: 0 } },
          y: { beginAtZero: true, position: 'left', title: { display: true, text: '目标数量' } },
          y1: { beginAtZero: true, position: 'right', title: { display: true, text: '目标分数' }, grid: { drawOnChartArea: false } }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }
    renderRiskChart();
    renderTodoChart();
    renderPlanChart();
    renderGoalChart();
  }

  init();
})();
