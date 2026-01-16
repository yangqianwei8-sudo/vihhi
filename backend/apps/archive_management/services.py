"""
档案管理模块业务逻辑服务层
"""
from django.utils import timezone
from django.db.models import Q
from typing import List, Dict, Optional

from backend.apps.system_management.models import User
from backend.apps.production_management.models import Project
from backend.apps.delivery_customer.models import DeliveryRecord
from backend.apps.archive_management.models import (
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveCategory,
)

# 尝试导入扩展模型
try:
    from backend.apps.archive_management.models import ArchiveOperationLog
    ARCHIVE_OPERATION_LOG_AVAILABLE = True
except ImportError:
    ARCHIVE_OPERATION_LOG_AVAILABLE = False


class ArchivePushService:
    """交付推送服务"""
    
    @staticmethod
    def push_delivery_to_archive(delivery_record: DeliveryRecord, user: User) -> ArchivePushRecord:
        """
        手动推送交付记录到档案管理模块
        """
        # 检查是否已经推送过
        existing_push = ArchivePushRecord.objects.filter(
            delivery_record=delivery_record,
            push_status='success'
        ).first()
        
        if existing_push:
            return existing_push
        
        # 创建推送记录
        push_record = ArchivePushRecord.objects.create(
            delivery_record=delivery_record,
            project=delivery_record.project,
            push_status='pending',
            push_time=timezone.now()
        )
        
        # 处理推送
        try:
            ArchivePushService._process_push(push_record)
        except Exception as e:
            push_record.push_status = 'failed'
            push_record.error_message = str(e)
            push_record.save()
            raise
        
        return push_record
    
    @staticmethod
    def _process_push(push_record: ArchivePushRecord):
        """处理推送逻辑"""
        delivery = push_record.delivery_record
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
    
    @staticmethod
    def retry_push(push_record: ArchivePushRecord) -> ArchivePushRecord:
        """重试推送"""
        push_record.push_status = 'retrying'
        push_record.retry_count += 1
        push_record.save()
        
        try:
            ArchivePushService._process_push(push_record)
        except Exception as e:
            push_record.push_status = 'failed'
            push_record.error_message = str(e)
            push_record.save()
            raise
        
        return push_record


class ProjectArchiveService:
    """项目归档服务"""
    
    @staticmethod
    def check_archive_conditions(project: Project) -> Dict[str, any]:
        """
        检查项目是否满足归档条件
        返回检查结果字典
        """
        result = {
            'can_archive': False,
            'conditions': {
                'settlement_confirmed': False,
                'all_deliveries_completed': False,
                'review_completed': True,  # 默认通过，待实现复盘检查
            },
            'messages': []
        }
        
        # 条件1：检查是否有已确认的结算记录
        try:
            from backend.apps.settlement_center.models import ProjectSettlement
            confirmed_settlements = ProjectSettlement.objects.filter(
                project=project,
                status='confirmed'
            )
            
            if confirmed_settlements.exists():
                result['conditions']['settlement_confirmed'] = True
            else:
                result['messages'].append('项目没有已确认的结算记录')
        except ImportError:
            # 如果结算模块不存在，跳过此检查
            result['conditions']['settlement_confirmed'] = True
            result['messages'].append('结算模块未安装，跳过结算检查')
        
        # 条件2：检查交付记录
        incomplete_deliveries = DeliveryRecord.objects.filter(
            project=project
        ).exclude(
            status__in=['confirmed', 'feedback_received', 'archived', 'cancelled']
        )
        
        if incomplete_deliveries.exists():
            result['messages'].append(f'存在{incomplete_deliveries.count()}条未完成的交付记录')
        else:
            result['conditions']['all_deliveries_completed'] = True
        
        # 所有条件都满足
        result['can_archive'] = all(result['conditions'].values())
        
        return result
    
    @staticmethod
    def create_project_archive(project: Project, applicant: User, 
                              archive_reason: str = '', archive_description: str = '') -> ArchiveProjectArchive:
        """
        创建项目归档申请
        """
        # 检查归档条件
        check_result = ProjectArchiveService.check_archive_conditions(project)
        if not check_result['can_archive']:
            raise ValueError('项目不满足归档条件：' + '；'.join(check_result['messages']))
        
        # 创建归档记录
        archive = ArchiveProjectArchive.objects.create(
            project=project,
            archive_reason=archive_reason or '项目结算完成，申请归档',
            archive_description=archive_description or '项目已结算，满足归档条件',
            status='pending',
            applicant=applicant
        )
        
        return archive
    
    @staticmethod
    def process_project_archive(archive: ArchiveProjectArchive, executor: User) -> ArchiveProjectArchive:
        """
        执行项目归档：收集项目所有文件并归档
        """
        project = archive.project
        
        # 更新状态为归档中
        archive.status = 'archiving'
        archive.executor = executor
        archive.executed_time = timezone.now()
        archive.save()
        
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
        
        # 2. 交付文件（已自动归档的交付文件）
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
        
        # 3. 图纸文件（从图纸管理模块获取）
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
        
        # 4. 结算文件（从结算管理模块获取）
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
        
        # 5. 回款文件（从回款管理模块获取）
        try:
            from backend.apps.settlement_center.models import PaymentRecord
            # 注意：PaymentRecord可能通过payment_plan关联项目，需要根据实际模型结构调整
            # 这里假设可以直接通过project关联，如果不行需要调整
            payment_records = PaymentRecord.objects.filter(
                payment_plan_type='project',
                status='confirmed'
            )
            # 需要通过payment_plan关联到project，这里简化处理
            # 实际实现需要根据PaymentRecord的实际关联关系调整
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
        
        # 6. 其他项目文档
        project_documents = ProjectArchiveDocument.objects.filter(
            project=project
        ).exclude(document_type='delivery_file')
        
        for doc in project_documents:
            file_list.append({
                'type': doc.document_type,
                'document_id': doc.id,
                'document_number': doc.document_number,
                'name': doc.document_name,
            })
        
        # 更新归档记录
        archive.file_list = file_list
        archive.save()
        
        return archive
    
    @staticmethod
    def confirm_project_archive(archive: ArchiveProjectArchive, confirmer: User) -> ArchiveProjectArchive:
        """
        确认项目归档完成
        """
        if archive.status != 'archiving':
            raise ValueError('只能确认归档执行中的记录')
        
        archive.status = 'archived'
        archive.confirmed_by = confirmer
        archive.confirmed_time = timezone.now()
        archive.save()
        
        # 更新项目状态为已归档（如果项目状态不是已归档）
        project = archive.project
        if project.status != 'archived':
            project.status = 'archived'
            project.save(update_fields=['status'])
        
        # 记录操作日志（延迟导入避免循环）
        try:
            from .services import ArchiveOperationLogService
            ArchiveOperationLogService.log_operation(
                operation_type='approve',
                operator=confirmer,
                operation_content=f'确认项目归档：{archive.archive_number}',
                operation_result='success',
                project_archive=archive,
            )
        except:
            pass
        
        # 注意：项目团队成员权限控制通常在视图层面实现
        # 通过检查项目状态是否为'archived'来控制编辑权限
        # 已归档的项目，团队成员只能查看，不能编辑
        
        return archive


class ArchiveBorrowService:
    """档案借阅服务"""
    
    @staticmethod
    def approve_borrow(borrow: ArchiveBorrow, approver: User, approved: bool, opinion: str = '') -> ArchiveBorrow:
        """审批借阅"""
        if borrow.status != 'pending':
            raise ValueError('只能审批待审批的记录')
        
        if approved:
            borrow.status = 'approved'
        else:
            borrow.status = 'rejected'
        
        borrow.approver = approver
        borrow.approved_time = timezone.now()
        borrow.approval_opinion = opinion
        borrow.save()
        
        # 记录操作日志（延迟导入避免循环）
        try:
            from .services import ArchiveOperationLogService
            archive_name = ''
            if borrow.project_document:
                archive_name = borrow.project_document.document_name
            elif borrow.administrative_archive:
                archive_name = borrow.administrative_archive.archive_name
            
            ArchiveOperationLogService.log_operation(
                operation_type='approve' if approved else 'reject',
                operator=approver,
                operation_content=f'{"审批通过" if approved else "审批驳回"}借阅申请：{archive_name}（借阅单号：{borrow.borrow_number}）',
                operation_result='success',
                borrow_record=borrow,
                project_document=borrow.project_document,
                administrative_archive=borrow.administrative_archive,
                extra_data={'opinion': opinion}
            )
        except:
            pass
        
        return borrow
    
    @staticmethod
    def checkout_borrow(borrow: ArchiveBorrow, operator: User) -> ArchiveBorrow:
        """出库"""
        if borrow.status != 'approved':
            raise ValueError('只能出库已批准的记录')
        
        borrow.status = 'out'
        borrow.out_by = operator
        borrow.out_time = timezone.now()
        borrow.save()
        
        # 更新档案状态
        if borrow.project_document:
            borrow.project_document.status = 'borrowed'
            borrow.project_document.save()
        elif borrow.administrative_archive:
            borrow.administrative_archive.status = 'borrowed'
            borrow.administrative_archive.save()
        
        # 记录操作日志（延迟导入避免循环）
        try:
            from .services import ArchiveOperationLogService
            archive_name = ''
            if borrow.project_document:
                archive_name = borrow.project_document.document_name
            elif borrow.administrative_archive:
                archive_name = borrow.administrative_archive.archive_name
            
            ArchiveOperationLogService.log_operation(
                operation_type='borrow',
                operator=operator,
                operation_content=f'出库档案：{archive_name}（借阅单号：{borrow.borrow_number}）',
                operation_result='success',
                borrow_record=borrow,
                project_document=borrow.project_document,
                administrative_archive=borrow.administrative_archive,
            )
        except:
            pass
        
        return borrow
    
    @staticmethod
    def return_borrow(borrow: ArchiveBorrow, operator: User, return_status: str = '完好', notes: str = '') -> ArchiveBorrow:
        """归还档案"""
        if borrow.status != 'out':
            raise ValueError('只能归还已出库的记录')
        
        borrow.status = 'returned'
        borrow.returned_by = operator
        borrow.returned_time = timezone.now()
        borrow.return_status = return_status
        borrow.return_notes = notes
        borrow.save()
        
        # 更新档案状态
        if borrow.project_document:
            borrow.project_document.status = 'archived'
            borrow.project_document.save()
        elif borrow.administrative_archive:
            borrow.administrative_archive.status = 'archived'
            borrow.administrative_archive.save()
        
        return borrow


class ArchiveDestroyService:
    """档案销毁服务"""
    
    @staticmethod
    def approve_destroy(destroy: ArchiveDestroy, approver: User, approved: bool, opinion: str = '') -> ArchiveDestroy:
        """审批销毁"""
        if destroy.status != 'pending':
            raise ValueError('只能审批待审批的记录')
        
        if approved:
            destroy.status = 'approved'
        else:
            destroy.status = 'rejected'
        
        destroy.approver = approver
        destroy.approved_time = timezone.now()
        destroy.approval_opinion = opinion
        destroy.save()
        
        return destroy
    
    @staticmethod
    def execute_destroy(destroy: ArchiveDestroy, destroy_record: str = '', 
                       destroy_proof=None, destroy_photos: List = None) -> ArchiveDestroy:
        """执行销毁"""
        if destroy.status != 'approved':
            raise ValueError('只能执行已批准的销毁')
        
        destroy.status = 'destroyed'
        destroy.destroyed_time = timezone.now()
        destroy.destroy_record = destroy_record
        
        if destroy_proof:
            destroy.destroy_proof = destroy_proof
        if destroy_photos:
            destroy.destroy_photos = destroy_photos
        
        destroy.save()
        
        # 记录操作日志（在删除前记录）
        archive_name = ''
        project_doc = destroy.project_document
        admin_archive = destroy.administrative_archive
        
        if project_doc:
            archive_name = project_doc.document_name
        elif admin_archive:
            archive_name = admin_archive.archive_name
        
        # 更新档案状态
        if project_doc:
            # 项目文档销毁后删除文件
            project_doc.file.delete()
            project_doc.delete()
        elif admin_archive:
            admin_archive.status = 'destroyed'
            admin_archive.save()
        
        # 记录操作日志（延迟导入避免循环）
        try:
            from .services import ArchiveOperationLogService
            ArchiveOperationLogService.log_operation(
                operation_type='destroy',
                operator=destroy.destroyer if hasattr(destroy, 'destroyer') else None,
                operation_content=f'销毁档案：{archive_name}（销毁单号：{destroy.destroy_number if hasattr(destroy, "destroy_number") else "N/A"}）',
                operation_result='success',
                project_document=project_doc if project_doc else None,
                administrative_archive=admin_archive,
                extra_data={'destroy_record': destroy_record}
            )
        except:
            pass
        
        return destroy


class ArchiveOperationLogService:
    """档案操作日志服务"""
    
    @staticmethod
    def log_operation(
        operation_type: str,
        operator: User,
        operation_content: str = '',
        operation_result: str = 'success',
        error_message: str = '',
        project_document=None,
        administrative_archive=None,
        project_archive=None,
        borrow_record=None,
        ip_address: str = None,
        user_agent: str = None,
        extra_data: dict = None
    ):
        """
        记录档案操作日志
        
        Args:
            operation_type: 操作类型（upload, download, edit, delete, archive, borrow, return, destroy等）
            operator: 操作人
            operation_content: 操作内容描述
            operation_result: 操作结果（success, failed, pending）
            error_message: 错误信息（如果操作失败）
            project_document: 关联的项目文档（可选）
            administrative_archive: 关联的行政档案（可选）
            project_archive: 关联的项目归档（可选）
            borrow_record: 关联的借阅记录（可选）
            ip_address: IP地址（可选）
            user_agent: 用户代理（可选）
            extra_data: 额外信息（可选）
        """
        if not ARCHIVE_OPERATION_LOG_AVAILABLE:
            return None
        
        try:
            log = ArchiveOperationLog.objects.create(
                operation_type=operation_type,
                operator=operator,
                operation_time=timezone.now(),
                operation_content=operation_content,
                operation_result=operation_result,
                error_message=error_message,
                project_document=project_document,
                administrative_archive=administrative_archive,
                project_archive=project_archive,
                borrow_record=borrow_record,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data or {}
            )
            return log
        except Exception as e:
            # 日志记录失败不应该影响主流程，只记录错误
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"记录操作日志失败: {str(e)}")
            return None
    
    @staticmethod
    def log_from_request(request, operation_type: str, operation_content: str = '', 
                        operation_result: str = 'success', error_message: str = '',
                        project_document=None, administrative_archive=None, 
                        project_archive=None, borrow_record=None, extra_data: dict = None):
        """
        从请求对象记录操作日志（自动提取IP和User-Agent）
        
        Args:
            request: Django请求对象
            operation_type: 操作类型
            operation_content: 操作内容
            operation_result: 操作结果
            error_message: 错误信息
            project_document: 关联的项目文档
            administrative_archive: 关联的行政档案
            project_archive: 关联的项目归档
            borrow_record: 关联的借阅记录
            extra_data: 额外信息
        """
        # 获取IP地址
        ip_address = None
        if hasattr(request, 'META'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # 获取User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if hasattr(request, 'META') else ''
        
        return ArchiveOperationLogService.log_operation(
            operation_type=operation_type,
            operator=request.user if request.user.is_authenticated else None,
            operation_content=operation_content,
            operation_result=operation_result,
            error_message=error_message,
            project_document=project_document,
            administrative_archive=administrative_archive,
            project_archive=project_archive,
            borrow_record=borrow_record,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data
        )

