from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine


class Command(BaseCommand):
    help = '为已完成的借款审批补发出纳员通知'

    def add_arguments(self, parser):
        parser.add_argument(
            '--instance-number',
            type=str,
            help='指定审批单号（如：loan_approval-20260130-0004），如果不指定则补发所有已完成的借款审批通知',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要补发的通知，不实际发送',
        )

    def handle(self, *args, **options):
        instance_number = options.get('instance_number')
        dry_run = options.get('dry_run', False)
        
        # 获取借款审批流程的审批实例
        if instance_number:
            # 指定审批单号
            instances = ApprovalInstance.objects.filter(
                instance_number=instance_number,
                workflow__code='loan_approval',
                status='approved'
            )
        else:
            # 所有已完成的借款审批
            instances = ApprovalInstance.objects.filter(
                workflow__code='loan_approval',
                status='approved'
            ).order_by('-completed_time')
        
        if not instances.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'未找到符合条件的借款审批实例'
                    + (f'（审批单号：{instance_number}）' if instance_number else '')
                )
            )
            return
        
        self.stdout.write(f'找到 {instances.count()} 个已完成的借款审批实例，开始补发通知...\n')
        
        success_count = 0
        fail_count = 0
        
        for instance in instances:
            try:
                # 获取业务对象信息
                try:
                    content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
                    obj_name = str(content_obj)[:50]
                except Exception as e:
                    obj_name = f"{instance.content_type.model}#{instance.object_id}"
                
                if dry_run:
                    self.stdout.write(
                        f'  [{instance.instance_number}] {obj_name} - 将补发通知'
                    )
                else:
                    # 调用抄送方法
                    ApprovalEngine._notify_cashier_on_loan_approval(instance)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [{instance.instance_number}] {obj_name} - 通知已补发'
                        )
                    )
                    success_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  [{instance.instance_number}] {obj_name} - 补发失败: {str(e)}'
                    )
                )
                fail_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n这是预览模式，没有实际发送通知。\n'
                    f'将补发 {instances.count()} 个审批实例的通知。'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n完成！成功补发 {success_count} 个通知，失败 {fail_count} 个。'
                )
            )
