"""
补发用印申请审批通知给行政主管的管理命令
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from backend.apps.administrative_management.models import SealUsage
from backend.apps.system_management.models import Role
from backend.apps.project_center.models import ProjectTeamNotification
from backend.apps.workflow_engine.models import ApprovalInstance
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "为已审批的用印申请补发通知给行政主管"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要发送的通知，不实际发送',
        )
        parser.add_argument(
            '--usage-id',
            type=int,
            help='仅处理指定的用印申请ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        usage_id = options.get('usage_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== 模拟运行模式（不会实际发送通知）==='))
        
        # 查找行政主管角色
        admin_office_role = Role.objects.filter(code='admin_office', is_active=True).first()
        if not admin_office_role:
            self.stdout.write(self.style.ERROR('未找到行政主管角色（admin_office），请先配置角色'))
            return
        
        # 获取所有行政主管用户
        admin_office_users = admin_office_role.users.filter(is_active=True)
        if not admin_office_users.exists():
            self.stdout.write(self.style.ERROR('未找到行政主管用户，请先为用户分配行政主管角色'))
            return
        
        self.stdout.write(f'找到 {admin_office_users.count()} 位行政主管')
        
        # 查询用印申请
        if usage_id:
            usages = SealUsage.objects.filter(id=usage_id)
            if not usages.exists():
                self.stdout.write(self.style.ERROR(f'未找到ID为 {usage_id} 的用印申请'))
                return
        else:
            # 查找所有已审批的用印申请（有审批实例且状态为已通过或已驳回）
            content_type = ContentType.objects.get_for_model(SealUsage)
            approved_instances = ApprovalInstance.objects.filter(
                content_type=content_type,
                status__in=['approved', 'rejected']
            ).values_list('object_id', flat=True)
            
            usages = SealUsage.objects.filter(id__in=approved_instances)
        
        total_count = usages.count()
        self.stdout.write(f'找到 {total_count} 条已审批的用印申请')
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('没有需要处理的用印申请'))
            return
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        with transaction.atomic():
            for usage in usages.select_related('seal', 'used_by'):
                try:
                    # 检查是否已经发送过通知
                    existing_notifications = ProjectTeamNotification.objects.filter(
                        project=None,
                        recipient__in=admin_office_users,
                        category='approval',
                        context__seal_usage_id=usage.id
                    )
                    
                    if existing_notifications.exists():
                        skip_count += 1
                        if not dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'跳过 {usage.usage_number}：已存在通知'
                                )
                            )
                        continue
                    
                    # 获取审批实例
                    approval_instance = ApprovalInstance.objects.filter(
                        content_type=ContentType.objects.get_for_model(SealUsage),
                        object_id=usage.id,
                        workflow__code='seal_usage_approval'
                    ).order_by('-created_time').first()
                    
                    # 创建通知
                    action_url = f'/administrative/seals/usages/{usage.id}/'
                    
                    for admin_user in admin_office_users:
                        if not dry_run:
                            ProjectTeamNotification.objects.create(
                                project=None,
                                recipient=admin_user,
                                operator=usage.used_by,
                                title=f'用印申请通知 - {usage.usage_number}',
                                message=f'{usage.used_by.get_full_name() or usage.used_by.username} 提交了用印申请：{usage.seal.seal_name}，用印事由：{usage.usage_reason[:100]}',
                                category='approval',
                                action_url=action_url,
                                is_read=False,
                                context={
                                    'approval_instance_id': approval_instance.id if approval_instance else None,
                                    'approval_instance_number': approval_instance.instance_number if approval_instance else None,
                                    'seal_usage_id': usage.id,
                                    'seal_usage_number': usage.usage_number,
                                    'resend': True,  # 标记为补发
                                }
                            )
                        else:
                            self.stdout.write(
                                f'  [模拟] 将为 {admin_user.username} 发送通知：{usage.usage_number}'
                            )
                    
                    success_count += 1
                    if not dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ 已为 {usage.usage_number} 补发通知给 {admin_office_users.count()} 位行政主管'
                            )
                        )
                
                except Exception as e:
                    error_count += 1
                    logger.exception(f'处理用印申请 {usage.usage_number} 时出错: {str(e)}')
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ 处理 {usage.usage_number} 时出错: {str(e)}'
                        )
                    )
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('处理完成'))
        self.stdout.write(f'  总计: {total_count} 条')
        self.stdout.write(self.style.SUCCESS(f'  成功: {success_count} 条'))
        if skip_count > 0:
            self.stdout.write(self.style.WARNING(f'  跳过: {skip_count} 条（已存在通知）'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'  失败: {error_count} 条'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
