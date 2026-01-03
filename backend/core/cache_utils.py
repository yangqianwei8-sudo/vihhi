"""
缓存工具模块
提供统一的缓存管理功能
"""
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    # 缓存键前缀
    DASHBOARD_STATS_PREFIX = 'dashboard_stats_'
    DASHBOARD_TODOS_PREFIX = 'dashboard_todos_'
    CACHE_INVALIDATION_KEY = 'dashboard_cache_invalidated'
    
    @classmethod
    def clear_user_dashboard_cache(cls, user_id):
        """清除指定用户的仪表盘缓存"""
        if not user_id:
            return
        
        cache_keys = [
            f'{cls.DASHBOARD_STATS_PREFIX}{user_id}',
            f'{cls.DASHBOARD_TODOS_PREFIX}{user_id}',
        ]
        
        cleared_count = 0
        for key in cache_keys:
            if cache.delete(key):
                cleared_count += 1
                logger.debug(f'已清除缓存: {key}')
        
        logger.info(f'已清除用户 {user_id} 的 {cleared_count} 个仪表盘缓存')
        return cleared_count
    
    @classmethod
    def clear_all_dashboard_cache(cls):
        """标记所有仪表盘缓存为无效"""
        cache.set(cls.CACHE_INVALIDATION_KEY, True, 300)  # 5分钟内有效
        logger.info('已标记所有仪表盘缓存为无效')
    
    @classmethod
    def is_cache_invalidated(cls):
        """检查缓存是否被标记为无效"""
        return cache.get(cls.CACHE_INVALIDATION_KEY, False)
    
    @classmethod
    def reset_cache_invalidation(cls):
        """重置缓存失效标记"""
        cache.delete(cls.CACHE_INVALIDATION_KEY)
        logger.debug('已重置缓存失效标记')
    
    @classmethod
    def get_with_invalidation_check(cls, key, default=None):
        """获取缓存值，同时检查全局失效标记"""
        if cls.is_cache_invalidated():
            return None
        return cache.get(key, default)
    
    @classmethod
    def set_with_prefix(cls, prefix, key, value, timeout=None):
        """使用前缀设置缓存"""
        full_key = f'{prefix}{key}'
        cache.set(full_key, value, timeout)
        return full_key
    
    @classmethod
    def delete_with_prefix(cls, prefix, key):
        """使用前缀删除缓存"""
        full_key = f'{prefix}{key}'
        return cache.delete(full_key)
    
    @classmethod
    def clear_pattern(cls, pattern_prefix):
        """
        清除匹配前缀的所有缓存
        注意：Django 默认缓存后端不支持通配符删除
        如果使用 Redis，可以通过维护键列表或使用 Redis 的 keys 命令实现
        """
        # 对于不支持通配符的缓存后端，使用失效标记
        cls.clear_all_dashboard_cache()
        logger.warning(f'缓存后端不支持通配符删除，已使用全局失效标记替代')


def clear_related_cache(model_instance, user_fields=None):
    """
    清除与模型实例相关的缓存
    
    Args:
        model_instance: 模型实例
        user_fields: 用户字段列表，例如 ['created_by', 'project_manager']
    """
    if user_fields is None:
        user_fields = ['created_by', 'responsible_user', 'project_manager']
    
    cleared_users = set()
    
    # 从实例中提取用户ID
    for field_name in user_fields:
        if hasattr(model_instance, field_name):
            user_field = getattr(model_instance, field_name, None)
            if user_field:
                user_id = user_field.id if hasattr(user_field, 'id') else user_field
                if user_id:
                    cleared_users.add(user_id)
    
    # 清除相关用户的缓存
    for user_id in cleared_users:
        CacheManager.clear_user_dashboard_cache(user_id)
    
    return len(cleared_users)



