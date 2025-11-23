#!/bin/bash
# GitHub自动同步脚本
# 支持定时检查和实时监控两种模式

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
LOG_FILE="/tmp/git_auto_sync.log"
BRANCH="main"
REMOTE="origin"

cd "$PROJECT_DIR" || exit 1

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 同步函数
sync_from_github() {
    # 确保在正确的目录
    cd "$PROJECT_DIR" || {
        log "✗ 错误：无法进入项目目录 $PROJECT_DIR"
        return 1
    }
    
    log "开始同步..."
    
    # 获取远程更新
    if ! git fetch "$REMOTE" >> "$LOG_FILE" 2>&1; then
        log "✗ 获取远程更新失败，请检查网络和权限"
        return 1
    fi
    
    # 检查是否有更新
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE_REF="$REMOTE/$BRANCH"
    REMOTE=$(git rev-parse "$REMOTE_REF" 2>/dev/null)
    
    if [ -z "$LOCAL" ] || [ -z "$REMOTE" ]; then
        log "✗ 无法获取本地或远程提交信息"
        return 1
    fi
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        log "检测到远程更新，开始拉取..."
        
        # 检查是否有本地未提交的更改
        if ! git diff-index --quiet HEAD --; then
            log "警告：检测到本地未提交的更改，先暂存..."
            git stash >> "$LOG_FILE" 2>&1
            STASHED=true
        else
            STASHED=false
        fi
        
        # 拉取更新
        if git pull "$REMOTE" "$BRANCH" >> "$LOG_FILE" 2>&1; then
            log "✓ 同步成功"
            
            # 如果有暂存的更改，尝试恢复
            if [ "$STASHED" = true ]; then
                log "恢复本地更改..."
                git stash pop >> "$LOG_FILE" 2>&1 || log "警告：恢复本地更改时出现冲突"
            fi
            
            # 如果有迁移文件，提示运行迁移
            if git diff --name-only HEAD@{1} HEAD | grep -q "migrations/"; then
                log "检测到数据库迁移文件，请运行: python manage.py migrate"
            fi
            
            return 0
        else
            log "✗ 同步失败，请查看日志: $LOG_FILE"
            return 1
        fi
    else
        log "已是最新版本，无需同步"
        return 0
    fi
}

# 主函数
main() {
    MODE=${1:-"once"}  # 默认执行一次
    
    case "$MODE" in
        "once")
            sync_from_github
            ;;
        "watch")
            log "启动监控模式（每30秒检查一次）..."
            while true; do
                sync_from_github
                sleep 30
            done
            ;;
        "interval")
            INTERVAL=${2:-60}  # 默认60秒
            log "启动定时模式（每${INTERVAL}秒检查一次）..."
            while true; do
                sync_from_github
                sleep "$INTERVAL"
            done
            ;;
        *)
            echo "用法: $0 [once|watch|interval [秒数]]"
            echo "  once      - 执行一次同步"
            echo "  watch     - 监控模式，每30秒检查一次"
            echo "  interval  - 自定义间隔，默认60秒"
            exit 1
            ;;
    esac
}

main "$@"

