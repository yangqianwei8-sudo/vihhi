"""
统一编号生成服务
提供系统统一的编号生成功能，支持多种编号格式和序列号策略
"""
import re
import logging
from typing import Optional, Dict, Any
from datetime import date, datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Model, Max, Q
from django.core.cache import cache

logger = logging.getLogger(__name__)


class NumberGeneratorService:
    """
    统一编号生成服务
    
    支持的编号格式：
    1. 前缀 + 日期 + 序列号：{prefix}-{date}-{seq}
    2. 前缀 + 日期：{prefix}-{date}
    3. 前缀 + 序列号：{prefix}-{seq}
    4. 前缀 + 关联对象编号 + 序列号：{prefix}-{related_number}-{seq}
    5. 自定义格式：通过模板字符串定义
    
    支持的序列号策略：
    1. daily: 按日期重置（每天从1开始）
    2. monthly: 按月重置（每月从1开始）
    3. yearly: 按年重置（每年从1开始）
    4. global: 全局累计（永不重置）
    5. related: 按关联对象分组累计
    """
    
    # 默认配置
    DEFAULT_SEQ_LENGTH = 4  # 默认序列号长度
    MAX_RETRY_COUNT = 100  # 最大重试次数
    
    @staticmethod
    def generate(
        model_class: type[Model],
        field_name: str = 'number',
        prefix: str = '',
        date_format: Optional[str] = None,
        seq_length: int = DEFAULT_SEQ_LENGTH,
        seq_strategy: str = 'daily',
        related_field: Optional[str] = None,
        related_value: Optional[Any] = None,
        template: Optional[str] = None,
        filter_conditions: Optional[Dict] = None,
        cache_key_prefix: Optional[str] = None,
    ) -> str:
        """
        生成编号
        
        Args:
            model_class: 模型类
            field_name: 编号字段名（默认为'number'）
            prefix: 编号前缀（如'VIH-JF'、'SW'等）
            date_format: 日期格式（如'%Y%m%d'、'%Y'等），None表示不使用日期
            seq_length: 序列号长度（默认4位）
            seq_strategy: 序列号策略（'daily'、'monthly'、'yearly'、'global'、'related'）
            related_field: 关联字段名（用于related策略）
            related_value: 关联字段值（用于related策略）
            template: 自定义模板（如'{prefix}-{date}-{seq:04d}'），如果提供则优先使用
            filter_conditions: 额外的过滤条件（字典格式）
            cache_key_prefix: 缓存键前缀（用于提高性能）
        
        Returns:
            str: 生成的编号
        
        Examples:
            # 交付单号：VIH-JF-20250101-0001
            NumberGeneratorService.generate(
                DeliveryRecord,
                field_name='delivery_number',
                prefix='VIH-JF',
                date_format='%Y%m%d',
                seq_strategy='daily'
            )
            
            # 收文编号：SW20250001
            NumberGeneratorService.generate(
                IncomingDocument,
                field_name='document_number',
                prefix='SW',
                date_format='%Y',
                seq_strategy='yearly'
            )
            
            # 结算单号：VIH-JS-项目编号-0001
            NumberGeneratorService.generate(
                ProjectSettlement,
                field_name='settlement_number',
                prefix='VIH-JS',
                related_field='project__project_number',
                related_value=project_number,
                seq_strategy='related'
            )
        """
        # 使用事务确保并发安全
        with transaction.atomic():
            # 获取当前日期信息
            now = timezone.now()
            today = now.date()
            
            # 构建日期字符串
            date_str = ''
            if date_format:
                if seq_strategy == 'daily':
                    date_str = today.strftime(date_format)
                elif seq_strategy == 'monthly':
                    date_str = today.strftime(date_format.replace('%d', '').replace('-%d', '').replace('%d-', ''))
                elif seq_strategy == 'yearly':
                    date_str = today.strftime(date_format.replace('%m', '').replace('%d', '').replace('-%m', '').replace('-%d', '').replace('%m-', '').replace('%d-', ''))
                else:
                    date_str = today.strftime(date_format)
            
            # 构建查询过滤条件
            filters = {}
            
            # 根据序列号策略构建过滤条件
            if seq_strategy == 'daily':
                # 按日期过滤
                if date_format:
                    pattern = f"{prefix}-{date_str}-" if prefix else f"{date_str}-"
                else:
                    pattern = f"{prefix}-" if prefix else ""
            elif seq_strategy == 'monthly':
                # 按月过滤
                month_str = today.strftime('%Y%m')
                if date_format:
                    pattern = f"{prefix}-{month_str}-" if prefix else f"{month_str}-"
                else:
                    pattern = f"{prefix}-" if prefix else ""
            elif seq_strategy == 'yearly':
                # 按年过滤
                year_str = today.strftime('%Y')
                if date_format:
                    pattern = f"{prefix}{year_str}" if not prefix or date_format == '%Y' else f"{prefix}-{year_str}-"
                else:
                    pattern = f"{prefix}-" if prefix else ""
            elif seq_strategy == 'related':
                # 按关联对象过滤
                if related_field and related_value:
                    filters[related_field] = related_value
                    pattern = f"{prefix}-{related_value}-" if prefix else f"{related_value}-"
                else:
                    pattern = f"{prefix}-" if prefix else ""
            else:  # global
                # 全局累计
                pattern = f"{prefix}-" if prefix else ""
            
            # 添加额外的过滤条件
            if filter_conditions:
                filters.update(filter_conditions)
            
            # 构建查询
            query = Q()
            if pattern:
                query = Q(**{f"{field_name}__startswith": pattern})
            
            # 添加其他过滤条件
            for key, value in filters.items():
                if '__' in key:
                    # 处理关联字段查询
                    query &= Q(**{key: value})
                else:
                    query &= Q(**{key: value})
            
            # 获取最大编号
            max_number = model_class.objects.filter(query).aggregate(
                max_num=Max(field_name)
            )['max_num']
            
            # 计算下一个序列号
            if max_number:
                # 从最大编号中提取序列号
                seq = NumberGeneratorService._extract_sequence(
                    max_number, pattern, seq_length
                )
                seq += 1
            else:
                seq = 1
            
            # 检查序列号是否超出范围
            max_seq = 10 ** seq_length - 1
            if seq > max_seq:
                raise ValueError(
                    f"编号序列号已达到最大值{max_seq}，无法生成新的编号。"
                    f"请考虑调整编号规则或增加序列号长度。"
                )
            
            # 生成编号
            if template:
                # 使用自定义模板
                number = template.format(
                    prefix=prefix,
                    date=date_str,
                    seq=seq,
                    seq_formatted=f"{seq:0{seq_length}d}",
                    related=related_value or '',
                    year=today.strftime('%Y'),
                    month=today.strftime('%m'),
                    day=today.strftime('%d'),
                )
            else:
                # 使用默认格式
                if date_format and related_value:
                    # 前缀 + 日期 + 关联值 + 序列号
                    number = f"{prefix}-{date_str}-{related_value}-{seq:0{seq_length}d}"
                elif date_format:
                    # 前缀 + 日期 + 序列号
                    if prefix and date_str:
                        number = f"{prefix}-{date_str}-{seq:0{seq_length}d}"
                    elif prefix:
                        number = f"{prefix}{date_str}{seq:0{seq_length}d}"
                    else:
                        number = f"{date_str}{seq:0{seq_length}d}"
                elif related_value:
                    # 前缀 + 关联值 + 序列号
                    number = f"{prefix}-{related_value}-{seq:0{seq_length}d}"
                else:
                    # 前缀 + 序列号
                    if prefix:
                        number = f"{prefix}-{seq:0{seq_length}d}"
                    else:
                        number = f"{seq:0{seq_length}d}"
            
            # 确保编号唯一（处理并发情况）
            attempt_count = 0
            while model_class.objects.filter(**{field_name: number}).exists():
                attempt_count += 1
                if attempt_count > NumberGeneratorService.MAX_RETRY_COUNT:
                    raise ValueError(
                        f"无法生成唯一的编号，已尝试{NumberGeneratorService.MAX_RETRY_COUNT}次。"
                        f"请检查编号规则配置。"
                    )
                
                seq += 1
                if seq > max_seq:
                    raise ValueError(
                        f"编号序列号已达到最大值{max_seq}，无法生成新的编号。"
                    )
                
                # 重新生成编号
                if template:
                    number = template.format(
                        prefix=prefix,
                        date=date_str,
                        seq=seq,
                        seq_formatted=f"{seq:0{seq_length}d}",
                        related=related_value or '',
                        year=today.strftime('%Y'),
                        month=today.strftime('%m'),
                        day=today.strftime('%d'),
                    )
                else:
                    if date_format and related_value:
                        number = f"{prefix}-{date_str}-{related_value}-{seq:0{seq_length}d}"
                    elif date_format:
                        if prefix and date_str:
                            number = f"{prefix}-{date_str}-{seq:0{seq_length}d}"
                        elif prefix:
                            number = f"{prefix}{date_str}{seq:0{seq_length}d}"
                        else:
                            number = f"{date_str}{seq:0{seq_length}d}"
                    elif related_value:
                        number = f"{prefix}-{related_value}-{seq:0{seq_length}d}"
                    else:
                        if prefix:
                            number = f"{prefix}-{seq:0{seq_length}d}"
                        else:
                            number = f"{seq:0{seq_length}d}"
            
            logger.info(
                f"生成编号成功: {number}, "
                f"模型: {model_class.__name__}, "
                f"字段: {field_name}, "
                f"策略: {seq_strategy}"
            )
            
            return number
    
    @staticmethod
    def _extract_sequence(number: str, pattern: str, seq_length: int) -> int:
        """
        从编号中提取序列号
        
        Args:
            number: 完整编号
            pattern: 编号模式（用于定位序列号位置）
            seq_length: 序列号长度
        
        Returns:
            int: 序列号
        """
        if not number:
            return 0
        
        try:
            # 方法1：如果pattern以-结尾，提取最后一个-后面的数字
            if pattern.endswith('-'):
                parts = number.split('-')
                if parts:
                    last_part = parts[-1]
                    if last_part.isdigit():
                        return int(last_part)
            
            # 方法2：提取编号末尾的指定长度数字
            if number:
                # 尝试提取最后seq_length位数字
                match = re.search(rf'\d{{{seq_length}}}$', number)
                if match:
                    return int(match.group())
                
                # 如果失败，尝试提取所有末尾数字
                match = re.search(r'(\d+)$', number)
                if match:
                    return int(match.group())
            
            # 方法3：如果pattern存在，尝试从pattern之后提取
            if pattern and pattern in number:
                suffix = number[len(pattern):]
                match = re.search(r'^\d+', suffix)
                if match:
                    return int(match.group())
            
            # 默认返回0
            return 0
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"提取序列号失败: {number}, 错误: {e}")
            return 0
    
    @staticmethod
    def generate_by_rule(
        rule_code: str,
        model_class: type[Model],
        field_name: str = 'number',
        related_value: Optional[Any] = None,
        **kwargs
    ) -> str:
        """
        根据规则代码生成编号（需要配合NumberRule模型使用）
        
        Args:
            rule_code: 规则代码
            model_class: 模型类
            field_name: 编号字段名
            related_value: 关联值
            **kwargs: 其他参数
        
        Returns:
            str: 生成的编号
        """
        # 这里可以扩展为从数据库读取规则配置
        # 目前先返回基础生成方法
        return NumberGeneratorService.generate(
            model_class=model_class,
            field_name=field_name,
            related_value=related_value,
            **kwargs
        )


# ==================== 便捷方法 ====================

def generate_delivery_number(model_class, instance=None):
    """生成交付单号：VIH-JF-YYYYMMDD-0001"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='delivery_number',
        prefix='VIH-JF',
        date_format='%Y%m%d',
        seq_strategy='daily',
        seq_length=4
    )


def generate_incoming_document_number(model_class, instance=None):
    """生成收文编号：SWYYYY0001"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='document_number',
        prefix='SW',
        date_format='%Y',
        seq_strategy='yearly',
        seq_length=4
    )


def generate_outgoing_document_number(model_class, instance=None):
    """生成发文编号：FWYYYY0001"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='document_number',
        prefix='FW',
        date_format='%Y',
        seq_strategy='yearly',
        seq_length=4
    )


def generate_settlement_number(model_class, project_number, instance=None):
    """生成结算单号：VIH-JS-项目编号-0001"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='settlement_number',
        prefix='VIH-JS',
        related_field='project__project_number',
        related_value=project_number,
        seq_strategy='related',
        seq_length=4
    )


def generate_approval_instance_number(model_class, workflow_code, instance=None):
    """生成审批实例编号：{workflow_code}-YYYYMMDD-0001"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='instance_number',
        prefix=workflow_code,
        date_format='%Y%m%d',
        seq_strategy='daily',
        seq_length=4
    )

