"""
档案管理模块序列化器
"""
from rest_framework import serializers
from backend.apps.archive_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveStorageRoom,
    ArchiveLocation,
    ArchiveShelf,
    ArchiveInventory,
)
from backend.apps.production_management.models import Project
from backend.apps.delivery_customer.models import DeliveryRecord


class ArchiveCategorySerializer(serializers.ModelSerializer):
    """档案分类序列化器"""
    children_count = serializers.SerializerMethodField()
    archive_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveCategory
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_archive_count(self, obj):
        return obj.archive_count


class ProjectArchiveSerializer(serializers.ModelSerializer):
    """项目归档序列化器"""
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    executor_name = serializers.CharField(source='executor.username', read_only=True)
    
    class Meta:
        model = ArchiveProjectArchive
        fields = '__all__'
        read_only_fields = ['archive_number', 'created_time', 'updated_time']


class ProjectArchiveDocumentSerializer(serializers.ModelSerializer):
    """项目档案文档序列化器"""
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectArchiveDocument
        fields = '__all__'
        read_only_fields = ['document_number', 'uploaded_time', 'updated_time']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class ArchivePushRecordSerializer(serializers.ModelSerializer):
    """交付推送记录序列化器"""
    delivery_number = serializers.CharField(source='delivery_record.delivery_number', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    
    class Meta:
        model = ArchivePushRecord
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time']


class AdministrativeArchiveSerializer(serializers.ModelSerializer):
    """行政档案序列化器"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    archivist_name = serializers.CharField(source='archivist.username', read_only=True)
    department_name = serializers.CharField(source='archive_department.name', read_only=True)
    storage_room_name = serializers.CharField(source='storage_room.room_name', read_only=True)
    location_name = serializers.CharField(source='location.location_name', read_only=True)
    
    class Meta:
        model = AdministrativeArchive
        fields = '__all__'
        read_only_fields = ['archive_number', 'created_time', 'updated_time']


class ArchiveBorrowSerializer(serializers.ModelSerializer):
    """档案借阅序列化器"""
    borrower_name = serializers.CharField(source='borrower.username', read_only=True)
    archive_name = serializers.SerializerMethodField()
    archive_number = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveBorrow
        fields = '__all__'
        read_only_fields = ['borrow_number', 'created_time', 'updated_time']
    
    def get_archive_name(self, obj):
        if obj.project_document:
            return obj.project_document.document_name
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_name
        return None
    
    def get_archive_number(self, obj):
        if obj.project_document:
            return obj.project_document.document_number
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_number
        return None
    
    def get_is_overdue(self, obj):
        return obj.is_overdue


class ArchiveDestroySerializer(serializers.ModelSerializer):
    """档案销毁序列化器"""
    destroyer_name = serializers.CharField(source='destroyer.username', read_only=True)
    archive_name = serializers.SerializerMethodField()
    archive_number = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveDestroy
        fields = '__all__'
        read_only_fields = ['destroy_number', 'created_time', 'updated_time']
    
    def get_archive_name(self, obj):
        if obj.project_document:
            return obj.project_document.document_name
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_name
        return None
    
    def get_archive_number(self, obj):
        if obj.project_document:
            return obj.project_document.document_number
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_number
        return None


class ArchiveStorageRoomSerializer(serializers.ModelSerializer):
    """档案库房序列化器"""
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    archive_count = serializers.SerializerMethodField()
    usage_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveStorageRoom
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time']
    
    def get_archive_count(self, obj):
        return obj.archive_count
    
    def get_usage_rate(self, obj):
        return obj.usage_rate


class ArchiveLocationSerializer(serializers.ModelSerializer):
    """档案位置序列化器"""
    storage_room_name = serializers.CharField(source='storage_room.room_name', read_only=True)
    archive_count = serializers.SerializerMethodField()
    usage_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveLocation
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time']
    
    def get_archive_count(self, obj):
        return obj.archive_count
    
    def get_usage_rate(self, obj):
        return obj.usage_rate


class ArchiveShelfSerializer(serializers.ModelSerializer):
    """档案上架记录序列化器"""
    archive_number = serializers.CharField(source='archive.archive_number', read_only=True)
    location_number = serializers.CharField(source='location.location_number', read_only=True)
    shelf_by_name = serializers.CharField(source='shelf_by.username', read_only=True)
    
    class Meta:
        model = ArchiveShelf
        fields = '__all__'


class ArchiveInventorySerializer(serializers.ModelSerializer):
    """档案盘点序列化器"""
    inventory_by_name = serializers.CharField(source='inventory_by.username', read_only=True)
    storage_room_name = serializers.CharField(source='storage_room.room_name', read_only=True)
    
    class Meta:
        model = ArchiveInventory
        fields = '__all__'
        read_only_fields = ['inventory_number', 'created_time', 'updated_time']

