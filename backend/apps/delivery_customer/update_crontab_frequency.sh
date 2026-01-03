#!/bin/bash
# 修改 Crontab 执行频率

echo "当前 crontab 配置："
crontab -l | grep "update_tracking_status" || echo "未找到任务"
echo ""

echo "请选择新的执行频率："
echo "1. 每15分钟执行一次 (*/15 * * * *)"
echo "2. 每30分钟执行一次 (*/30 * * * *)"
echo "3. 每小时执行一次 (0 * * * *)"
echo "4. 每2小时执行一次 (0 */2 * * *)"
echo "5. 每天上午9点执行 (0 9 * * *)"
echo "6. 自定义（手动输入）"
read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        NEW_SCHEDULE="*/15 * * * *"
        ;;
    2)
        NEW_SCHEDULE="*/30 * * * *"
        ;;
    3)
        NEW_SCHEDULE="0 * * * *"
        ;;
    4)
        NEW_SCHEDULE="0 */2 * * *"
        ;;
    5)
        NEW_SCHEDULE="0 9 * * *"
        ;;
    6)
        read -p "请输入 cron 表达式（如：0 * * * *）: " NEW_SCHEDULE
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

# 获取当前 crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# 替换时间表达式
NEW_CRONTAB=$(echo "$CURRENT_CRONTAB" | sed "s|^[^ ]* [^ ]* [^ ]* [^ ]* [^ ]*|$NEW_SCHEDULE|" | sed "s|^\([^#].*update_tracking_status.*\)|$NEW_SCHEDULE \$(echo '\1' | sed 's/^[^ ]* [^ ]* [^ ]* [^ ]* [^ ]* //')|")

# 更简单的方法：直接替换时间部分
NEW_CRONTAB=$(echo "$CURRENT_CRONTAB" | sed "s|^\([0-9*\/]* [0-9*\/]* [0-9*\/]* [0-9*\/]* [0-9*\/]*\)\(.*update_tracking_status.*\)|$NEW_SCHEDULE\2|")

echo "$NEW_CRONTAB" | crontab -

echo ""
echo "✅ 已更新为：$NEW_SCHEDULE"
echo ""
echo "新的配置："
crontab -l | grep "update_tracking_status"
