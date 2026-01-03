from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from backend.apps.system_management.models import User, Role, Department
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '设置田霞为商务总监并分配相应权限'

    # 商务总监应该拥有的权限点
    BUSINESS_DIRECTOR_PERMISSIONS = [
        # 商机管理 - 查看权限
        'customer_management.opportunity.view',
        'customer_management.opportunity.view_all',  # 查看全部商机
        
        # 商机管理 - 操作权限
        'customer_management.opportunity.create',
        'customer_management.opportunity.edit',
        'customer_management.opportunity.delete',
        'customer_management.opportunity.manage',
        
        # 客户管理 - 查看权限
        'customer_management.client.view',
        'customer_management.client.view_all',  # 查看全部客户
        
        # 客户管理 - 操作权限
        'customer_management.client.create',
        'customer_management.client.edit',
        'customer_management.client.delete',
        
        # 合同管理权限（如果有）
        'customer_management.contract.view',
        'customer_management.contract.view_all',
        'customer_management.contract.create',
        'customer_management.contract.edit',
        'customer_management.contract.manage',
    ]

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
        
        # 1. 创建或获取商务总监角色
        self.stdout.write('\n📋 步骤1: 创建/获取商务总监角色...')
        business_director_role, created = Role.objects.get_or_create(
            code='business_director',
            defaults={
                'name': '商务总监',
                'description': '商务总监角色，拥有查看全部商机、审批商机、销售数据分析、团队绩效管理等权限',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✅ 创建了商务总监角色: {business_director_role.name}'))
        else:
            self.stdout.write(f'  ℹ️  商务总监角色已存在: {business_director_role.name}')
        
        # 2. 为商务总监角色分配权限
        self.stdout.write('\n📋 步骤2: 为商务总监角色分配权限...')
        permissions_to_add = []
        permissions_not_found = []
        
        for perm_code in self.BUSINESS_DIRECTOR_PERMISSIONS:
            try:
                perm = PermissionItem.objects.get(code=perm_code, is_active=True)
                permissions_to_add.append(perm)
            except PermissionItem.DoesNotExist:
                permissions_not_found.append(perm_code)
        
        if permissions_not_found:
            self.stdout.write(self.style.WARNING(f'  ⚠️  以下权限点不存在，将跳过: {", ".join(permissions_not_found)}'))
        
        if not dry_run:
            # 添加权限到角色
            business_director_role.custom_permissions.set(permissions_to_add)
            self.stdout.write(self.style.SUCCESS(f'  ✅ 已为商务总监角色分配 {len(permissions_to_add)} 个权限点'))
        else:
            self.stdout.write(f'  📝 将分配 {len(permissions_to_add)} 个权限点:')
            for perm in permissions_to_add:
                self.stdout.write(f'      - {perm.code} ({perm.name})')
        
        # 3. 查找田霞用户
        self.stdout.write('\n📋 步骤3: 查找田霞用户...')
        tianxia = User.objects.filter(
            Q(username='tianxia') | Q(username='13666287899') |
            Q(first_name='田', last_name='霞') | Q(phone='13666287899')
        ).first()
        
        if not tianxia:
            self.stdout.write(self.style.ERROR('  ❌ 未找到田霞用户'))
            return
        
        self.stdout.write(f'  ✅ 找到用户: {tianxia.username} ({tianxia.get_full_name()})')
        self.stdout.write(f'     当前职位: {tianxia.position or "未设置"}')
        self.stdout.write(f'     当前部门: {tianxia.department.name if tianxia.department else "未设置"}')
        self.stdout.write(f'     当前角色: {", ".join([r.name for r in tianxia.roles.all()]) or "无"}')
        
        # 4. 更新田霞的职位和角色
        self.stdout.write('\n📋 步骤4: 更新田霞的职位和角色...')
        
        if not dry_run:
            # 更新职位
            old_position = tianxia.position
            tianxia.position = '商务总监'
            tianxia.save()
            
            if old_position != '商务总监':
                self.stdout.write(self.style.SUCCESS(f'  ✅ 职位已更新: {old_position} → 商务总监'))
            else:
                self.stdout.write(f'  ℹ️  职位已是商务总监，无需更新')
            
            # 移除旧的商务部经理角色（如果存在）
            old_roles = list(tianxia.roles.all())
            business_manager_role = Role.objects.filter(code='business_manager').first()
            business_team_role = Role.objects.filter(code='business_team').first()
            
            if business_manager_role and business_manager_role in old_roles:
                tianxia.roles.remove(business_manager_role)
                self.stdout.write(f'  ✅ 已移除旧角色: 商务部经理')
            
            if business_team_role and business_team_role in old_roles:
                tianxia.roles.remove(business_team_role)
                self.stdout.write(f'  ✅ 已移除旧角色: 商务部团队')
            
            # 添加商务总监角色
            if business_director_role not in old_roles:
                tianxia.roles.add(business_director_role)
                self.stdout.write(self.style.SUCCESS(f'  ✅ 已添加角色: 商务总监'))
            else:
                self.stdout.write(f'  ℹ️  用户已拥有商务总监角色')
        else:
            self.stdout.write(f'  📝 将执行以下操作:')
            self.stdout.write(f'      - 更新职位: {tianxia.position or "未设置"} → 商务总监')
            if business_manager_role := Role.objects.filter(code='business_manager').first():
                if business_manager_role in tianxia.roles.all():
                    self.stdout.write(f'      - 移除角色: 商务部经理')
            if business_director_role not in tianxia.roles.all():
                self.stdout.write(f'      - 添加角色: 商务总监')
        
        # 5. 显示最终状态
        self.stdout.write('\n📋 步骤5: 验证最终状态...')
        if not dry_run:
            tianxia.refresh_from_db()
            self.stdout.write(self.style.SUCCESS('\n✅ 田霞的权限配置已完成！'))
            self.stdout.write(f'\n📊 最终状态:')
            self.stdout.write(f'   - 用户名: {tianxia.username}')
            self.stdout.write(f'   - 姓名: {tianxia.get_full_name()}')
            self.stdout.write(f'   - 职位: {tianxia.position}')
            self.stdout.write(f'   - 部门: {tianxia.department.name if tianxia.department else "未设置"}')
            self.stdout.write(f'   - 角色: {", ".join([r.name for r in tianxia.roles.all()])}')
            
            # 显示权限
            from backend.apps.system_management.services import get_user_permission_codes
            permission_codes = get_user_permission_codes(tianxia)
            opportunity_perms = [p for p in permission_codes if 'opportunity' in p]
            self.stdout.write(f'\n📋 商机管理权限 ({len(opportunity_perms)} 个):')
            for perm in sorted(opportunity_perms):
                self.stdout.write(f'   - {perm}')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  这是模拟运行，未实际修改数据'))
            self.stdout.write('   要实际执行，请移除 --dry-run 参数')

