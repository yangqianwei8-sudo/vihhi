"""
强制清除用户数据的管理命令
清除除系统管理员、杨乾维、田霞、陈洁滢、袁鑫、姜松琴、何静以外的所有用户
"""
from django.core.management.base import BaseCommand
from django.db import transaction, models, connections
from django.db.models import Q
from django.db.utils import ProgrammingError, OperationalError
from django.apps import apps
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "强制清除除指定用户外的所有用户及其关联数据"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='跳过确认提示，直接执行删除',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("开始强制清除用户数据..."))
        
        # 1. 识别需要保留的用户
        keep_users = self._identify_keep_users()
        
        if not keep_users:
            self.stdout.write(self.style.ERROR("错误：未找到任何需要保留的用户！"))
            self.stdout.write(self.style.ERROR("至少需要保留一个系统管理员用户。"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"识别到 {len(keep_users)} 个需要保留的用户："))
        for user in keep_users:
            self.stdout.write(f"  - {user.username} ({user.get_full_name() or '未设置姓名'})")
        
        # 2. 查询需要删除的用户
        keep_user_ids = [user.id for user in keep_users]
        users_to_delete = User.objects.exclude(id__in=keep_user_ids)
        delete_count = users_to_delete.count()
        
        if delete_count == 0:
            self.stdout.write(self.style.SUCCESS("没有需要删除的用户。"))
            return
        
        # 3. 显示待删除用户列表
        self.stdout.write(self.style.WARNING(f"\n将要删除 {delete_count} 个用户："))
        for user in users_to_delete[:20]:  # 只显示前20个
            self.stdout.write(f"  - {user.username} ({user.get_full_name() or '未设置姓名'})")
        if delete_count > 20:
            self.stdout.write(f"  ... 还有 {delete_count - 20} 个用户")
        
        # 4. 确认操作
        if not options['no_confirm']:
            self.stdout.write(self.style.WARNING("\n警告：此操作不可逆，将永久删除用户及其关联数据！"))
            confirm = input("确认执行删除操作？输入 'yes' 继续: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR("操作已取消。"))
                return
        
        # 5. 执行删除
        self._delete_users(users_to_delete)
        
        self.stdout.write(self.style.SUCCESS("\n用户清除完成！"))

    def _identify_keep_users(self):
        """识别需要保留的用户"""
        keep_users = []
        
        # 1. 系统管理员
        superusers = User.objects.filter(is_superuser=True)
        keep_users.extend(superusers)
        self.stdout.write(f"找到 {superusers.count()} 个系统管理员")
        
        # 2. 通过姓名识别指定用户
        # 定义需要保留的用户姓名（支持多种可能的存储方式）
        target_names = [
            '杨乾维', '田霞', '陈洁滢', '袁鑫', '姜松琴', '何静'
        ]
        
        name_mappings = [
            # 杨乾维：可能是 '杨' + '乾维' 或 '杨乾' + '维' 或全在 first_name/last_name
            {'first_name': '杨', 'last_name': '乾维'},
            {'first_name': '杨乾', 'last_name': '维'},
            {'first_name': '杨乾维', 'last_name': ''},
            {'first_name': '', 'last_name': '杨乾维'},
            # 田霞
            {'first_name': '田', 'last_name': '霞'},
            {'first_name': '田霞', 'last_name': ''},
            {'first_name': '', 'last_name': '田霞'},
            # 陈洁滢：可能是 '陈' + '洁滢' 或 '陈洁' + '滢'
            {'first_name': '陈', 'last_name': '洁滢'},
            {'first_name': '陈洁', 'last_name': '滢'},
            {'first_name': '陈洁滢', 'last_name': ''},
            {'first_name': '', 'last_name': '陈洁滢'},
            # 袁鑫
            {'first_name': '袁', 'last_name': '鑫'},
            {'first_name': '袁鑫', 'last_name': ''},
            {'first_name': '', 'last_name': '袁鑫'},
            # 姜松琴：可能是 '姜' + '松琴' 或 '姜松' + '琴'
            {'first_name': '姜', 'last_name': '松琴'},
            {'first_name': '姜松', 'last_name': '琴'},
            {'first_name': '姜松琴', 'last_name': ''},
            {'first_name': '', 'last_name': '姜松琴'},
            # 何静
            {'first_name': '何', 'last_name': '静'},
            {'first_name': '何静', 'last_name': ''},
            {'first_name': '', 'last_name': '何静'},
        ]
        
        found_users = set()
        for mapping in name_mappings:
            # 构建查询条件
            query = Q()
            if mapping['first_name']:
                query &= Q(first_name=mapping['first_name'])
            if mapping['last_name']:
                query &= Q(last_name=mapping['last_name'])
            
            # 如果两个都为空，跳过
            if not query:
                continue
                
            users = User.objects.filter(query)
            for user in users:
                # 验证完整姓名是否匹配目标姓名
                full_name = user.get_full_name() or f"{user.first_name}{user.last_name}"
                if any(target_name in full_name for target_name in target_names):
                    found_users.add(user.id)
        
        if found_users:
            name_users = User.objects.filter(id__in=found_users)
            keep_users.extend(name_users)
            self.stdout.write(f"通过姓名找到 {len(found_users)} 个指定用户")
            for user in name_users:
                self.stdout.write(f"  - {user.username}: {user.get_full_name() or f'{user.first_name}{user.last_name}'}")
        
        # 去重
        keep_users_dict = {user.id: user for user in keep_users}
        return list(keep_users_dict.values())

    def _delete_users(self, users_queryset):
        """删除用户及其关联数据"""
        deleted_count = 0
        failed_users = []
        
        for user in users_queryset:
            username = user.username
            try:
                # 先清理用户的所有关联数据（在事务外执行，避免事务冲突）
                try:
                    self._cleanup_user_references(user)
                except Exception as cleanup_error:
                    # 清理过程中的错误不影响删除，记录但继续
                    error_str = str(cleanup_error).lower()
                    if 'does not exist' not in error_str and 'relation' not in error_str:
                        self.stdout.write(self.style.WARNING(f"  警告：清理 {username} 的关联数据时出错: {str(cleanup_error)[:100]}"))
                
                # 在事务中执行删除操作
                try:
                    with transaction.atomic():
                        # 清理多对多关系
                        try:
                            user.roles.clear()
                        except Exception:
                            pass
                        try:
                            user.groups.clear()
                        except Exception:
                            pass
                        try:
                            user.user_permissions.clear()
                        except Exception:
                            pass
                        
                        # 使用原始SQL删除用户，避免Django ORM访问不存在的表
                        db_conn = connections['default']
                        with db_conn.cursor() as cursor:
                            cursor.execute("DELETE FROM system_user WHERE id = %s", [user.id])
                            if cursor.rowcount > 0:
                                deleted_count += 1
                                self.stdout.write(f"  ✓ 已删除用户: {username}")
                            else:
                                failed_users.append((username, "用户不存在或已被删除"))
                except Exception as delete_error:
                    error_str = str(delete_error).lower()
                    # 如果是表不存在的错误，尝试使用原始SQL删除
                    if 'does not exist' in error_str or 'relation' in error_str:
                        try:
                            db_conn = connections['default']
                            with db_conn.cursor() as cursor:
                                cursor.execute("DELETE FROM system_user WHERE id = %s", [user.id])
                                if cursor.rowcount > 0:
                                    deleted_count += 1
                                    self.stdout.write(f"  ✓ 已删除用户: {username} (使用原始SQL)")
                                else:
                                    failed_users.append((username, "用户不存在"))
                        except Exception as sql_error:
                            failed_users.append((username, str(sql_error)[:100]))
                    else:
                        failed_users.append((username, str(delete_error)[:100]))
                        self.stdout.write(self.style.ERROR(f"  ✗ 删除用户失败: {username} - {str(delete_error)[:100]}"))
                    
            except Exception as e:
                failed_users.append((username, str(e)[:100]))
                self.stdout.write(self.style.ERROR(f"  ✗ 删除用户失败: {username} - {str(e)[:100]}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n成功删除 {deleted_count} 个用户"))
        if failed_users:
            self.stdout.write(self.style.ERROR(f"删除失败 {len(failed_users)} 个用户："))
            for username, error in failed_users[:10]:  # 只显示前10个错误
                self.stdout.write(self.style.ERROR(f"  - {username}: {error}"))
            if len(failed_users) > 10:
                self.stdout.write(self.style.ERROR(f"  ... 还有 {len(failed_users) - 10} 个失败的用户"))

    def _cleanup_user_references(self, user):
        """清理用户的所有 PROTECT 约束引用，通过直接更新数据库绕过约束"""
        # 获取所有模型
        all_models = apps.get_models()
        
        # 使用数据库连接
        db_connection = connections['default']
        
        # 先获取所有存在的表名（一次性查询，提高效率）
        existing_tables = set()
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                existing_tables = {row[0] for row in cursor.fetchall()}
        except Exception:
            # 如果查询失败，继续执行，但会在后续步骤中逐个检查
            pass
        
        # 查找所有引用 system_user 表的外键约束（包括数据库级别的约束）
        self._cleanup_database_foreign_keys(user, db_connection, existing_tables)
        
        # 收集需要清理的表和字段
        cleanup_tasks = []
        for model in all_models:
            # 跳过 User 模型本身
            if model == User:
                continue
            
            # 获取表名
            table_name = model._meta.db_table
            
            # 如果已知表不存在，跳过
            if existing_tables and table_name not in existing_tables:
                continue
                
            # 检查模型的所有字段
            try:
                for field in model._meta.get_fields():
                    if isinstance(field, models.ForeignKey):
                        # 检查是否是引用 User 模型的外键
                        related_model = getattr(field, 'related_model', None)
                        if related_model == User:
                            # 检查是否是 PROTECT 约束
                            if hasattr(field, 'remote_field') and field.remote_field.on_delete == models.PROTECT:
                                # 获取字段名
                                field_name = field.column
                                cleanup_tasks.append((table_name, field_name, field.null))
            except Exception:
                # 如果访问模型元数据失败（可能因为表不存在），跳过这个模型
                continue
        
        # 为每个清理任务使用独立的事务
        for table_name, field_name, allow_null in cleanup_tasks:
            try:
                # 再次确认表存在（双重检查）
                if existing_tables and table_name not in existing_tables:
                    continue
                    
                with transaction.atomic():
                    with db_connection.cursor() as cursor:
                        # 再次检查表是否存在
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = %s
                            )
                        """, [table_name])
                        table_exists = cursor.fetchone()[0]
                        
                        if not table_exists:
                            # 表不存在，跳过
                            continue
                        
                        # 如果字段允许 NULL，设置为 NULL
                        if allow_null:
                            try:
                                sql = f'UPDATE {table_name} SET {field_name} = NULL WHERE {field_name} = %s'
                                cursor.execute(sql, [user.id])
                                updated = cursor.rowcount
                                if updated > 0:
                                    self.stdout.write(f"    - 已清理 {table_name}.{field_name}: {updated} 条记录设置为 NULL")
                            except (ProgrammingError, OperationalError) as e:
                                # 如果表或字段不存在，跳过
                                error_str = str(e).lower()
                                if 'does not exist' in error_str or 'relation' in error_str:
                                    continue
                                raise
                        else:
                            # 如果字段不允许 NULL，删除相关记录
                            try:
                                sql = f'DELETE FROM {table_name} WHERE {field_name} = %s'
                                cursor.execute(sql, [user.id])
                                deleted = cursor.rowcount
                                if deleted > 0:
                                    self.stdout.write(f"    - 已删除 {table_name}.{field_name}: {deleted} 条记录")
                            except (ProgrammingError, OperationalError) as e:
                                # 如果表或字段不存在，跳过
                                error_str = str(e).lower()
                                if 'does not exist' in error_str or 'relation' in error_str:
                                    continue
                                raise
            except (ProgrammingError, OperationalError) as e:
                # 如果表不存在或其他数据库错误，跳过这个表
                error_str = str(e).lower()
                if 'does not exist' in error_str or 'relation' in error_str or 'current transaction is aborted' in error_str:
                    # 回滚当前事务并继续
                    try:
                        transaction.rollback()
                    except:
                        pass
                    continue
                # 其他错误也跳过，避免影响整体删除
                try:
                    transaction.rollback()
                except:
                    pass
                continue
            except Exception as e:
                # 其他未知错误，回滚并继续
                error_str = str(e).lower()
                if 'does not exist' in error_str or 'relation' in error_str:
                    try:
                        transaction.rollback()
                    except:
                        pass
                    continue
                # 对于其他错误，也尝试继续
                try:
                    transaction.rollback()
                except:
                    pass
                continue
    
    def _cleanup_database_foreign_keys(self, user, db_connection, existing_tables):
        """清理所有数据库级别的外键约束引用（包括所有类型的外键，不仅仅是PROTECT）"""
        try:
            with db_connection.cursor() as cursor:
                # 查找所有引用 system_user 表的外键约束
                cursor.execute("""
                    SELECT 
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND ccu.table_name = 'system_user'
                        AND tc.table_schema = 'public'
                """)
                
                foreign_keys = cursor.fetchall()
                
                for table_name, column_name, _, _, constraint_name in foreign_keys:
                    # 跳过不存在的表
                    if existing_tables and table_name not in existing_tables:
                        continue
                    
                    try:
                        # 检查字段是否允许NULL
                        cursor.execute("""
                            SELECT is_nullable
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                                AND table_name = %s
                                AND column_name = %s
                        """, [table_name, column_name])
                        
                        result = cursor.fetchone()
                        if not result:
                            continue
                        
                        allow_null = result[0] == 'YES'
                        
                        # 在独立事务中处理
                        with transaction.atomic():
                            with db_connection.cursor() as inner_cursor:
                                if allow_null:
                                    # 设置为 NULL
                                    sql = f'UPDATE {table_name} SET {column_name} = NULL WHERE {column_name} = %s'
                                    inner_cursor.execute(sql, [user.id])
                                    updated = inner_cursor.rowcount
                                    if updated > 0:
                                        self.stdout.write(f"    - 已清理 {table_name}.{column_name}: {updated} 条记录设置为 NULL (外键约束: {constraint_name})")
                                else:
                                    # 删除相关记录
                                    sql = f'DELETE FROM {table_name} WHERE {column_name} = %s'
                                    inner_cursor.execute(sql, [user.id])
                                    deleted = inner_cursor.rowcount
                                    if deleted > 0:
                                        self.stdout.write(f"    - 已删除 {table_name}.{column_name}: {deleted} 条记录 (外键约束: {constraint_name})")
                    except (ProgrammingError, OperationalError) as e:
                        error_str = str(e).lower()
                        if 'does not exist' in error_str or 'relation' in error_str:
                            continue
                        # 其他错误也跳过
                        try:
                            transaction.rollback()
                        except:
                            pass
                        continue
                    except Exception:
                        # 其他错误也跳过
                        try:
                            transaction.rollback()
                        except:
                            pass
                        continue
        except Exception as e:
            # 如果查询外键失败，不影响主流程
            error_str = str(e).lower()
            if 'does not exist' not in error_str and 'relation' not in error_str:
                # 只记录非表不存在的错误，但不影响主流程
                pass

