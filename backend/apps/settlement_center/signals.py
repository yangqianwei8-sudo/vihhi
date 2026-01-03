"""
结算中心信号处理器
监听模型变化，自动清除相关缓存
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from backend.core.cache_utils import CacheManager, clear_related_cache

from .models import (
    ProjectSettlement, SettlementItem, OutputValueRecord,
    PaymentRecord, ContractSettlement
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProjectSettlement)
def clear_cache_on_settlement_save(sender, instance, created, **kwargs):
    """项目结算保存时清除相关缓存"""
    try:
        # 使用通用函数清除相关用户的缓存
        user_fields = ['created_by', 'submitted_by', 'confirmed_by', 'reconciliation_by']
        cleared_count = clear_related_cache(instance, user_fields)
        
        # 清除项目负责人的缓存
        if instance.project_id:
            try:
                project = instance.project
                if hasattr(project, 'project_manager') and project.project_manager_id:
                    CacheManager.clear_user_dashboard_cache(project.project_manager_id)
                    cleared_count += 1
            except Exception as e:
                logger.warning(f'获取项目信息失败: {e}')
        
        logger.debug(f'项目结算 {instance.settlement_number} 保存，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除项目结算缓存时出错: {e}')


@receiver(post_delete, sender=ProjectSettlement)
def clear_cache_on_settlement_delete(sender, instance, **kwargs):
    """项目结算删除时清除相关缓存"""
    try:
        user_fields = ['created_by', 'submitted_by', 'confirmed_by', 'reconciliation_by']
        cleared_count = clear_related_cache(instance, user_fields)
        
        if instance.project_id:
            try:
                project = instance.project
                if hasattr(project, 'project_manager') and project.project_manager_id:
                    CacheManager.clear_user_dashboard_cache(project.project_manager_id)
                    cleared_count += 1
            except Exception:
                pass
        
        logger.debug(f'项目结算删除，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除项目结算缓存时出错: {e}')


@receiver(post_save, sender=SettlementItem)
def clear_cache_on_settlement_item_save(sender, instance, created, **kwargs):
    """结算明细项保存时清除相关缓存"""
    try:
        if instance.settlement_id:
            settlement = instance.settlement
            user_fields = ['created_by', 'reviewed_by']
            cleared_count = clear_related_cache(settlement, user_fields)
            
            # 清除项目负责人的缓存
            if settlement.project_id:
                try:
                    project = settlement.project
                    if hasattr(project, 'project_manager') and project.project_manager_id:
                        CacheManager.clear_user_dashboard_cache(project.project_manager_id)
                        cleared_count += 1
                except Exception:
                    pass
            
            logger.debug(f'结算明细项保存，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除结算明细项缓存时出错: {e}')


@receiver(post_save, sender=OutputValueRecord)
def clear_cache_on_output_value_save(sender, instance, created, **kwargs):
    """产值记录保存时清除相关缓存"""
    try:
        user_fields = ['responsible_user', 'confirmed_by']
        cleared_count = clear_related_cache(instance, user_fields)
        
        # 清除项目负责人的缓存
        if instance.project_id:
            try:
                project = instance.project
                if hasattr(project, 'project_manager') and project.project_manager_id:
                    CacheManager.clear_user_dashboard_cache(project.project_manager_id)
                    cleared_count += 1
            except Exception:
                pass
        
        logger.debug(f'产值记录保存，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除产值记录缓存时出错: {e}')


@receiver(post_save, sender=PaymentRecord)
def clear_cache_on_payment_save(sender, instance, created, **kwargs):
    """回款记录保存时清除相关缓存"""
    try:
        user_fields = ['created_by', 'confirmed_by']
        cleared_count = clear_related_cache(instance, user_fields)
        logger.debug(f'回款记录保存，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除回款记录缓存时出错: {e}')


@receiver(post_save, sender=ContractSettlement)
def clear_cache_on_contract_settlement_save(sender, instance, created, **kwargs):
    """合同结算保存时清除相关缓存"""
    try:
        user_fields = ['created_by', 'submitted_by', 'approver', 'confirmed_by']
        cleared_count = clear_related_cache(instance, user_fields)
        logger.debug(f'合同结算保存，已清除 {cleared_count} 个用户缓存')
    except Exception as e:
        logger.error(f'清除合同结算缓存时出错: {e}')

