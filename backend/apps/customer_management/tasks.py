# ==================== 客户管理模块Celery定时任务（按《客户管理详细设计方案 v1.12》实现）====================

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def auto_move_clients_to_public_sea():
    """
    定时任务：每天自动将超过90天没有拜访信息的客户移入公海
    
    执行时间：每天凌晨2点（需要在Celery Beat中配置）
    
    返回：
    {
        'success': bool,
        'count': int,  # 移入公海的客户数量
        'message': str
    }
    """
    try:
        from .services import auto_move_to_public_sea
        
        count = auto_move_to_public_sea()
        
        logger.info(f'自动移入公海任务执行成功，共移入 {count} 个客户')
        
        return {
            'success': True,
            'count': count,
            'message': f'成功将 {count} 个客户移入公海'
        }
    except Exception as e:
        logger.error(f'自动移入公海任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'count': 0,
            'error': str(e),
            'message': f'自动移入公海任务执行失败: {str(e)}'
        }

