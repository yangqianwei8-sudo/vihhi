"""
档案管理模块信号处理器
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from backend.apps.delivery_customer.models import DeliveryRecord
from backend.apps.production_management.models import Project
from backend.apps.archive_management.models import ArchivePushRecord, ProjectArchiveDocument, ArchiveProjectArchive


@receiver(post_save, sender=DeliveryRecord)
def handle_delivery_archive_push(sender, instance, created, **kwargs):
    """
    监听交付记录状态变化，当状态为"已确认"或"已反馈"时，自动推送到档案管理模块
    """
    # 只处理状态为"已确认"或"已反馈"的记录
    if instance.status not in ['confirmed', 'feedback_received']:
        return
    
    # 检查是否已经推送过
    existing_push = ArchivePushRecord.objects.filter(
        delivery_record=instance,
        push_status='success'
    ).exists()
    
    if existing_push:
        return
    
    # 创建推送记录
    push_record = ArchivePushRecord.objects.create(
        delivery_record=instance,
        project=instance.project,
        push_status='pending',
        push_time=timezone.now()
    )
    
    # 异步处理推送（这里先同步处理，后续可以改为Celery任务）
    try:
        _process_delivery_push(push_record)
    except Exception as e:
        push_record.push_status = 'failed'
        push_record.error_message = str(e)
        push_record.save()


def _process_delivery_push(push_record):
    """
    处理交付推送：将交付文件推送到档案管理模块
    """
    delivery = push_record.delivery_record
    
    # 收集推送的文件列表
    pushed_files = []
    
    # 处理交付文件
    for delivery_file in delivery.files.all():
        # 创建项目档案文档
        document = ProjectArchiveDocument.objects.create(
            document_name=delivery_file.file_name,
            document_type='delivery_file',
            project=delivery.project,
            file=delivery_file.file,
            file_name=delivery_file.file_name,
            file_size=delivery_file.file_size,
            file_extension=delivery_file.file_extension or '',
            mime_type=delivery_file.mime_type or '',
            description=f'交付文件：{delivery.delivery_number}',
            status='archived',
            uploaded_by=delivery.created_by
        )
        
        pushed_files.append({
            'document_id': document.id,
            'document_number': document.document_number,
            'file_name': delivery_file.file_name,
        })
    
    # 更新推送记录
    push_record.push_status = 'success'
    push_record.receive_time = timezone.now()
    push_record.pushed_files = pushed_files
    push_record.save()


@receiver(post_save, sender=Project)
def handle_project_auto_archive(sender, instance, created, **kwargs):
    """
    监听项目状态变化，当项目满足归档条件时，自动触发归档
    注意：当前项目模型中还没有settled状态，改为检查结算记录状态
    """
    # 检查是否已经归档过
    existing_archive = ArchiveProjectArchive.objects.filter(
        project=instance,
        status='archived'
    ).exists()
    
    if existing_archive:
        return
    
    # 检查归档条件（不依赖项目状态，而是检查结算记录）
    if _check_project_archive_conditions(instance):
        # 创建归档记录
        applicant = getattr(instance, 'project_manager', None) or getattr(instance, 'created_by', None)
        if not applicant:
            return  # 如果没有申请人，跳过
        
        archive = ArchiveProjectArchive.objects.create(
            project=instance,
            archive_reason='项目结算完成，自动归档',
            archive_description='项目已结算，满足归档条件，系统自动触发归档',
            status='pending',
            applicant=applicant
        )
        
        # 异步处理归档（这里先同步处理，后续可以改为Celery任务）
        try:
            _process_project_archive(archive)
        except Exception as e:
            archive.status = 'rejected'
            archive.archive_description = f'自动归档失败：{str(e)}'
            archive.save()


def _check_project_archive_conditions(project):
    """
    检查项目是否满足归档条件
    条件：
    1. 项目有已确认的结算记录（结算状态为"已确认"）
    2. 项目复盘已完成（如果有复盘记录）
    3. 所有交付成果已完成（交付状态为"已确认"或"已反馈"）
    """
    # 条件1：检查是否有已确认的结算记录
    try:
        from backend.apps.settlement_center.models import ProjectSettlement
        confirmed_settlements = ProjectSettlement.objects.filter(
            project=project,
            status='confirmed'
        ).exists()
        
        if not confirmed_settlements:
            return False
    except ImportError:
        # 如果结算模块不存在，跳过此检查
        pass
    
    # 条件2：检查是否有未完成的交付记录
    incomplete_deliveries = DeliveryRecord.objects.filter(
        project=project
    ).exclude(
        status__in=['confirmed', 'feedback_received', 'archived', 'cancelled']
    ).exists()
    
    if incomplete_deliveries:
        return False
    
    # 条件3：检查项目复盘（如果有复盘功能）
    # TODO: 根据实际复盘模块实现检查逻辑
    
    return True


def _process_project_archive(archive):
    """
    处理项目归档：收集项目所有文件并归档
    """
    project = archive.project
    
    # 收集归档文件
    file_list = []
    
    # 1. 项目基本信息
    file_list.append({
        'type': 'project_info',
        'name': f'{project.project_number}_项目信息.json',
        'data': {
            'project_number': project.project_number,
            'project_name': project.project_name,
            'client': project.client.name if project.client else None,
            'contract_amount': str(project.contract_amount) if project.contract_amount else None,
        }
    })
    
    # 2. 图纸文件（从图纸管理模块获取）
    try:
        from backend.apps.production_management.models import ProjectDrawingFile, ProjectDrawingSubmission
        drawing_submissions = ProjectDrawingSubmission.objects.filter(project=project)
        for submission in drawing_submissions:
            drawing_files = ProjectDrawingFile.objects.filter(submission=submission)
            for drawing_file in drawing_files:
                file_list.append({
                    'type': 'drawing',
                    'submission_id': submission.id,
                    'drawing_file_id': drawing_file.id,
                    'name': drawing_file.name,
                    'category': drawing_file.category,
                })
    except ImportError:
        # 如果图纸管理模块不存在，跳过
        pass
    
    # 3. 意见文件（从意见管理模块获取）
    # TODO: 根据实际意见管理模块实现（如果存在意见管理模块）
    
    # 4. 交付文件（已自动归档的交付文件）
    delivery_documents = ProjectArchiveDocument.objects.filter(
        project=project,
        document_type='delivery_file',
        status='archived'
    )
    for doc in delivery_documents:
        file_list.append({
            'type': 'delivery_file',
            'document_id': doc.id,
            'document_number': doc.document_number,
            'name': doc.document_name,
        })
    
    # 5. 结算文件（从结算管理模块获取）
    try:
        from backend.apps.settlement_center.models import ProjectSettlement
        settlements = ProjectSettlement.objects.filter(project=project, status='confirmed')
        for settlement in settlements:
            if settlement.settlement_file:
                file_list.append({
                    'type': 'settlement',
                    'settlement_id': settlement.id,
                    'settlement_number': settlement.settlement_number,
                    'name': f'结算文件_{settlement.settlement_number}',
                    'file_path': settlement.settlement_file.name if settlement.settlement_file else None,
                })
    except ImportError:
        # 如果结算模块不存在，跳过
        pass
    
    # 6. 回款文件（从回款管理模块获取）
    try:
        from backend.apps.settlement_center.models import PaymentRecord
        # 注意：PaymentRecord可能通过payment_plan关联项目，需要根据实际模型结构调整
        # 这里简化处理，实际实现需要根据PaymentRecord的实际关联关系调整
        payment_records = PaymentRecord.objects.filter(
            payment_plan_type='project',
            status='confirmed'
        )
        # 需要通过payment_plan关联到project，这里简化处理
        for payment in payment_records:
            if payment.receipt_voucher:
                file_list.append({
                    'type': 'payment',
                    'payment_id': payment.id,
                    'payment_number': payment.payment_number,
                    'name': f'回款凭证_{payment.payment_number}',
                    'file_path': payment.receipt_voucher.name if payment.receipt_voucher else None,
                })
    except ImportError:
        # 如果回款模块不存在，跳过
        pass
    
    # 更新归档记录
    archive.file_list = file_list
    archive.status = 'archiving'
    archive.executor = archive.applicant  # 临时使用申请人作为执行人
    archive.executed_time = timezone.now()
    archive.save()
    
    # 归档完成后，状态更新为"已归档"
    archive.status = 'archived'
    archive.confirmed_by = archive.executor
    archive.confirmed_time = timezone.now()
    archive.save()

