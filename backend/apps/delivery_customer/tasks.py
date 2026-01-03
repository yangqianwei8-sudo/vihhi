"""
发文管理模块Celery定时任务
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_outgoing_document_express_status():
    """
    定时任务：同步发文快递状态
    
    执行时间：建议每30分钟执行一次（需要在Celery Beat中配置）
    
    返回：
    {
        'success': bool,
        'total': int,
        'success_count': int,
        'failed_count': int,
        'skipped_count': int,
        'message': str
    }
    """
    try:
        from backend.apps.delivery_customer.services import OutgoingDocumentExpressSyncService
        
        result = OutgoingDocumentExpressSyncService.sync_all_pending_documents()
        
        logger.info(
            f'发文快递状态同步任务执行成功：'
            f'总数={result["total"]}, '
            f'成功={result["success"]}, '
            f'失败={result["failed"]}, '
            f'跳过={result["skipped"]}'
        )
        
        return {
            'success': True,
            'total': result['total'],
            'success_count': result['success'],
            'failed_count': result['failed'],
            'skipped_count': result['skipped'],
            'message': f'成功同步 {result["success"]} 个发文的快递状态'
        }
    except Exception as e:
        logger.error(f'发文快递状态同步任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'total': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'error': str(e),
            'message': f'发文快递状态同步任务执行失败: {str(e)}'
        }


@shared_task
def check_outgoing_document_delayed():
    """
    定时任务：检查并标记延迟的发文
    
    执行时间：建议每天执行一次（需要在Celery Beat中配置）
    
    返回：
    {
        'success': bool,
        'total_checked': int,
        'delayed_count': int,
        'message': str
    }
    """
    try:
        from backend.apps.delivery_customer.services import OutgoingDocumentExpressSyncService
        
        result = OutgoingDocumentExpressSyncService.check_delayed_documents()
        
        logger.info(
            f'发文延迟检查任务执行成功：'
            f'检查={result["total_checked"]}, '
            f'延迟={result["delayed_count"]}'
        )
        
        return {
            'success': True,
            'total_checked': result['total_checked'],
            'delayed_count': result['delayed_count'],
            'message': f'检查完成，发现 {result["delayed_count"]} 个延迟的发文'
        }
    except Exception as e:
        logger.error(f'发文延迟检查任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'total_checked': 0,
            'delayed_count': 0,
            'error': str(e),
            'message': f'发文延迟检查任务执行失败: {str(e)}'
        }


@shared_task
def send_outgoing_document_warnings():
    """
    定时任务：发送发文延迟预警通知
    
    执行时间：建议每天执行一次（需要在Celery Beat中配置）
    通常在延迟检查之后执行
    
    返回：
    {
        'success': bool,
        'total_checked': int,
        'warnings_sent': int,
        'already_warned': int,
        'message': str
    }
    """
    try:
        from backend.apps.delivery_customer.services import OutgoingDocumentWarningService
        
        result = OutgoingDocumentWarningService.check_and_send_warnings()
        
        logger.info(
            f'发文延迟预警任务执行成功：'
            f'检查={result["total_checked"]}, '
            f'已发送={result["warnings_sent"]}, '
            f'已预警={result["already_warned"]}'
        )
        
        return {
            'success': True,
            'total_checked': result['total_checked'],
            'warnings_sent': result['warnings_sent'],
            'already_warned': result['already_warned'],
            'message': f'成功发送 {result["warnings_sent"]} 个延迟预警通知'
        }
    except Exception as e:
        logger.error(f'发文延迟预警任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'total_checked': 0,
            'warnings_sent': 0,
            'already_warned': 0,
            'error': str(e),
            'message': f'发文延迟预警任务执行失败: {str(e)}'
        }


@shared_task
def auto_archive_outgoing_documents():
    """
    定时任务：自动归档符合条件的发文
    
    执行时间：建议每天执行一次（需要在Celery Beat中配置）
    
    归档条件：
    - 状态为已完成(completed)
    - 已签收确认(is_receipt_confirmed=True)
    - 签收确认后超过7天
    
    返回：
    {
        'success': bool,
        'total_checked': int,
        'archived_count': int,
        'failed_count': int,
        'message': str
    }
    """
    try:
        from backend.apps.delivery_customer.services import OutgoingDocumentArchiveService
        
        result = OutgoingDocumentArchiveService.auto_archive_eligible_documents(
            days_after_completion=7
        )
        
        logger.info(
            f'发文自动归档任务执行成功：'
            f'检查={result["total_checked"]}, '
            f'归档={result["archived_count"]}, '
            f'失败={result["failed_count"]}'
        )
        
        return {
            'success': True,
            'total_checked': result['total_checked'],
            'archived_count': result['archived_count'],
            'failed_count': result['failed_count'],
            'message': f'成功归档 {result["archived_count"]} 个发文'
        }
    except Exception as e:
        logger.error(f'发文自动归档任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'total_checked': 0,
            'archived_count': 0,
            'failed_count': 0,
            'error': str(e),
            'message': f'发文自动归档任务执行失败: {str(e)}'
        }



@shared_task
def update_outgoing_document_tracking_status():
    """
    定时任务：自动更新发文跟踪状态（邮件、快递等）
    
    执行时间：建议每30分钟执行一次（需要在Celery Beat中配置）
    
    返回：
    {
        'success': bool,
        'updated_count': int,  # 成功更新的数量
        'error_count': int,     # 失败的数量
        'message': str
    }
    """
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # 调用管理命令
        out = StringIO()
        call_command('update_tracking_status', limit=50, stdout=out)
        output = out.getvalue()
        
        # 解析输出（简单解析）
        updated_count = 0
        error_count = 0
        
        if '成功' in output:
            # 尝试从输出中提取数字
            import re
            success_match = re.search(r'成功 (\d+) 条', output)
            failed_match = re.search(r'失败 (\d+) 条', output)
            if success_match:
                updated_count = int(success_match.group(1))
            if failed_match:
                error_count = int(failed_match.group(1))
        
        logger.info(
            f'发文跟踪状态更新任务执行完成：'
            f'成功={updated_count}, 失败={error_count}'
        )
        
        return {
            'success': True,
            'updated_count': updated_count,
            'error_count': error_count,
            'message': f'成功更新 {updated_count} 条跟踪记录，失败 {error_count} 条'
        }
    except Exception as e:
        logger.error(f'发文跟踪状态更新任务执行失败: {str(e)}', exc_info=True)
        return {
            'success': False,
            'updated_count': 0,
            'error_count': 0,
            'error': str(e),
            'message': f'任务执行失败：{str(e)}'
        }
