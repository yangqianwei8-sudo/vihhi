"""
Django管理命令：检查Plan表字段状态

使用方法：
    python manage.py check_plan_fields
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '检查Plan表字段状态（用于字段治理）'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("检查Plan表字段状态")
        self.stdout.write("=" * 60)
        
        table_name = 'plan_plan'
        
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, [table_name])
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(self.style.ERROR(f"\n✗ 表 {table_name} 不存在"))
                return
            
            self.stdout.write(self.style.SUCCESS(f"\n✓ 表 {table_name} 存在"))
            
            # 获取所有字段
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, [table_name])
            columns = cursor.fetchall()
            
            self.stdout.write(f"\n找到 {len(columns)} 个字段:")
            self.stdout.write("-" * 60)
            
            # 检查关键字段
            key_fields = {
                'name': '计划名称',
                'content': '计划内容',
                'plan_objective': '计划目标',
                'description': '问题描述（遗留字段）',  # 可能已废弃
                'status': '计划状态',
            }
            
            found_fields = {row[0]: row for row in columns}
            
            for field_name, description in key_fields.items():
                if field_name in found_fields:
                    col_info = found_fields[field_name]
                    data_type = col_info[1]
                    max_length = col_info[2]
                    nullable = col_info[3]
                    
                    length_info = f"({max_length})" if max_length else ""
                    nullable_info = "可为空" if nullable == 'YES' else "不可为空"
                    
                    status = "✓" if field_name != 'description' else "⚠"
                    self.stdout.write(
                        f"{status} {field_name:20s} ({description:20s}) "
                        f"类型: {data_type}{length_info}, {nullable_info}"
                    )
                else:
                    if field_name == 'description':
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ {field_name:20s} ({description:20s}) - 不存在（已清理）"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ {field_name:20s} ({description:20s}) - 不存在"
                            )
                        )
            
            # 检查是否有description字段（遗留字段检查）
            has_description = 'description' in found_fields
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("字段治理状态检查")
            self.stdout.write("=" * 60)
            
            if has_description:
                self.stdout.write(self.style.WARNING(
                    "\n⚠ 发现遗留字段 'description'"
                ))
                self.stdout.write("  建议：如果已不再使用，可以通过迁移删除此字段")
                self.stdout.write("  迁移命令示例：")
                self.stdout.write("    python manage.py makemigrations plan_management")
                self.stdout.write("    python manage.py migrate plan_management")
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n✓ 未发现遗留字段 'description'"
                ))
                self.stdout.write("  字段治理状态正常")
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("所有字段列表")
            self.stdout.write("=" * 60)
            
            for col_info in columns:
                field_name = col_info[0]
                data_type = col_info[1]
                max_length = col_info[2]
                nullable = col_info[3]
                
                length_info = f"({max_length})" if max_length else ""
                nullable_info = "NULL" if nullable == 'YES' else "NOT NULL"
                
                self.stdout.write(
                    f"  {field_name:30s} {data_type:20s} {length_info:10s} {nullable_info}"
                )

