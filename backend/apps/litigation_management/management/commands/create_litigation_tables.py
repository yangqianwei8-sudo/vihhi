"""
直接创建诉讼管理模块的数据库表
用于解决迁移依赖问题
"""
import logging
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '直接创建诉讼管理模块的数据库表（用于解决迁移依赖问题）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建表（会删除现有表）',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.SUCCESS('开始创建诉讼管理模块的数据库表...'))

        cursor = connection.cursor()

        # 读取SQL文件
        import os
        from django.conf import settings
        
        sql_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'migrations', 'create_missing_tables.sql'
        )
        
        if not os.path.exists(sql_file):
            self.stdout.write(self.style.ERROR(f'SQL文件不存在: {sql_file}'))
            return

        # 读取SQL内容
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 如果使用force，先删除表
        if force:
            tables_to_drop = [
                'litigation_notification_confirmation',
                'preservation_seal',
                'litigation_person',
                'litigation_document',
                'litigation_process',
            ]
            
            self.stdout.write(self.style.WARNING('删除现有表...'))
            for table in tables_to_drop:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                    self.stdout.write(f'  ✓ 删除表: {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ 删除表失败 {table}: {e}'))

        # 执行SQL
        try:
            # 直接执行整个SQL文件（使用execute而不是按分号分割）
            # 因为SQL文件可能包含DO块等复杂结构
            success_count = 0
            error_count = 0
            
            try:
                cursor.execute(sql_content)
                connection.commit()
                success_count += 1
                self.stdout.write(self.style.SUCCESS('  ✓ SQL执行成功'))
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                # 如果表已存在，不算错误
                if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    self.stdout.write(self.style.WARNING(f'  ⚠ 部分对象已存在: {error_msg[:100]}'))
                    success_count += 1
                    error_count -= 1
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ 执行失败: {error_msg[:200]}'))
                    # 尝试逐条执行（如果整体执行失败）
                    self.stdout.write('  尝试逐条执行SQL语句...')
                    # 移除注释和空行，然后按分号分割（但保留DO块）
                    lines = sql_content.split('\n')
                    cleaned_lines = []
                    in_do_block = False
                    current_statement = []
                    
                    for line in lines:
                        stripped = line.strip()
                        # 跳过注释
                        if stripped.startswith('--'):
                            continue
                        if not stripped:
                            continue
                        
                        # 检查是否进入DO块
                        if 'DO $$' in stripped.upper():
                            in_do_block = True
                            current_statement = [line]
                            continue
                        
                        if in_do_block:
                            current_statement.append(line)
                            if 'END $$' in stripped.upper():
                                # 执行完整的DO块
                                do_block_sql = '\n'.join(current_statement)
                                try:
                                    cursor.execute(do_block_sql)
                                    self.stdout.write('  ✓ 执行DO块成功')
                                except Exception as e2:
                                    self.stdout.write(self.style.WARNING(f'  ⚠ DO块执行警告: {str(e2)[:100]}'))
                                in_do_block = False
                                current_statement = []
                            continue
                        
                        # 普通SQL语句
                        current_statement.append(line)
                        if stripped.endswith(';'):
                            sql_stmt = '\n'.join(current_statement)
                            try:
                                cursor.execute(sql_stmt)
                                # 提取表名或索引名
                                if 'CREATE TABLE' in sql_stmt.upper():
                                    parts = sql_stmt.split('CREATE TABLE')[1].split()
                                    if parts:
                                        obj_name = parts[0].strip()
                                        self.stdout.write(f'  ✓ 创建表: {obj_name}')
                                elif 'CREATE INDEX' in sql_stmt.upper():
                                    parts = sql_stmt.split('CREATE INDEX')[1].split()
                                    if parts:
                                        obj_name = parts[0].strip()
                                        self.stdout.write(f'  ✓ 创建索引: {obj_name}')
                            except Exception as e2:
                                error_msg2 = str(e2)
                                if 'already exists' not in error_msg2.lower():
                                    self.stdout.write(self.style.WARNING(f'  ⚠ 执行警告: {error_msg2[:100]}'))
                            current_statement = []
                    
                    connection.commit()
            
            self.stdout.write(self.style.SUCCESS(f'\n完成！成功: {success_count}, 失败: {error_count}'))
            
            # 验证表是否创建成功
            self.stdout.write('\n验证表是否存在...')
            tables_to_check = [
                'litigation_process',
                'litigation_document',
                'litigation_person',
                'preservation_seal',
                'litigation_notification_confirmation',
            ]
            
            for table_name in tables_to_check:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, [table_name])
                exists = cursor.fetchone()[0]
                status = "✓" if exists else "✗"
                self.stdout.write(f'{status} {table_name}')
            
        except Exception as e:
            connection.rollback()
            self.stdout.write(self.style.ERROR(f'执行SQL失败: {str(e)}'))
            logger.error(f'创建表失败: {str(e)}', exc_info=True)
        finally:
            cursor.close()

