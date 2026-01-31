"""
共享基础数据模型
供合同、商机、客户、生产等模块通过数据交互引用
"""
from django.db import models


class ServiceType(models.Model):
    """服务类型"""
    code = models.CharField(max_length=50, unique=True, verbose_name='服务类型编码')
    name = models.CharField(max_length=100, verbose_name='服务类型名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_service_type'
        verbose_name = '服务类型'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class ServiceProfession(models.Model):
    """服务专业"""
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='professions', verbose_name='所属服务类型')
    code = models.CharField(max_length=50, verbose_name='服务专业编码')
    name = models.CharField(max_length=100, verbose_name='服务专业名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_service_profession'
        verbose_name = '服务专业'
        verbose_name_plural = verbose_name
        ordering = ['service_type__order', 'order', 'id']
        unique_together = ('service_type', 'code')

    def __str__(self):
        return f"{self.service_type.name} - {self.name}"


class BusinessType(models.Model):
    """项目业态"""
    code = models.CharField(max_length=50, unique=True, verbose_name='业态编码')
    name = models.CharField(max_length=100, verbose_name='业态名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='业态描述')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_business_type'
        verbose_name = '项目业态'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class DesignStage(models.Model):
    """图纸阶段"""
    code = models.CharField(max_length=50, unique=True, verbose_name='阶段编码')
    name = models.CharField(max_length=100, verbose_name='阶段名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='阶段描述')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_design_stage'
        verbose_name = '图纸阶段'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class StructureType(models.Model):
    """结构形式"""
    code = models.CharField(max_length=50, unique=True, verbose_name='结构形式编码')
    name = models.CharField(max_length=100, verbose_name='结构形式名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='结构形式描述')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_structure_type'
        verbose_name = '结构形式'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class DesignUnitCategory(models.Model):
    """设计单位分类"""
    code = models.CharField(max_length=50, unique=True, verbose_name='分类编码')
    name = models.CharField(max_length=100, verbose_name='分类名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='分类描述')

    class Meta:
        app_label = 'base_data'
        db_table = 'production_management_design_unit_category'
        verbose_name = '设计单位分类'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name
