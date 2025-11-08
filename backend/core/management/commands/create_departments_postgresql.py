from django.core.management.base import BaseCommand
from django.db import connection
from backend.apps.system_management.models import Department

class Command(BaseCommand):
    help = '使用 PostgreSQL 创建部门数据：总经理办公室、造价部、技术部、商务部'
    
    def handle(self, *args, **options):
        # 检查数据库类型
        db_engine = connection.settings_dict['ENGINE']
        self.stdout.write(f'当前数据库引擎：{db_engine}')
        
        if 'postgresql' not in db_engine.lower() and 'postgis' not in db_engine.lower():
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  当前数据库不是 PostgreSQL！\n'
                    '请设置 DATABASE_URL 环境变量，例如：\n'
                    'export DATABASE_URL="postgres://postgres:password@localhost:5432/weihai_tech"\n'
                    '或使用 docker-compose 启动 PostgreSQL 服务'
                )
            )
            return
        
        self.stdout.write('开始使用 PostgreSQL 创建部门数据...')
        
        # 使用原生 SQL 插入数据
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'system_department'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(
                    self.style.ERROR('❌ 表 system_department 不存在！请先运行数据库迁移：')
                )
                self.stdout.write('   python manage.py migrate')
                return
            
            # 插入部门数据（使用 ON CONFLICT 避免重复）
            sql = """
                INSERT INTO system_department (name, code, description, "order", is_active, created_time)
                VALUES 
                    (%s, %s, %s, %s, %s, NOW()),
                    (%s, %s, %s, %s, %s, NOW()),
                    (%s, %s, %s, %s, %s, NOW()),
                    (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (code) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    "order" = EXCLUDED."order",
                    is_active = EXCLUDED.is_active,
                    created_time = EXCLUDED.created_time;
            """
            
            departments = [
                ('总经理办公室', 'GM_OFFICE', '总经理办公室，负责公司整体战略规划和管理决策', 1, True),
                ('造价部', 'COST', '造价部门，负责项目造价审核、成本控制等工作', 2, True),
                ('技术部', 'TECH', '技术部门，负责技术研发和项目执行', 3, True),
                ('商务部', 'BUSINESS', '商务部门，负责商务洽谈和客户管理', 4, True),
            ]
            
            # 展开参数
            params = []
            for dept in departments:
                params.extend(dept)
            
            try:
                cursor.execute(sql, params)
                connection.commit()
                
                # 查询创建的部门
                cursor.execute("""
                    SELECT id, code, name, description, "order", is_active, created_time
                    FROM system_department
                    WHERE code IN ('GM_OFFICE', 'COST', 'TECH', 'BUSINESS')
                    ORDER BY "order", id;
                """)
                
                results = cursor.fetchall()
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✓ 部门数据创建成功！'))
                self.stdout.write('')
                self.stdout.write('=' * 70)
                self.stdout.write('创建的部门列表：')
                self.stdout.write('=' * 70)
                
                for row in results:
                    dept_id, code, name, desc, order, is_active, created = row
                    status = '✓' if is_active else '✗'
                    self.stdout.write(
                        f'{status} [{code}] {name} (ID: {dept_id}, 排序: {order})'
                    )
                    self.stdout.write(f'   描述: {desc}')
                    self.stdout.write(f'   创建时间: {created}')
                    self.stdout.write('-' * 70)
                
                self.stdout.write('')
                self.stdout.write(f'总计：{len(results)} 个部门')
                
            except Exception as e:
                connection.rollback()
                self.stdout.write(
                    self.style.ERROR(f'❌ 创建部门数据时出错：{str(e)}')
                )
                raise

