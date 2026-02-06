"""
修复卡住的审批流程
检查并修复所有状态为 pending 但可能卡住的审批实例
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord, ApprovalNode
from backend.apps.workflow_engine.services import ApprovalEngine


class Command(BaseCommand):
    help = '修复卡住的审批流程：检查并修复所有状态为 pending 但可能卡住的审批实例'

    def add_arguments(self, parser):
        parser.add_argument(
            '--instance-number',
            type=str,
            help='指定要修复的审批实例编号（如：loan_approval-20260130-0004），如果不指定则修复所有卡住的审批',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅检查，不实际修复',
        )

    def handle(self, *args, **options):
        instance_number = options.get('instance_number')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('DRY RUN 模式：仅检查，不实际修复'))
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write('')
        
        # 获取待修复的审批实例
        if instance_number:
            instances = ApprovalInstance.objects.filter(
                instance_number=instance_number,
                status='pending'
            )
        else:
            instances = ApprovalInstance.objects.filter(status='pending')
        
        if not instances.exists():
            self.stdout.write(self.style.SUCCESS('✓ 没有找到需要修复的审批实例'))
            return
        
        self.stdout.write(f'找到 {instances.count()} 个待处理的审批实例')
        self.stdout.write('')
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        for instance in instances:
            self.stdout.write('-' * 60)
            self.stdout.write(f'检查审批实例: {instance.instance_number}')
            self.stdout.write(f'  流程: {instance.workflow.name}')
            self.stdout.write(f'  状态: {instance.get_status_display()}')
            self.stdout.write(f'  当前节点: {instance.current_node.name if instance.current_node else "无"}')
            
            if not instance.current_node:
                self.stdout.write(self.style.WARNING('  ⚠ 当前节点为空，尝试修复'))
                
                # 检查是否有审批记录，如果有已通过的记录，说明流程应该已完成
                approved_records = ApprovalRecord.objects.filter(
                    instance=instance,
                    result='approved'
                ).order_by('-approval_time')
                
                if approved_records.exists():
                    # 查找最后一个审批节点
                    last_node = approved_records.first().node
                    next_node = ApprovalEngine._get_next_node(last_node)
                    
                    if not next_node or (next_node and next_node.node_type == 'end'):
                        # 没有下一个节点或下一个是结束节点，流程应该已完成
                        self.stdout.write(self.style.WARNING('  ⚠ 所有审批已完成，但流程状态未更新'))
                        if not dry_run:
                            try:
                                instance.status = 'approved'
                                instance.completed_time = timezone.now()
                                instance.save()
                                
                                ApprovalEngine._update_business_object_status(instance, 'approved')
                                
                                if instance.workflow.code == 'loan_approval':
                                    ApprovalEngine._notify_cashier_on_loan_approval(instance)
                                
                                self.stdout.write(self.style.SUCCESS('  ✓ 已修复：流程状态已更新为已完成'))
                                fixed_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                                error_count += 1
                        else:
                            self.stdout.write(self.style.WARNING('  [DRY RUN] 将更新流程状态为已完成'))
                            fixed_count += 1
                    else:
                        # 还有下一个节点，应该进入下一个节点
                        self.stdout.write(self.style.WARNING(f'  ⚠ 应该进入下一个节点: {next_node.name}'))
                        if not dry_run:
                            try:
                                instance.current_node = next_node
                                instance.save()
                                ApprovalEngine._create_pending_records(instance, next_node)
                                self.stdout.write(self.style.SUCCESS(f'  ✓ 已修复：进入节点 {next_node.name}'))
                                fixed_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                                error_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'  [DRY RUN] 将进入节点 {next_node.name}'))
                            fixed_count += 1
                else:
                    # 没有审批记录，尝试从开始节点重新启动
                    start_node = instance.workflow.nodes.filter(node_type='start').first()
                    if start_node:
                        self.stdout.write(self.style.WARNING('  ⚠ 没有审批记录，尝试从开始节点重新启动'))
                        if not dry_run:
                            try:
                                next_node = ApprovalEngine._get_next_node(start_node)
                                if next_node:
                                    instance.current_node = next_node
                                    instance.save()
                                    ApprovalEngine._create_pending_records(instance, next_node)
                                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已修复：从开始节点重新启动，进入节点 {next_node.name}'))
                                    fixed_count += 1
                                else:
                                    self.stdout.write(self.style.ERROR('  ❌ 没有找到下一个节点'))
                                    error_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                                error_count += 1
                        else:
                            self.stdout.write(self.style.WARNING('  [DRY RUN] 将从开始节点重新启动'))
                            fixed_count += 1
                    else:
                        self.stdout.write(self.style.ERROR('  ❌ 无法修复：没有开始节点'))
                        error_count += 1
                continue
            
            # 情况1：当前节点是结束节点
            if instance.current_node.node_type == 'end':
                self.stdout.write(self.style.WARNING('  ⚠ 发现卡在结束节点，需要修复'))
                if not dry_run:
                    try:
                        # 直接完成流程
                        instance.status = 'approved'
                        instance.completed_time = timezone.now()
                        instance.current_node = None
                        instance.save()
                        
                        # 更新业务对象状态
                        ApprovalEngine._update_business_object_status(instance, 'approved')
                        
                        # 抄送出纳员（如果是借款审批流程）
                        if instance.workflow.code == 'loan_approval':
                            ApprovalEngine._notify_cashier_on_loan_approval(instance)
                        
                        self.stdout.write(self.style.SUCCESS('  ✓ 已修复：流程已完成'))
                        fixed_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                        error_count += 1
                else:
                    self.stdout.write(self.style.WARNING('  [DRY RUN] 将完成流程'))
                    fixed_count += 1
                continue
            
            # 情况2：检查当前节点是否已完成所有审批
            if instance.current_node.node_type == 'approval':
                # 检查节点是否已完成
                is_completed = ApprovalEngine._check_node_completed(instance, instance.current_node)
                
                if is_completed:
                    self.stdout.write(self.style.WARNING('  ⚠ 发现节点已完成但未进入下一节点，需要修复'))
                    
                    if not dry_run:
                        try:
                            # 获取下一个节点
                            next_node = ApprovalEngine._get_next_node(instance.current_node)
                            
                            if next_node:
                                # 进入下一个节点
                                instance.current_node = next_node
                                instance.save()
                                
                                # 为下一个节点创建审批记录
                                ApprovalEngine._create_pending_records(instance, next_node)
                                
                                self.stdout.write(self.style.SUCCESS(f'  ✓ 已修复：进入下一个节点 {next_node.name}'))
                                fixed_count += 1
                            else:
                                # 没有下一个节点，流程完成
                                instance.status = 'approved'
                                instance.completed_time = timezone.now()
                                instance.current_node = None
                                instance.save()
                                
                                ApprovalEngine._update_business_object_status(instance, 'approved')
                                
                                if instance.workflow.code == 'loan_approval':
                                    ApprovalEngine._notify_cashier_on_loan_approval(instance)
                                
                                self.stdout.write(self.style.SUCCESS('  ✓ 已修复：流程已完成'))
                                fixed_count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                            error_count += 1
                    else:
                        self.stdout.write(self.style.WARNING('  [DRY RUN] 将进入下一个节点或完成流程'))
                        fixed_count += 1
                    continue
                
                # 情况3：检查是否有审批人
                approvers = ApprovalEngine._get_approvers(instance.current_node, instance)
                if not approvers and instance.current_node.is_required:
                    self.stdout.write(self.style.WARNING('  ⚠ 发现必审节点没有审批人，需要检查'))
                    
                    # 检查是否有待审批记录
                    pending_records = ApprovalRecord.objects.filter(
                        instance=instance,
                        node=instance.current_node,
                        result='pending'
                    )
                    
                    if not pending_records.exists():
                        self.stdout.write(self.style.ERROR('  ❌ 没有审批人且没有待审批记录，无法自动修复'))
                        self.stdout.write('     请手动检查节点配置或分配审批人')
                        error_count += 1
                    else:
                        self.stdout.write(f'  ℹ 有 {pending_records.count()} 条待审批记录，流程正常')
                        skipped_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ 节点状态正常'))
                    skipped_count += 1
            
            # 情况4：开始节点（不应该卡在这里）
            elif instance.current_node.node_type == 'start':
                self.stdout.write(self.style.WARNING('  ⚠ 发现卡在开始节点，尝试进入第一个审批节点'))
                
                if not dry_run:
                    try:
                        next_node = ApprovalEngine._get_next_node(instance.current_node)
                        if next_node:
                            instance.current_node = next_node
                            instance.save()
                            ApprovalEngine._create_pending_records(instance, next_node)
                            self.stdout.write(self.style.SUCCESS(f'  ✓ 已修复：进入第一个审批节点 {next_node.name}'))
                            fixed_count += 1
                        else:
                            self.stdout.write(self.style.ERROR('  ❌ 没有找到下一个节点'))
                            error_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ❌ 修复失败: {str(e)}'))
                        error_count += 1
                else:
                    self.stdout.write(self.style.WARNING('  [DRY RUN] 将进入第一个审批节点'))
                    fixed_count += 1
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('修复完成统计'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  总检查数: {instances.count()}')
        self.stdout.write(self.style.SUCCESS(f'  已修复: {fixed_count}'))
        self.stdout.write(f'  跳过: {skipped_count}')
        self.stdout.write(self.style.ERROR(f'  错误: {error_count}'))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('注意：这是 DRY RUN 模式，没有实际修改数据'))
            self.stdout.write(self.style.WARNING('运行时不加 --dry-run 参数来实际执行修复'))
