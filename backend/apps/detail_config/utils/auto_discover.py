"""
自动字段发现工具
从Django模型自动发现所有字段并生成详情页配置
"""
from typing import List, Dict, Any, Optional
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from ..configs.field_types import FieldConfig, SectionConfig, DetailPageConfig


def infer_field_type(field: models.Field) -> tuple[str, Optional[str]]:
    """
    根据Django字段类型推断详情页字段类型和格式
    
    Returns:
        (field_type, format_type) 元组
    """
    field_type = "text"
    format_type = None
    
    # 日期时间字段
    if isinstance(field, models.DateTimeField):
        field_type = "datetime"
        format_type = "datetime"
    elif isinstance(field, models.DateField):
        field_type = "date"
        format_type = "date"
    elif isinstance(field, models.TimeField):
        field_type = "text"
        format_type = None
    
    # 数字字段
    elif isinstance(field, (models.DecimalField, models.FloatField)):
        # 检查字段名是否包含金额相关关键词
        field_name_lower = field.name.lower()
        if any(keyword in field_name_lower for keyword in ['amount', 'price', 'cost', 'fee', 'money', 'capital', '金额', '价格', '费用', '成本', '资金']):
            field_type = "currency"
            format_type = "currency"
        elif any(keyword in field_name_lower for keyword in ['percent', 'rate', 'ratio', '百分比', '比率']):
            field_type = "percent"
            format_type = "percent"
        else:
            field_type = "text"
    elif isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField, models.PositiveIntegerField)):
        # 检查是否是评分字段
        field_name_lower = field.name.lower()
        if 'score' in field_name_lower or '评分' in field_name_lower:
            field_type = "text"
        elif 'count' in field_name_lower or '数量' in field_name_lower:
            field_type = "text"
        else:
            field_type = "text"
    
    # 布尔字段
    elif isinstance(field, models.BooleanField):
        field_type = "status"
    
    # 邮箱字段
    elif isinstance(field, models.EmailField):
        field_type = "email"
    
    # URL字段
    elif isinstance(field, models.URLField):
        field_type = "link"
    
    # 外键字段
    elif isinstance(field, models.ForeignKey):
        field_type = "text"  # 外键会通过get_XXX_display或相关对象属性显示
    
    # 多对多字段
    elif isinstance(field, models.ManyToManyField):
        field_type = "tag"  # 多对多字段显示为标签
    
    # 有choices的字段
    if hasattr(field, 'choices') and field.choices:
        field_type = "status"
    
    return field_type, format_type


def get_field_display_name(field: models.Field) -> str:
    """获取字段的显示名称"""
    return getattr(field, 'verbose_name', None) or field.name


def should_skip_field(field: models.Field) -> bool:
    """判断是否应该跳过某个字段"""
    # 跳过主键（id字段通常不需要显示）
    if isinstance(field, models.AutoField) and field.name == 'id':
        return True
    
    # 跳过ManyToManyField（通常通过关联对象显示）
    if isinstance(field, models.ManyToManyField):
        return True
    
    return False


def get_field_id_for_display(field: models.Field, model_instance: Any) -> str:
    """
    获取用于显示的字段ID
    
    对于choices字段，返回get_XXX_display
    对于ForeignKey，尝试返回相关对象的显示名称
    """
    field_name = field.name
    
    # 如果有choices，使用get_XXX_display
    if hasattr(field, 'choices') and field.choices:
        return f"get_{field_name}_display"
    
    # 如果是ForeignKey，尝试获取相关对象的显示方法
    if isinstance(field, models.ForeignKey):
        # 检查相关模型的类型，决定使用什么显示方法
        try:
            related_model = field.related_model
            # 如果是User模型，使用get_full_name
            if related_model and hasattr(related_model, 'get_full_name'):
                return f"{field_name}.get_full_name"
            # 其他情况使用字段名，让get_field_value处理__str__
            return field_name
        except:
            return field_name
    
    return field_name


def categorize_fields(fields: List[models.Field]) -> Dict[str, List[models.Field]]:
    """
    将字段分类到不同的组
    
    Returns:
        Dict[section_name, List[Field]]
    """
    categories = {
        '基本信息': [],
        '企业信息': [],
        '分类信息': [],
        '联系信息': [],
        '财务信息': [],
        '法律风险信息': [],
        '状态信息': [],
        '负责人信息': [],
        '公海信息': [],
        '审计信息': [],
        '其他信息': [],
    }
    
    # 关键词映射
    keyword_mapping = {
        '基本信息': ['name', 'number', 'code', '编号', '名称', '简称', 'credit_code', '统一信用', 'customer_number'],
        '企业信息': ['legal', 'representative', 'established', 'registered', 'capital', 'company', 'address', '法定代表人', '成立日期', '注册资本', '企业', '公司'],
        '分类信息': ['level', 'grade', 'type', 'industry', 'region', 'source', 'credit_level', '等级', '分级', '类型', '行业', '区域', '来源', '信用'],
        '联系信息': ['contact', 'phone', 'email', 'address', '联系人', '电话', '邮箱', '地址', 'position', '职务'],
        '财务信息': ['amount', 'payment', 'contract', 'score', 'health_score', '金额', '回款', '合同', '评分', 'total_contract', 'total_payment'],
        '法律风险信息': ['legal_risk', 'litigation', 'executed', 'case', 'consumption', 'execution', '法律风险', '司法', '执行', '案件', '限制消费', '终本'],
        '状态信息': ['is_active', 'status', 'active', '状态', '活跃'],
        '负责人信息': ['responsible', '负责人'],
        '公海信息': ['public_sea', '公海'],
        '审计信息': ['created', 'updated', 'by', 'time', '创建', '更新', '时间'],
    }
    
    for field in fields:
        field_name_lower = field.name.lower()
        categorized = False
        
        # 根据关键词分类
        for category, keywords in keyword_mapping.items():
            if any(keyword in field_name_lower for keyword in keywords):
                categories[category].append(field)
                categorized = True
                break
        
        # 如果没有匹配到，根据字段类型分类
        if not categorized:
            if isinstance(field, (models.DateTimeField, models.DateField)):
                if 'created' in field_name_lower or 'updated' in field_name_lower:
                    categories['审计信息'].append(field)
                else:
                    categories['其他信息'].append(field)
            elif isinstance(field, models.ForeignKey):
                if 'user' in field_name_lower or 'by' in field_name_lower:
                    categories['审计信息'].append(field)
                else:
                    categories['其他信息'].append(field)
            else:
                categories['其他信息'].append(field)
    
    # 移除空分类
    return {k: v for k, v in categories.items() if v}


def auto_discover_fields(model_instance: Any) -> List[FieldConfig]:
    """
    自动发现模型的所有字段并生成FieldConfig列表
    
    Args:
        model_instance: Django模型实例
    
    Returns:
        List[FieldConfig]: 字段配置列表
    """
    if not hasattr(model_instance, '_meta'):
        return []
    
    field_configs = []
    model_meta = model_instance._meta
    
    # 获取所有concrete字段（不包括ManyToMany）
    concrete_fields = [f for f in model_meta.concrete_fields if not isinstance(f, models.ManyToManyField)]
    
    # 为每个字段创建FieldConfig
    for field in concrete_fields:
        if should_skip_field(field):
            continue
            
        field_type, format_type = infer_field_type(field)
        field_id = get_field_id_for_display(field, model_instance)
        label = get_field_display_name(field)
        
        # 根据字段类型确定span
        span = 12
        if field_type in ['status', 'date', 'datetime', 'email', 'phone']:
            span = 6
        elif field_type in ['currency', 'percent']:
            span = 6
        
        field_config = FieldConfig(
            id=field_id,
            label=label,
            type=field_type,
            span=span,
            format=format_type,
        )
        field_configs.append(field_config)
    
    return field_configs


def build_auto_config(model_instance: Any, title: str = None, layout: str = "standard") -> DetailPageConfig:
    """
    自动构建详情页配置
    
    Args:
        model_instance: Django模型实例
        title: 页面标题（如果不提供，使用模型的verbose_name）
        layout: 布局模式（standard或tabbed）
    
    Returns:
        DetailPageConfig: 完整的详情页配置
    """
    if not hasattr(model_instance, '_meta'):
        raise ValueError("model_instance must be a Django model instance")
    
    model_meta = model_instance._meta
    page_title = title or getattr(model_meta, 'verbose_name', '详情')
    
    # 获取所有concrete字段
    concrete_fields = [f for f in model_meta.concrete_fields if not isinstance(f, models.ManyToManyField)]
    
    # 分类字段
    categorized = categorize_fields(concrete_fields)
    
    # 为每个分类创建SectionConfig
    sections = []
    for section_name, fields in categorized.items():
        field_configs = []
        for field in fields:
            if should_skip_field(field):
                continue
                
            field_type, format_type = infer_field_type(field)
            field_id = get_field_id_for_display(field, model_instance)
            label = get_field_display_name(field)
            
            # 根据字段类型确定span
            span = 12
            if field_type in ['status', 'date', 'datetime', 'email', 'phone', 'currency', 'percent']:
                span = 6
            
            field_config = FieldConfig(
                id=field_id,
                label=label,
                type=field_type,
                span=span,
                format=format_type,
            )
            field_configs.append(field_config)
        
        if field_configs:
            section = SectionConfig(
                id=section_name.lower().replace('信息', '-info').replace(' ', '-'),
                title=section_name,
                layout="grid",
                columns=2,
                fields=field_configs,
            )
            sections.append(section)
    
    # 如果没有分类，创建一个默认分类包含所有字段
    if not sections:
        all_field_configs = auto_discover_fields(model_instance)
        if all_field_configs:
            sections.append(SectionConfig(
                id="all-info",
                title="全部信息",
                layout="grid",
                columns=2,
                fields=all_field_configs,
            ))
    
    return DetailPageConfig(
        title=page_title,
        layout=layout,
        sections=sections,
        timeline_enabled=True,
    )

