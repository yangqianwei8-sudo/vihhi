"""
数据格式化工具
提供各种数据格式化功能
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional


def format_value(value: Any, format_type: Optional[str] = None) -> str:
    """
    格式化值
    
    Args:
        value: 要格式化的值
        format_type: 格式化类型（currency, date, datetime, percent）
    
    Returns:
        格式化后的字符串
    """
    if value is None:
        return "—"
    
    if format_type == 'currency':
        if isinstance(value, (int, float, Decimal)):
            return f"¥{value:,.2f}"
        return str(value)
    
    elif format_type == 'percent':
        if isinstance(value, (int, float)):
            return f"{value:.2f}%"
        return str(value)
    
    elif format_type == 'date':
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        return str(value)
    
    elif format_type == 'datetime':
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)
    
    # 默认返回字符串
    return str(value) if value else "—"

