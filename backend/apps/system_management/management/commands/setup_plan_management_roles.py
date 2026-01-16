"""
配置计划管理模块的角色和权限

使用方法：
    python manage.py setup_plan_management_roles
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.apps.system_management.models import Role
from backend.apps.permission_management.models import PermissionItem


# 角色定义
ROLE_DEFINITIONS = [
    {
        'code': 'plan_manager',
        'name': '计划管理员',
        'description': '全面管理计划和审批，拥有计划管理模块的所有权限',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.approve_plan',
            'plan_management.approve',
            'plan_management.goal.view',
            'plan_management.goal.create',
            'plan_management.manage_goal',
        ]
    },
    {
        'code': 'project_manager',
        'name': '项目经理',
        'description': '创建和管理自己的计划，但不能审批',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.goal.view',
        ]
    },
    {
        'code': 'plan_approver',
        'name': '计划审批人',
        'description': '审批计划的启动/取消请求，查看计划信息',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.approve_plan',
            'plan_management.approve',
            'plan_management.goal.view',
        ]
    },
    {
        'code': 'plan_viewer',
        'name': '计划查看者',
        'description': '只能查看计划信息，不能创建或审批',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.goal.view',
        ]
    },
]


class Command(BaseCommand):
    help = "配置计划管理模块的角色和权限"

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='更新已存在的角色权限（默认只创建新角色）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览将要执行的操作，不实际修改数据库',
        )

    def handle(self, *args, **options):
        update_existing = options['update']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际修改数据库）===\n'))

        created_count = 0
        updated_count = 0
        error_count = 0

        with transaction.atomic():
            for role_def in ROLE_DEFINITIONS:
                try:
                    # 获取或创建角色（使用原始SQL处理user_type字段，因为模型定义中没有）
                    from django.db import connection
                    
                    # 先检查角色是否存在
                    existing_role = Role.objects.filter(code=role_def['code']).first()
                    
                    if existing_role:
                        role = existing_role
                        role_created = False
                        if update_existing:
                            # 更新角色信息
                            role.name = role_def['name']
                            role.description = role_def['description']
                            role.is_active = True
                            role.save(update_fields=['name', 'description', 'is_active'])
                    else:
                        # 使用原始SQL创建角色（包含user_type字段）
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO system_role (name, code, description, is_active, created_time, user_type)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id
                                """,
                                [
                                    role_def['name'],
                                    role_def['code'],
                                    role_def['description'],
                                    True,
                                    timezone.now(),
                                    'internal'  # 设置user_type为internal
                                ]
                            )
                            role_id = cursor.fetchone()[0]
                        
                        # 获取刚创建的角色对象
                        role = Role.objects.get(id=role_id)
                        role_created = True

                    if role_created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ 创建角色: {role.name} ({role.code})')
                        )
                    else:
                        if update_existing:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'↻ 更新角色: {role.name} ({role.code})')
                            )
                        else:
                            self.stdout.write(
                                self.style.NOTICE(f'⊘ 跳过已存在角色: {role.name} ({role.code})')
                            )
                            continue

                    # 分配权限
                    permission_codes = role_def['permissions']
                    permissions = PermissionItem.objects.filter(
                        code__in=permission_codes,
                        is_active=True
                    )

                    # 检查是否有缺失的权限
                    found_codes = set(permissions.values_list('code', flat=True))
                    missing_codes = set(permission_codes) - found_codes

                    if missing_codes:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ⚠ 警告：以下权限不存在，请先运行 seed_permissions：{", ".join(missing_codes)}'
                            )
                        )
                        error_count += len(missing_codes)

                    if not dry_run:
                        # 清除现有权限并分配新权限
                        role.custom_permissions.clear()
                        role.custom_permissions.add(*permissions)

                    self.stdout.write(
                        f'  → 分配权限: {permissions.count()} 个'
                    )

                    if missing_codes:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  → 缺失权限: {len(missing_codes)} 个'
                            )
                        )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ 处理角色 {role_def["code"]} 时出错: {str(e)}')
                    )

            if dry_run:
                # 回滚事务
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING('\n=== 预览模式：未实际修改数据库 ===')
                )

        # 输出总结
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('预览结果：'))
        else:
            self.stdout.write(self.style.SUCCESS('执行结果：'))
        
        self.stdout.write(f'  创建角色: {created_count} 个')
        if update_existing:
            self.stdout.write(f'  更新角色: {updated_count} 个')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  错误: {error_count} 个')
            )
        
        self.stdout.write('\n角色列表：')
        for role_def in ROLE_DEFINITIONS:
            try:
                role = Role.objects.get(code=role_def['code'])
                perm_count = role.custom_permissions.filter(is_active=True).count()
                status = '✓' if role.is_active else '✗'
                self.stdout.write(
                    f'  {status} {role.name} ({role.code}) - {perm_count} 个权限'
                )
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {role_def["name"]} ({role_def["code"]}) - 不存在')
                )

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    '\n⚠ 请先运行以下命令创建缺失的权限：\n'
                    '  python manage.py seed_permissions'
                )
            )
