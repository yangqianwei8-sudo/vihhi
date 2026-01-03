from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from backend.apps.system_management.models import User, Role, Department
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '创建陈洁滢用户账号并分配相应权限'

    # 职务对应的角色代码
    POSITION_ROLE_MAP = {
        '档案管理员': 'archive_manager',
        '行政主管': 'admin_office',
        '技术助理': 'technical_assistant',
        '资料员': 'data_clerk',
        '出纳员': 'cashier',
    }

    # 各角色应该拥有的权限（根据职务功能）
    # 注意：如果某些权限点不存在，命令会自动跳过并提示
    ROLE_PERMISSIONS = {
        'archive_manager': [
            # 档案管理权限
            'archive_management.add',
            'archive_management.view',
            'archive_management.edit',
            'archive_management.delete',
            'archive_management.manage',
        ],
        'admin_office': [
            # 行政管理权限
            'system_management.user.view',
            'system_management.department.view',
            'system_management.config.view',
            'system_management.config.edit',
            # 合同管理权限（行政主管通常需要）
            'customer_management.contract.view',
            'customer_management.contract.view_all',
            'customer_management.contract.create',
            'customer_management.contract.edit',
            # 收文管理和发文管理权限（交付客户模块）
            'delivery_center.view',
            'delivery_center.view_all',
            'delivery_center.create',
            'delivery_center.edit',
            'delivery_center.edit_assigned',
            'delivery_center.view_statistics',
        ],
        'technical_assistant': [
            # 技术助理权限
            'production_management.project.view',
            'production_management.project.view_assigned',
            'production_management.task.view',
            'production_management.task.view_assigned',
            'production_management.task.create',
            'production_management.task.edit',
        ],
        'data_clerk': [
            # 资料员权限（通常需要查看和上传资料）
            'production_management.document.view',
            'production_management.document.upload',
            'production_management.document.manage',
            'production_management.file.view',
            'production_management.file.upload',
        ],
        'cashier': [
            # 出纳员权限（财务管理相关）
            'financial_management.payment.view',
            'financial_management.payment.create',
            'financial_management.payment.edit',
            'financial_management.receipt.view',
            'financial_management.receipt.create',
            'financial_management.receipt.edit',
            'settlement_center.payment.view',
            'settlement_center.payment.create',
        ],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))
        
        User = get_user_model()
        
        # 1. 创建或获取综合管理部
        self.stdout.write('\n📋 步骤1: 创建/获取综合管理部...')
        admin_dept = Department.objects.filter(
            Q(code='dept_admin') | Q(name='综合管理部')
        ).first()
        
        if not admin_dept:
            admin_dept = Department.objects.create(
                name='综合管理部',
                code='dept_admin',
                description='综合管理部门，负责行政、档案、财务等综合事务',
                order=10,
                is_active=True,
            )
            created = True
        else:
            created = False
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✅ 创建了部门: {admin_dept.name}'))
        else:
            self.stdout.write(f'  ℹ️  部门已存在: {admin_dept.name}')
        
        # 2. 创建或获取所需的角色
        self.stdout.write('\n📋 步骤2: 创建/获取所需角色...')
        roles_to_assign = []
        
        for position, role_code in self.POSITION_ROLE_MAP.items():
            role, created = Role.objects.get_or_create(
                code=role_code,
                defaults={
                    'name': position,
                    'description': f'{position}角色',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ 创建了角色: {role.name} ({role_code})'))
            else:
                self.stdout.write(f'  ℹ️  角色已存在: {role.name} ({role_code})')
            
            roles_to_assign.append(role)
            
            # 为角色分配权限
            if role_code in self.ROLE_PERMISSIONS:
                permissions_to_add = []
                permissions_not_found = []
                
                for perm_code in self.ROLE_PERMISSIONS[role_code]:
                    try:
                        perm = PermissionItem.objects.get(code=perm_code, is_active=True)
                        permissions_to_add.append(perm)
                    except PermissionItem.DoesNotExist:
                        permissions_not_found.append(perm_code)
                
                if permissions_not_found:
                    self.stdout.write(self.style.WARNING(
                        f'    ⚠️  {role.name} 的以下权限点不存在，将跳过: {", ".join(permissions_not_found)}'
                    ))
                
                if not dry_run:
                    role.custom_permissions.set(permissions_to_add)
                    self.stdout.write(f'    ✅ 已为 {role.name} 分配 {len(permissions_to_add)} 个权限点')
                else:
                    self.stdout.write(f'    📝 将为 {role.name} 分配 {len(permissions_to_add)} 个权限点')
        
        # 3. 查找或创建陈洁滢用户
        self.stdout.write('\n📋 步骤3: 查找/创建陈洁滢用户...')
        username = '13281895910'
        phone = '13281895910'
        
        chenjieying = User.objects.filter(
            Q(username=username) | Q(phone=phone) |
            Q(first_name='洁滢', last_name='陈') | Q(first_name='陈', last_name='洁滢')
        ).first()
        
        if chenjieying:
            self.stdout.write(f'  ℹ️  用户已存在: {chenjieying.username} ({chenjieying.get_full_name()})')
            self.stdout.write(f'     当前职位: {chenjieying.position or "未设置"}')
            self.stdout.write(f'     当前部门: {chenjieying.department.name if chenjieying.department else "未设置"}')
            
            if not dry_run:
                # 更新用户信息
                chenjieying.first_name = '洁滢'
                chenjieying.last_name = '陈'
                chenjieying.phone = phone
                chenjieying.position = '、'.join(self.POSITION_ROLE_MAP.keys())  # 多个职务用顿号连接
                chenjieying.department = admin_dept
                chenjieying.user_type = 'internal'
                chenjieying.is_active = True
                chenjieying.save()
                self.stdout.write(self.style.SUCCESS('  ✅ 已更新用户信息'))
        else:
            if not dry_run:
                chenjieying = User.objects.create_user(
                    username=username,
                    first_name='洁滢',
                    last_name='陈',
                    email=f'{username}@vihhi.com',
                    phone=phone,
                    position='、'.join(self.POSITION_ROLE_MAP.keys()),
                    department=admin_dept,
                    user_type='internal',
                    is_active=True,
                    password='T159357',
                )
                self.stdout.write(self.style.SUCCESS(f'  ✅ 创建了用户: {chenjieying.username} ({chenjieying.get_full_name()})'))
            else:
                self.stdout.write(f'  📝 将创建用户: {username} (陈洁滢)')
        
        # 4. 为用户分配角色
        self.stdout.write('\n📋 步骤4: 为用户分配角色...')
        if not dry_run:
            chenjieying.roles.set(roles_to_assign)
            self.stdout.write(self.style.SUCCESS(f'  ✅ 已为用户分配 {len(roles_to_assign)} 个角色:'))
            for role in roles_to_assign:
                self.stdout.write(f'      - {role.name}')
        else:
            self.stdout.write(f'  📝 将分配 {len(roles_to_assign)} 个角色:')
            for role in roles_to_assign:
                self.stdout.write(f'      - {role.name}')
        
        # 5. 显示最终状态
        self.stdout.write('\n📋 步骤5: 验证最终状态...')
        if not dry_run:
            chenjieying.refresh_from_db()
            self.stdout.write(self.style.SUCCESS('\n✅ 陈洁滢的账号配置已完成！'))
            self.stdout.write(f'\n📊 最终状态:')
            self.stdout.write(f'   - 用户名: {chenjieying.username}')
            self.stdout.write(f'   - 姓名: {chenjieying.get_full_name()}')
            self.stdout.write(f'   - 电话: {chenjieying.phone}')
            self.stdout.write(f'   - 职位: {chenjieying.position}')
            self.stdout.write(f'   - 部门: {chenjieying.department.name if chenjieying.department else "未设置"}')
            self.stdout.write(f'   - 角色: {", ".join([r.name for r in chenjieying.roles.all()])}')
            self.stdout.write(f'   - 密码: T159357')
            
            # 显示权限
            from backend.apps.system_management.services import get_user_permission_codes
            permission_codes = get_user_permission_codes(chenjieying)
            self.stdout.write(f'\n📋 用户权限 ({len(permission_codes)} 个):')
            if permission_codes:
                # 按模块分组显示
                modules = {}
                for perm in permission_codes:
                    if perm == '__all__':
                        modules['全部权限'] = ['__all__']
                    else:
                        module = perm.split('.')[0] if '.' in perm else '其他'
                        if module not in modules:
                            modules[module] = []
                        modules[module].append(perm)
                
                for module, perms in sorted(modules.items()):
                    self.stdout.write(f'   {module}: {len(perms)} 个权限')
                    if len(perms) <= 5:
                        for perm in sorted(perms):
                            self.stdout.write(f'      - {perm}')
            else:
                self.stdout.write('   ⚠️  暂无权限（可能需要手动配置）')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  这是模拟运行，未实际修改数据'))
            self.stdout.write('   要实际执行，请移除 --dry-run 参数')

