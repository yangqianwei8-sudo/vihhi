"""
同步审批实例状态到关联的业务对象
用于修复已完成审批但业务对象状态未更新的情况
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.delivery_customer.models import OutgoingDocument


class Command(BaseCommand):
    help = '同步已完成审批实例的状态到关联的业务对象（发文）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示需要更新的记录，不实际更新',
        )
        parser.add_argument(
            '--document-number',
            type=str,
            help='指定要更新的发文编号（部分匹配）',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        document_number = options.get('document_number')
        
        self.stdout.write('开始同步审批状态...')
        
        # 查找所有已完成的审批实例
        completed_instances = ApprovalInstance.objects.filter(
            status__in=['approved', 'rejected']
        )
        
        if document_number:
            # 如果指定了发文编号，只处理该发文
            outgoing_doc_type = ContentType.objects.get(app_label='delivery_customer', model='outgoingdocument')
            try:
                doc = OutgoingDocument.objects.get(document_number__icontains=document_number)
                completed_instances = completed_instances.filter(
                    content_type=outgoing_doc_type,
                    object_id=doc.id
                )
                self.stdout.write(f'找到发文: {doc.document_number} (ID: {doc.id})')
            except OutgoingDocument.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'未找到发文: {document_number}'))
                return
            except OutgoingDocument.MultipleObjectsReturned:
                self.stdout.write(self.style.WARNING(f'找到多个匹配的发文: {document_number}'))
                return
        
        # 获取发文类型
        outgoing_doc_type = ContentType.objects.get(app_label='delivery_customer', model='outgoingdocument')
        
        # 只处理关联到发文的审批实例
        outgoing_instances = completed_instances.filter(content_type=outgoing_doc_type)
        
        self.stdout.write(f'找到 {outgoing_instances.count()} 个已完成的发文审批实例')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for instance in outgoing_instances:
            try:
                # 获取关联的发文对象
                doc = OutgoingDocument.objects.get(id=instance.object_id)
                
                # 检查是否需要更新
                if instance.status == 'approved' and doc.status == 'reviewing':
                    if dry_run:
                        self.stdout.write(
                            f'  [DRY RUN] 需要更新: {doc.document_number} '
                            f'(审批实例: {instance.instance_number}, 当前状态: {doc.status})'
                        )
                    else:
                        # 同步状态
                        ApprovalEngine._sync_content_object_status(instance, 'approved')
                        doc.refresh_from_db()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ 已更新: {doc.document_number} '
                                f'(审批实例: {instance.instance_number}, 新状态: {doc.status})'
                            )
                        )
                        updated_count += 1
                elif instance.status == 'rejected' and doc.status == 'reviewing':
                    if dry_run:
                        self.stdout.write(
                            f'  [DRY RUN] 需要更新: {doc.document_number} '
                            f'(审批实例: {instance.instance_number}, 当前状态: {doc.status})'
                        )
                    else:
                        # 同步状态
                        ApprovalEngine._sync_content_object_status(instance, 'rejected')
                        doc.refresh_from_db()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ 已更新: {doc.document_number} '
                                f'(审批实例: {instance.instance_number}, 新状态: {doc.status})'
                            )
                        )
                        updated_count += 1
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f'  跳过: {doc.document_number} '
                        f'(审批状态: {instance.status}, 发文状态: {doc.status}, 无需更新)'
                    )
            except OutgoingDocument.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ 审批实例 {instance.instance_number} 关联的发文不存在 (ID: {instance.object_id})'
                    )
                )
                skipped_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ 处理失败: {instance.instance_number} - {str(e)}'
                    )
                )
                error_count += 1
        
        # 输出统计信息
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 模式 - 未实际更新'))
        else:
            self.stdout.write(self.style.SUCCESS('状态同步完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'总计: {outgoing_instances.count()} 个审批实例')
        self.stdout.write(f'已更新: {updated_count} 个')
        self.stdout.write(f'已跳过: {skipped_count} 个')
        self.stdout.write(f'错误: {error_count} 个')
        self.stdout.write('='*60)

