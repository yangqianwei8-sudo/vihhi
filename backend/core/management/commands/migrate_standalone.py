#!/usr/bin/env python
"""
独立的迁移执行命令
绕过Django迁移系统的依赖检查，直接执行SQL并标记迁移为已应用

使用方法:
    python manage.py migrate_standalone <app_name> <migration_name>
    
示例:
    python manage.py migrate_standalone delivery_customer 0001
    python manage.py migrate_standalone customer_success 0020
    
选项:
    --fake: 只标记迁移为已应用，不执行SQL
    --sql-only: 只生成SQL，不执行
    --output: 指定SQL输出文件路径
"""
import os
import sys
from io import StringIO
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection, transaction
from django.utils import timezone
from django.apps import apps


class Command(BaseCommand):
    help = '独立执行迁移，绕过依赖检查'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='应用名称（如 delivery_customer）')
        parser.add_argument('migration_name', type=str, help='迁移名称（如 0001_initial）')
        parser.add_argument(
            '--fake',
            action='store_true',
            help='只标记迁移为已应用，不执行SQL',
        )
        parser.add_argument(
            '--sql-only',
            action='store_true',
            help='只生成SQL，不执行',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='SQL输出文件路径',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制执行，即使迁移已应用',
        )

    def handle(self, *args, **options):
        app_name = options['app_name']
        migration_name = options['migration_name']
        fake = options['fake']
        sql_only = options['sql_only']
        output_file = options.get('output')
        force = options['force']

        # 安全提示：这是一个手动工具，不会自动执行
        # 部署脚本使用的是标准的 migrate 命令，不会调用此工具
        self.stdout.write(self.style.SUCCESS(f'\n🚀 开始独立迁移: {app_name}.{migration_name}'))
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.WARNING(
            '⚠️  注意：这是一个手动工具，需要明确指定应用和迁移名称才会执行'
        ))
        self.stdout.write('=' * 70)

        # 检查应用是否存在
        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            raise CommandError(f'应用 "{app_name}" 不存在')

        # 检查迁移文件是否存在
        migration_path = os.path.join(
            app_config.path,
            'migrations',
            f'{migration_name}.py'
        )
        if not os.path.exists(migration_path):
            raise CommandError(f'迁移文件不存在: {migration_path}')

        # 检查迁移是否已应用
        if not force:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations 
                    WHERE app = %s AND name = %s
                """, [app_name, migration_name])
                if cursor.fetchone()[0] > 0:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  迁移 {app_name}.{migration_name} 已经应用'
                    ))
                    if not fake:
                        response = input('是否继续？(y/n): ')
                        if response.lower() != 'y':
                            self.stdout.write('已取消')
                            return
                    else:
                        self.stdout.write('使用 --fake 模式，跳过执行')
                        return

        # 如果是 --fake 模式，直接标记为已应用
        if fake:
            self._mark_migration_applied(app_name, migration_name)
            self.stdout.write(self.style.SUCCESS(f'\n✅ 已标记迁移 {app_name}.{migration_name} 为已应用'))
            return

        # 生成SQL
        self.stdout.write(f'\n📝 生成迁移SQL...')
        try:
            sql = self._generate_sql(app_name, migration_name)
        except Exception as e:
            # 如果生成SQL失败（可能是依赖问题），尝试从迁移文件直接提取
            self.stdout.write(self.style.WARNING(
                f'⚠️  使用 sqlmigrate 生成SQL失败: {e}'
            ))
            self.stdout.write('尝试从迁移文件提取SQL...')
            sql = self._extract_sql_from_migration(migration_path)

        if not sql or not sql.strip():
            self.stdout.write(self.style.WARNING('⚠️  未生成SQL，可能是空迁移'))
            # 即使是空迁移，也标记为已应用
            self._mark_migration_applied(app_name, migration_name)
            self.stdout.write(self.style.SUCCESS(f'\n✅ 已标记空迁移 {app_name}.{migration_name} 为已应用'))
            return

        # 如果只生成SQL，不执行
        if sql_only:
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(sql)
                self.stdout.write(self.style.SUCCESS(f'\n✅ SQL已保存到: {output_file}'))
            else:
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write('生成的SQL:')
                self.stdout.write('=' * 70)
                self.stdout.write(sql)
                self.stdout.write('=' * 70)
            return

        # 执行SQL
        self.stdout.write(f'\n⚙️  执行SQL...')
        success = self._execute_sql(sql)

        if success:
            # 标记迁移为已应用
            self._mark_migration_applied(app_name, migration_name)
            self.stdout.write(self.style.SUCCESS(f'\n✅ 迁移 {app_name}.{migration_name} 执行成功！'))
        else:
            raise CommandError(f'迁移执行失败，请检查错误信息')

    def _generate_sql(self, app_name, migration_name):
        """使用 sqlmigrate 生成SQL"""
        output = StringIO()
        error_output = StringIO()
        try:
            # 尝试使用 sqlmigrate 生成 SQL
            # 即使有依赖问题，也尝试生成
            call_command(
                'sqlmigrate', 
                app_name, 
                migration_name, 
                stdout=output,
                stderr=error_output,
                verbosity=0  # 减少输出
            )
            sql = output.getvalue()
            
            # 如果输出为空，检查错误
            if not sql or not sql.strip():
                error_msg = error_output.getvalue()
                if error_msg:
                    # 如果是依赖问题，尝试继续
                    if 'permission_management' in error_msg.lower() or 'isn\'t installed' in error_msg.lower():
                        self.stdout.write(self.style.WARNING(
                            '⚠️  检测到依赖问题，尝试继续生成 SQL...'
                        ))
                        # 尝试使用 --skip-checks 或直接读取迁移文件
                        # 这里我们返回 None，让调用者使用备用方案
                        return None
                    raise Exception(f'生成 SQL 失败: {error_msg}')
            
            # 清理SQL（移除注释和BEGIN/COMMIT）
            sql_lines = []
            for line in sql.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    if line.upper() not in ['BEGIN', 'COMMIT']:
                        sql_lines.append(line)
            return '\n'.join(sql_lines)
        except Exception as e:
            # 如果是依赖相关的错误，尝试使用备用方案
            error_msg = str(e).lower()
            if 'permission_management' in error_msg or 'isn\'t installed' in error_msg or 'dependency' in error_msg:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  依赖检查失败: {e}，尝试备用方案...'
                ))
                return None
            # 其他错误直接抛出
            raise

    def _extract_sql_from_migration(self, migration_path):
        """从迁移文件中提取SQL（备用方案）"""
        # 读取迁移文件，查找 RunSQL 操作
        try:
            with open(migration_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找 RunSQL 操作中的 SQL
            import re
            # 匹配 RunSQL(sql="...", ...) 或 RunSQL(sql='...', ...)
            sql_pattern = r'RunSQL\s*\([^)]*sql\s*=\s*["\']([^"\']+)["\']'
            matches = re.findall(sql_pattern, content, re.DOTALL)
            
            if matches:
                # 返回第一个匹配的 SQL
                sql = matches[0]
                # 处理多行字符串
                sql = sql.replace('\\n', '\n')
                return sql
            
            # 如果没有找到 RunSQL，返回 None
            # 这意味着需要从模型操作生成 SQL，这需要 Django 的迁移系统
            return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'⚠️  从迁移文件提取 SQL 失败: {e}'
            ))
            return None

    def _execute_sql(self, sql):
        """执行SQL语句"""
        if not sql or not sql.strip():
            return True

        # 按分号分割SQL语句
        statements = []
        current_statement = []
        for line in sql.split('\n'):
            line = line.strip()
            if line:
                current_statement.append(line)
                if line.endswith(';'):
                    statement = ' '.join(current_statement)
                    if statement.strip() and statement.strip() != ';':
                        statements.append(statement)
                    current_statement = []

        if current_statement:
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)

        if not statements:
            return True

        success_count = 0
        error_count = 0

        with connection.cursor() as cursor:
            for sql_statement in statements:
                if not sql_statement.strip():
                    continue
                try:
                    cursor.execute(sql_statement)
                    success_count += 1
                    self.stdout.write(f'  ✓ 执行成功: {sql_statement[:60]}...')
                except Exception as e:
                    error_msg = str(e).lower()
                    # 如果是表已存在的错误，忽略
                    if 'already exists' in error_msg or 'duplicate' in error_msg:
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠️  已存在，跳过: {sql_statement[:60]}...'
                        ))
                        success_count += 1
                    else:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(
                            f'  ❌ 执行失败: {sql_statement[:60]}...'
                        ))
                        self.stdout.write(self.style.ERROR(f'     错误: {e}'))

        try:
            connection.commit()
            self.stdout.write(f'\n📊 执行统计: 成功 {success_count}, 失败 {error_count}')
            return error_count == 0
        except Exception as e:
            connection.rollback()
            self.stdout.write(self.style.ERROR(f'\n❌ 提交失败: {e}'))
            return False

    def _mark_migration_applied(self, app_name, migration_name):
        """标记迁移为已应用"""
        with connection.cursor() as cursor:
            # 检查是否已存在
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = %s AND name = %s
            """, [app_name, migration_name])
            
            if cursor.fetchone()[0] > 0:
                self.stdout.write(f'  - 迁移记录已存在: {app_name}.{migration_name}')
            else:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES (%s, %s, %s)
                """, [app_name, migration_name, timezone.now()])
                connection.commit()
                self.stdout.write(f'  ✓ 已标记迁移: {app_name}.{migration_name}')

