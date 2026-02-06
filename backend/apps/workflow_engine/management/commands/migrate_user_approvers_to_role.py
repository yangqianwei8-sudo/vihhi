"""
数据迁移：将所有 approver_type='user' 的节点自动迁移为 role

迁移策略：
1. 为每个使用 user 类型的节点创建一个专用角色（Role）
2. 将原 approver_users 全部加入该角色成员
3. 将该节点修改为 approver_type='role'，approver_roles = [新角色]
4. 清空 approver_users

迁移必须可重复执行且幂等（避免重复建角色）。
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.workflow_engine.models import ApprovalNode
from backend.apps.system_management.models import Role, User


class Command(BaseCommand):
    help = '将审批节点中的 user 类型迁移为 role 类型（消除写死用户隐患）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要迁移的节点，不执行实际迁移',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # 查找所有使用 user 类型的节点
        user_nodes = ApprovalNode.objects.filter(approver_type='user').prefetch_related('approver_users')
        
        if not user_nodes.exists():
            self.stdout.write(self.style.SUCCESS('✓ 没有找到使用 user 类型的节点，无需迁移'))
            return
        
        self.stdout.write(f'找到 {user_nodes.count()} 个使用 user 类型的节点，开始迁移...')
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for node in user_nodes:
                try:
                    # 检查是否有审批人
                    approver_users = list(node.approver_users.all())
                    if not approver_users:
                        self.stdout.write(
                            self.style.WARNING(f'  跳过节点 {node.id} ({node.name})：没有配置审批人')
                        )
                        skipped_count += 1
                        continue
                    
                    # 生成角色代码（保证唯一）
                    role_code = f'wf_node_{node.id}_approvers'
                    
                    # 检查角色是否已存在（幂等性检查）
                    role, created = Role.objects.get_or_create(
                        code=role_code,
                        defaults={
                            'name': f'流程节点审批人-{node.workflow.name}-{node.name}',
                            'description': f'由 user 类型节点自动迁移生成，用于节点 {node.id} ({node.name}) 的审批人配置',
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  创建角色: {role.name} ({role_code})')
                    else:
                        self.stdout.write(f'  复用已有角色: {role.name} ({role_code})')
                    
                    # 将审批人加入角色（幂等操作）
                    role.users.add(*approver_users)
                    self.stdout.write(f'  将 {len(approver_users)} 个审批人加入角色')
                    
                    if not dry_run:
                        # 修改节点为 role 类型
                        node.approver_type = 'role'
                        node.save()
                        
                        # 设置角色关联
                        node.approver_roles.clear()
                        node.approver_roles.add(role)
                        
                        # 清空用户关联（保留字段但不使用）
                        node.approver_users.clear()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ 节点 {node.id} ({node.name}) 迁移完成')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  [DRY-RUN] 节点 {node.id} ({node.name}) 将迁移为 role 类型')
                        )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ 节点 {node.id} ({node.name}) 迁移失败: {str(e)}')
                    )
                    error_count += 1
                    if not dry_run:
                        raise
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] 这是预览模式，未执行实际迁移'))
            self.stdout.write(f'将迁移 {migrated_count} 个节点，跳过 {skipped_count} 个节点')
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 迁移完成：成功 {migrated_count} 个，跳过 {skipped_count} 个，失败 {error_count} 个'))
            if migrated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '所有 user 类型节点已迁移为 role 类型，审批人由角色成员控制，'
                        '组织变化时只需维护角色成员，无需修改流程模板'
                    )
                )
