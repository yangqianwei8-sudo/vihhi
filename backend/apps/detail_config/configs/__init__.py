"""
配置模块
提供详情页配置类定义和配置示例
"""

from .field_types import (
    FieldConfig,
    SectionConfig,
    TabConfig,
    ActionConfig,
    DetailPageConfig,
)

from .template_configs import (
    INCOMING_DOCUMENT_DETAIL_CONFIG,
    CUSTOMER_DETAIL_CONFIG,
)

__all__ = [
    'FieldConfig',
    'SectionConfig',
    'TabConfig',
    'ActionConfig',
    'DetailPageConfig',
    'INCOMING_DOCUMENT_DETAIL_CONFIG',
    'CUSTOMER_DETAIL_CONFIG',
]
