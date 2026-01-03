#!/usr/bin/env python3
"""
发文跟踪状态更新守护进程
适用于没有 systemd/crontab 的环境（如 Docker 容器）

使用方法：
    python run_tracking_update_daemon.py

后台运行：
    nohup python run_tracking_update_daemon.py > tracking_update.log 2>&1 &
    
或者使用 screen/tmux：
    screen -S tracking_update
    python run_tracking_update_daemon.py
    # 按 Ctrl+A 然后 D 退出 screen
"""
import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tracking_update_daemon.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 配置
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
MANAGE_PY = PROJECT_DIR / 'manage.py'
INTERVAL_MINUTES = 30  # 执行间隔（分钟）
LIMIT = 50  # 每次更新的记录数量限制
RUNNING = True


def signal_handler(sig, frame):
    """处理退出信号"""
    global RUNNING
    logger.info('收到退出信号，正在停止...')
    RUNNING = False
    sys.exit(0)


def run_update():
    """执行更新命令"""
    try:
        logger.info(f'开始执行跟踪状态更新（限制：{LIMIT}条）...')
        
        # 执行 Django 管理命令
        result = subprocess.run(
            [sys.executable, str(MANAGE_PY), 'update_tracking_status', '--limit', str(LIMIT)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            logger.info('跟踪状态更新执行成功')
            if result.stdout:
                logger.info(f'输出：{result.stdout.strip()}')
        else:
            logger.error(f'跟踪状态更新执行失败（退出码：{result.returncode}）')
            if result.stderr:
                logger.error(f'错误：{result.stderr.strip()}')
            if result.stdout:
                logger.info(f'输出：{result.stdout.strip()}')
                
    except subprocess.TimeoutExpired:
        logger.error('执行超时（超过5分钟）')
    except Exception as e:
        logger.error(f'执行异常：{str(e)}', exc_info=True)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info('=' * 50)
    logger.info('发文跟踪状态更新守护进程启动')
    logger.info(f'项目目录：{PROJECT_DIR}')
    logger.info(f'执行间隔：{INTERVAL_MINUTES} 分钟')
    logger.info(f'每次更新限制：{LIMIT} 条')
    logger.info('=' * 50)
    
    # 验证 manage.py 是否存在
    if not MANAGE_PY.exists():
        logger.error(f'找不到 manage.py：{MANAGE_PY}')
        sys.exit(1)
    
    # 立即执行一次
    run_update()
    
    # 循环执行
    interval_seconds = INTERVAL_MINUTES * 60
    while RUNNING:
        try:
            logger.info(f'等待 {INTERVAL_MINUTES} 分钟后执行下一次更新...')
            time.sleep(interval_seconds)
            
            if RUNNING:
                run_update()
                
        except KeyboardInterrupt:
            logger.info('收到键盘中断信号')
            break
        except Exception as e:
            logger.error(f'循环执行异常：{str(e)}', exc_info=True)
            # 发生异常时等待一段时间再继续
            time.sleep(60)
    
    logger.info('守护进程已停止')


if __name__ == '__main__':
    main()
