#!/bin/bash
# 快速备份当前状态
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git add .
git commit -m "备份: $TIMESTAMP" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 备份完成: $TIMESTAMP"
else
    echo "ℹ️  没有需要备份的更改"
fi
