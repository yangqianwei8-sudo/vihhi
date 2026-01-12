"""
确保计划管理模块权限组和权限分配
创建 Plan Viewer 和 Plan Editor 组，并分配相应的 Django 模型权限
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '确保计划管理模块权限组和权限分配（幂等操作）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bind-user',
            type=str,
            help='将指定用户绑定到 Plan Editor 组（例如：--bind-user tester1）'
        )

    def handle(self, *args, **options):
        self.stdout.write('开始配置计划管理模块权限...')
        
        # 获取 ContentType
        try:
            plan_ct = ContentType.objects.get(app_label='plan_management', model='plan')
            goal_ct = ContentType.objects.get(app_label='plan_management', model='strategicgoal')
        except ContentType.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'错误：找不到 ContentType: {e}'))
            return
        
        # 获取权限
        permissions_map = {
            'view_plan': Permission.objects.get(content_type=plan_ct, codename='view_plan'),
            'view_strategicgoal': Permission.objects.get(content_type=goal_ct, codename='view_strategicgoal'),
            'change_plan': Permission.objects.get(content_type=plan_ct, codename='change_plan'),
        }
        
        # 创建 Plan Viewer 组
        viewer_group, viewer_created = Group.objects.get_or_create(name='Plan Viewer')
        if viewer_created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建组：{viewer_group.name}'))
        else:
            self.stdout.write(f'  组已存在：{viewer_group.name}')
        
        # 分配查看权限给 Plan Viewer
        viewer_perms = [permissions_map['view_plan'], permissions_map['view_strategicgoal']]
        added_count = 0
        for perm in viewer_perms:
            if perm not in viewer_group.permissions.all():
                viewer_group.permissions.add(perm)
                added_count += 1
        
        if added_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ 为 Plan Viewer 添加 {added_count} 个权限'))
        else:
            self.stdout.write('  Plan Viewer 权限已完整')
        
        # 创建 Plan Editor 组
        editor_group, editor_created = Group.objects.get_or_create(name='Plan Editor')
        if editor_created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建组：{editor_group.name}'))
        else:
            self.stdout.write(f'  组已存在：{editor_group.name}')
        
        # Plan Editor 继承 Plan Viewer 的所有权限，再加上 change_plan
        editor_perms = viewer_perms + [permissions_map['change_plan']]
        added_count = 0
        for perm in editor_perms:
            if perm not in editor_group.permissions.all():
                editor_group.permissions.add(perm)
                added_count += 1
        
        if added_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✓ 为 Plan Editor 添加 {added_count} 个权限'))
        else:
            self.stdout.write('  Plan Editor 权限已完整')
        
        # 绑定用户（如果指定）
        bind_username = options.get('bind_user')
        if bind_username:
            try:
                user = User.objects.get(username=bind_username)
                if editor_group not in user.groups.all():
                    user.groups.add(editor_group)
                    self.stdout.write(self.style.SUCCESS(f'✓ 将用户 {bind_username} 加入 Plan Editor 组'))
                else:
                    self.stdout.write(f'  用户 {bind_username} 已在 Plan Editor 组中')
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ 用户 {bind_username} 不存在，跳过绑定'))
        
        # 输出摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('权限配置完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'\n组配置：')
        self.stdout.write(f'  Plan Viewer ({viewer_group.permissions.count()} 个权限)')
        for perm in viewer_group.permissions.all():
            self.stdout.write(f'    - {perm.content_type.app_label}.{perm.codename}')
        self.stdout.write(f'\n  Plan Editor ({editor_group.permissions.count()} 个权限)')
        for perm in editor_group.permissions.all():
            self.stdout.write(f'    - {perm.content_type.app_label}.{perm.codename}')
        
        if bind_username:
            try:
                user = User.objects.get(username=bind_username)
                user_groups = [g.name for g in user.groups.all()]
                self.stdout.write(f'\n用户 {bind_username} 所属组：{", ".join(user_groups) if user_groups else "无"}')
            except User.DoesNotExist:
                pass
        
        self.stdout.write('='*60)

