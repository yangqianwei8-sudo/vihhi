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
DAILY_CRON="0 9 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_plan_reminder >> $LOG_DIR/daily_plan_reminder.log 2>&1"
WEEKLY_CRON="0 9 * * 5 cd $PROJECT_DIR && $VENV_PYTHON manage.py send_weekly_plan_reminder >> $LOG_DIR/weekly_plan_reminder.log 2>&1"
MONTHLY_CRON="0 9 28 * * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_monthly_plan_reminder >> $LOG_DIR/monthly_plan_reminder.log 2>&1"
QUARTERLY_CRON="0 9 15 3,6,9,12 * cd $PROJECT_DIR && $VENV_PYTHON manage.py send_quarterly_plan_reminder >> $LOG_DIR/quarterly_plan_reminder.log 2>&1"
OVERDUE_CHECK_CRON="30 18 * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py check_weekly_plan_overdue >> $LOG_DIR/weekly_plan_overdue.log 2>&1"

echo "将添加以下 crontab 条目："
echo ""
echo "# 日工作计划提醒（每天9点）"
echo "$DAILY_CRON"
echo ""
echo "# 周工作计划提醒（每周五9点）"
echo "$WEEKLY_CRON"
echo ""
echo "# 月度工作计划提醒（每月28日9点）"
echo "$MONTHLY_CRON"
echo ""
echo "# 季度工作计划提醒（每季度最后一个月15日9点：3月、6月、9月、12月）"
echo "$QUARTERLY_CRON"
echo ""
echo "# 周计划逾期检查（每天18:30执行，检查当天逾期的周计划）"
echo "$OVERDUE_CHECK_CRON"
echo ""

read -p "确认添加？(y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 获取当前 crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# 检查并删除旧任务
if echo "$CURRENT_CRONTAB" | grep -q "send_daily_plan_reminder"; then
    echo "⚠️  检测到已存在 send_daily_plan_reminder 任务，将替换"
    CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "send_daily_plan_reminder")
fi

if echo "$CURRENT_CRONTAB" | grep -q "send_weekly_plan_reminder"; then
    echo "⚠️  检测到已存在 send_weekly_plan_reminder 任务，将替换"
    CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "send_weekly_plan_reminder")
fi

if echo "$CURRENT_CRONTAB" | grep -q "send_monthly_plan_reminder"; then
    echo "⚠️  检测到已存在 send_monthly_plan_reminder 任务，将替换"
    CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "send_monthly_plan_reminder")
fi

if echo "$CURRENT_CRONTAB" | grep -q "send_quarterly_plan_reminder"; then
    echo "⚠️  检测到已存在 send_quarterly_plan_reminder 任务，将替换"
    CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "send_quarterly_plan_reminder")
fi

if echo "$CURRENT_CRONTAB" | grep -q "check_weekly_plan_overdue"; then
    echo "⚠️  检测到已存在 check_weekly_plan_overdue 任务，将替换"
    CURRENT_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "check_weekly_plan_overdue")
fi

# 添加新条目
(crontab -l 2>/dev/null | grep -v "send_daily_plan_reminder" | grep -v "send_weekly_plan_reminder" | grep -v "send_monthly_plan_reminder" | grep -v "send_quarterly_plan_reminder" | grep -v "check_weekly_plan_overdue"; echo ""; echo "# 计划管理提醒任务"; echo "$DAILY_CRON"; echo "$WEEKLY_CRON"; echo "$MONTHLY_CRON"; echo "$QUARTERLY_CRON"; echo "$OVERDUE_CHECK_CRON") | crontab -

echo ""
echo "✅ Crontab 任务已添加！"
echo ""
echo "查看当前 crontab："
echo "  crontab -l"
echo ""
echo "查看日志："
echo "  tail -f $LOG_DIR/daily_plan_reminder.log     # 日提醒日志"
echo "  tail -f $LOG_DIR/weekly_plan_reminder.log     # 周提醒日志"
echo "  tail -f $LOG_DIR/monthly_plan_reminder.log    # 月度提醒日志"
echo "  tail -f $LOG_DIR/quarterly_plan_reminder.log   # 季度提醒日志"
echo "  tail -f $LOG_DIR/weekly_plan_overdue.log      # 周计划逾期检查日志"
echo ""
echo "测试执行："
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_plan_reminder --test"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_weekly_plan_reminder --test"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_monthly_plan_reminder --test"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_quarterly_plan_reminder --test"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py check_weekly_plan_overdue --dry-run"
echo ""
echo "试运行（不实际发送）："
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_daily_plan_reminder --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_weekly_plan_reminder --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_monthly_plan_reminder --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py send_quarterly_plan_reminder --dry-run"
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py check_weekly_plan_overdue --dry-run"
echo ""
echo "删除任务："
echo "  crontab -e  # 然后删除相关行"

