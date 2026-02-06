"""
迁移 custom 类型的印章保管员节点为 role 类型

策略：
1. 创建或获取 seal_keeper 角色
2. 将所有印章的 keeper 加入该角色
3. 将 custom 类型的"抄送印章保管员"节点改为 role 类型，关联 seal_keeper 角色
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.workflow_engine.models import ApprovalNode
from backend.apps.system_management.models import Role, User
from backend.apps.administrative_management.models import Seal


class Command(BaseCommand):
    help = '将 custom 类型的印章保管员节点迁移为 role 类型（消除硬编码隐患）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要迁移的节点，不执行实际迁移',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # 查找所有 custom 类型的节点（特别是"抄送印章保管员"）
        custom_nodes = ApprovalNode.objects.filter(
            approver_type='custom'
        ).select_related('workflow')

        if not custom_nodes.exists():
            self.stdout.write(self.style.SUCCESS('✓ 没有找到 custom 类型的节点，无需迁移'))
            return

        self.stdout.write(f'找到 {custom_nodes.count()} 个 custom 类型的节点，开始迁移...')
        self.stdout.write('')

        # 创建或获取 seal_keeper 角色
        seal_keeper_role, created = Role.objects.get_or_create(
            code='seal_keeper',
            defaults={
                'name': '印章保管员',
                'description': '印章保管员角色，用于印章借用审批流程的抄送通知。由 custom 类型节点自动迁移生成。',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建角色: {seal_keeper_role.name} ({seal_keeper_role.code})'))
        else:
            self.stdout.write(f'复用已有角色: {seal_keeper_role.name} ({seal_keeper_role.code})')

        # 将所有印章的 keeper 加入该角色
        all_keepers = Seal.objects.filter(keeper__isnull=False).values_list('keeper', flat=True).distinct()
        keeper_users = User.objects.filter(id__in=all_keepers, is_active=True)

        if keeper_users.exists():
            seal_keeper_role.users.add(*keeper_users)
            self.stdout.write(f'✓ 将 {keeper_users.count()} 个印章保管员加入角色')
        else:
            self.stdout.write(self.style.WARNING('⚠️  未找到任何印章保管员，请确保 Seal.keeper 字段已正确设置'))

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for node in custom_nodes:
                try:
                    # 检查节点名称是否包含"印章保管员"或"seal_keeper"
                    is_seal_keeper_node = (
                        '印章保管员' in node.name or
                        'seal_keeper' in node.name.lower() or
                        '保管员' in node.name
                    )

                    if not is_seal_keeper_node:
                        self.stdout.write(
                            self.style.WARNING(f'  跳过节点 {node.id} ({node.name})：不是印章保管员节点')
                        )
                        skipped_count += 1
                        continue

                    if not dry_run:
                        # 修改节点为 role 类型
                        node.approver_type = 'role'
                        node.save()

                        # 设置角色关联
                        node.approver_roles.clear()
                        node.approver_roles.add(seal_keeper_role)

                        # 清空 approver_config（如果之前有配置）
                        node.approver_config = {}
                        node.save()

                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ 节点 {node.id} ({node.name}) 迁移完成：custom -> role (seal_keeper)')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  [DRY-RUN] 节点 {node.id} ({node.name}) 将迁移为 role 类型 (seal_keeper)')
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
                        '所有 custom 类型的印章保管员节点已迁移为 role 类型，'
                        '审批人由 seal_keeper 角色成员控制，组织变化时只需维护角色成员，无需修改流程模板'
                    )
                )
