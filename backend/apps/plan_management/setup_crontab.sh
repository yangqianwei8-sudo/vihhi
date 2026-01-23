#!/bin/bash
# 配置计划管理提醒 Crontab 定时任务

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_PYTHON="/home/devbox/project/.venv/bin/python"
LOG_DIR="/home/devbox/project/logs"

echo "=========================================="
echo "计划管理提醒 Crontab 定时任务配置"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p "$LOG_DIR"

# 生成 crontab 条目
# 每日通知（每天上午9点）
DAILY_NOTIFICATION_CRON="0 9 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_notifications >> $LOG_DIR/daily_notifications.log 2>&1"

# 计划自动状态流转（每天上午9点）
AUTO_TRANSITION_CRON="0 9 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py auto_transition_plans_to_in_progress >> $LOG_DIR/auto_transition_plans.log 2>&1"

# 目标进度更新待办（每周一上午10点）
GOAL_PROGRESS_UPDATE_CRON="0 10 * * 1 cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_goal_progress_update_todos >> $LOG_DIR/goal_progress_update_todos.log 2>&1"

# 周报生成（每周一上午9点）
WEEKLY_SUMMARY_CRON="0 9 * * 1 cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_weekly_summaries >> $LOG_DIR/weekly_summaries.log 2>&1"

# 月报生成（每月1日上午9点）
MONTHLY_SUMMARY_CRON="0 9 1 * * cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_monthly_summaries >> $LOG_DIR/monthly_summaries.log 2>&1"

# 目标创建待办（每个自然季度起始月1日9点：1月、4月、7月、10月）
GOAL_CREATION_CRON="0 9 1 1,4,7,10 * cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_goal_creation_todos >> $LOG_DIR/goal_creation_todos.log 2>&1"

# 月度公司计划创建待办（每月20日上午10点）
MONTHLY_COMPANY_PLAN_CRON="0 10 20 * * cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_monthly_company_plan_todos >> $LOG_DIR/monthly_company_plan_todos.log 2>&1"

# 周计划分解待办（每周五上午9点）
WEEKLY_PLAN_CRON="0 9 * * 5 cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_weekly_plan_todos >> $LOG_DIR/weekly_plan_todos.log 2>&1"

# 日计划分解待办（每天下午5点）
DAILY_PLAN_CRON="0 17 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_daily_plan_todos >> $LOG_DIR/daily_plan_todos.log 2>&1"

# 计划进度更新待办（每天下午5点）
PLAN_PROGRESS_UPDATE_CRON="0 17 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_plan_progress_update_todos >> $LOG_DIR/plan_progress_update_todos.log 2>&1"

# 待办事项逾期检查（每天凌晨1点）
TODO_OVERDUE_CHECK_CRON="0 1 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py check_todo_overdue >> $LOG_DIR/todo_overdue_check.log 2>&1"

# 周计划逾期检查（每天18:30）
OVERDUE_CHECK_CRON="30 18 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py check_weekly_plan_overdue >> $LOG_DIR/weekly_plan_overdue.log 2>&1"

# 保留原有的提醒任务（可选，如果不需要可以删除）
DAILY_CRON="0 9 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_plan_reminder >> $LOG_DIR/daily_plan_reminder.log 2>&1"
WEEKLY_CRON="0 9 * * 5 cd $PROJECT_DIR && $VENV_PYTHON manage.py send_weekly_plan_reminder >> $LOG_DIR/weekly_plan_reminder.log 2>&1"
MONTHLY_CRON="0 9 28 * * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_monthly_plan_reminder >> $LOG_DIR/monthly_plan_reminder.log 2>&1"
QUARTERLY_CRON="0 9 15 3,6,9,12 * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_quarterly_plan_reminder >> $LOG_DIR/quarterly_plan_reminder.log 2>&1"

echo "将添加以下 crontab 条目："
echo ""
echo "# ========== 每日任务 =========="
echo "# 每日通知（每天上午9点）"
echo "$DAILY_NOTIFICATION_CRON"
echo ""
echo "# 计划自动状态流转（每天上午9点）"
echo "$AUTO_TRANSITION_CRON"
echo ""
echo "# 日计划分解待办（每天下午5点）"
echo "$DAILY_PLAN_CRON"
echo ""
echo "# 计划进度更新待办（每天下午5点）"
echo "$PLAN_PROGRESS_UPDATE_CRON"
echo ""
echo "# 待办事项逾期检查（每天凌晨1点）"
echo "$TODO_OVERDUE_CHECK_CRON"
echo ""
echo "# 周计划逾期检查（每天18:30）"
echo "$OVERDUE_CHECK_CRON"
echo ""
echo "# ========== 每周任务 =========="
echo "# 目标进度更新待办（每周一上午10点）"
echo "$GOAL_PROGRESS_UPDATE_CRON"
echo ""
echo "# 周报生成（每周一上午9点）"
echo "$WEEKLY_SUMMARY_CRON"
echo ""
echo "# 周计划分解待办（每周五上午9点）"
echo "$WEEKLY_PLAN_CRON"
echo ""
echo "# ========== 每月任务 =========="
echo "# 月报生成（每月1日上午9点）"
echo "$MONTHLY_SUMMARY_CRON"
echo ""
echo "# 月度公司计划创建待办（每月20日上午10点）"
echo "$MONTHLY_COMPANY_PLAN_CRON"
echo ""
echo "# ========== 每季度任务 =========="
echo "# 目标创建待办（每个自然季度起始月1日9点：1月、4月、7月、10月）"
echo "$GOAL_CREATION_CRON"
echo ""
echo "# ========== 保留的原有任务（可选）=========="
echo "# 日工作计划提醒（每天9点）- 可选，已被每日通知替代"
echo "# $DAILY_CRON"
echo ""
echo "# 周工作计划提醒（每周五9点）- 可选，已被周计划分解待办替代"
echo "# $WEEKLY_CRON"
echo ""
echo "# 月度工作计划提醒（每月28日9点）- 可选"
echo "# $MONTHLY_CRON"
echo ""
echo "# 季度工作计划提醒（每季度最后一个月15日9点：3月、6月、9月、12月）- 可选"
echo "# $QUARTERLY_CRON"
echo ""

read -p "确认添加？(y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 获取当前 crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# 检查并删除旧任务
OLD_TASKS=(
    "send_daily_plan_reminder"
    "send_weekly_plan_reminder"
    "send_monthly_plan_reminder"
    "send_quarterly_plan_reminder"
    "check_weekly_plan_overdue"
    "send_daily_notifications"
    "auto_transition_plans_to_in_progress"
    "generate_goal_progress_update_todos"
    "generate_weekly_summaries"
    "generate_monthly_summaries"
    "generate_goal_creation_todos"
    "generate_monthly_company_plan_todos"
    "generate_weekly_plan_todos"
    "generate_daily_plan_todos"
    "generate_plan_progress_update_todos"
    "check_todo_overdue"
)

for task in "${OLD_TASKS[@]}"; do
    if echo "$CURRENT_CRONTAB" | grep -q "$task"; then
        echo "⚠️  检测到已存在 $task 任务，将替换"
        CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "$task")
    fi
done

# 构建新的 crontab 内容
NEW_CRONTAB=$(crontab -l 2>/dev/null | grep -v "send_daily_plan_reminder" | grep -v "send_weekly_plan_reminder" | grep -v "send_monthly_plan_reminder" | grep -v "send_quarterly_plan_reminder" | grep -v "check_weekly_plan_overdue" | grep -v "send_daily_notifications" | grep -v "auto_transition_plans_to_in_progress" | grep -v "generate_goal_progress_update_todos" | grep -v "generate_weekly_summaries" | grep -v "generate_monthly_summaries" | grep -v "generate_goal_creation_todos" | grep -v "generate_monthly_company_plan_todos" | grep -v "generate_weekly_plan_todos" | grep -v "generate_daily_plan_todos" | grep -v "generate_plan_progress_update_todos" | grep -v "check_todo_overdue")

# 添加新条目
(crontab -l 2>/dev/null | grep -v "计划管理" | grep -v "plan_management"; echo ""; echo "# ========== 计划管理自动任务 =========="; echo "$DAILY_NOTIFICATION_CRON"; echo "$AUTO_TRANSITION_CRON"; echo "$GOAL_PROGRESS_UPDATE_CRON"; echo "$WEEKLY_SUMMARY_CRON"; echo "$MONTHLY_SUMMARY_CRON"; echo "$GOAL_CREATION_CRON"; echo "$MONTHLY_COMPANY_PLAN_CRON"; echo "$WEEKLY_PLAN_CRON"; echo "$DAILY_PLAN_CRON"; echo "$PLAN_PROGRESS_UPDATE_CRON"; echo "$TODO_OVERDUE_CHECK_CRON"; echo "$OVERDUE_CHECK_CRON") | crontab -

echo ""
echo "✅ Crontab 任务已添加！"
echo ""
echo "查看当前 crontab："
echo "  crontab -l"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/daily_notifications.log              # 每日通知日志"
echo "  tail -f $LOG_DIR/auto_transition_plans.log           # 计划自动状态流转日志"
echo "  tail -f $LOG_DIR/goal_progress_update_todos.log      # 目标进度更新待办日志"
echo "  tail -f $LOG_DIR/weekly_summaries.log                 # 周报生成日志"
echo "  tail -f $LOG_DIR/monthly_summaries.log                # 月报生成日志"
echo "  tail -f $LOG_DIR/goal_creation_todos.log              # 目标创建待办日志"
echo "  tail -f $LOG_DIR/monthly_company_plan_todos.log       # 月度公司计划创建待办日志"
echo "  tail -f $LOG_DIR/weekly_plan_todos.log                 # 周计划分解待办日志"
echo "  tail -f $LOG_DIR/daily_plan_todos.log                 # 日计划分解待办日志"
echo "  tail -f $LOG_DIR/plan_progress_update_todos.log       # 计划进度更新待办日志"
echo "  tail -f $LOG_DIR/todo_overdue_check.log                # 待办事项逾期检查日志"
echo "  tail -f $LOG_DIR/weekly_plan_overdue.log              # 周计划逾期检查日志"
echo ""
echo "测试执行（使用 --dry-run 参数）："
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_notifications --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py auto_transition_plans_to_in_progress --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_goal_progress_update_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_weekly_summaries --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_monthly_summaries --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_goal_creation_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_monthly_company_plan_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_weekly_plan_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_daily_plan_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py generate_plan_progress_update_todos --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py check_todo_overdue --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py check_weekly_plan_overdue --dry-run"
echo ""
echo "删除任务："
echo "  crontab -e  # 然后删除相关行"

