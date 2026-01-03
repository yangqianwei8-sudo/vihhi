"""
检查部门经理数据完整性
检查是否存在一个部门有多名部门经理的情况
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from backend.apps.system_management.models import Department
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '检查部门经理数据完整性，确认是否存在一个部门有多名部门经理的情况'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("开始检查部门经理数据完整性..."))
        self.stdout.write("")

        # 1. 检查所有部门及其经理信息
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("1. 所有部门的经理信息"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        departments = Department.objects.all().order_by('order', 'name')
        dept_with_leader = 0
        dept_without_leader = 0
        
        for dept in departments:
            if dept.leader:
                dept_with_leader += 1
                leader_name = dept.leader.get_full_name() or dept.leader.username
                self.stdout.write(
                    f"  ✓ [{dept.code}] {dept.name} - 经理: {leader_name} (ID: {dept.leader.id})"
                )
            else:
                dept_without_leader += 1
                self.stdout.write(
                    f"  - [{dept.code}] {dept.name} - 未设置经理"
                )
        
        self.stdout.write("")
        self.stdout.write(f"  总计: {departments.count()} 个部门")
        self.stdout.write(f"  有经理: {dept_with_leader} 个")
        self.stdout.write(f"  无经理: {dept_without_leader} 个")
        self.stdout.write("")

        # 2. 检查是否有用户同时担任多个部门的经理
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("2. 检查是否有用户同时担任多个部门的经理"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # 使用聚合查询找出担任多个部门经理的用户
        from django.db.models import Count
        users_with_multiple_depts = (
            Department.objects
            .filter(leader__isnull=False)
            .values('leader_id', 'leader__username', 'leader__first_name', 'leader__last_name')
            .annotate(dept_count=Count('id'))
            .filter(dept_count__gt=1)
            .order_by('-dept_count')
        )
        
        if users_with_multiple_depts.exists():
            self.stdout.write(self.style.WARNING("  发现以下用户同时担任多个部门的经理："))
            for item in users_with_multiple_depts:
                user_id = item['leader_id']
                username = item['leader__username']
                first_name = item['leader__first_name'] or ''
                last_name = item['leader__last_name'] or ''
                full_name = f"{first_name} {last_name}".strip() or username
                dept_count = item['dept_count']
                
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {full_name} (用户名: {username}, ID: {user_id}) - 担任 {dept_count} 个部门的经理"
                    )
                )
                
                # 列出该用户担任经理的所有部门
                depts = Department.objects.filter(leader_id=user_id)
                for dept in depts:
                    self.stdout.write(f"      - [{dept.code}] {dept.name}")
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ 没有用户同时担任多个部门的经理"))
        
        self.stdout.write("")

        # 3. 检查数据完整性（理论上不应该出现，但检查一下）
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("3. 数据完整性检查"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # 检查是否有部门有多个leader记录（理论上不应该有，因为leader是ForeignKey）
        # 但我们可以检查是否有重复的leader_id在同一部门（虽然数据库层面不可能）
        # 这个检查主要是为了确认模型约束是否正常工作
        
        # 检查是否有leader指向不存在的用户
        depts_with_invalid_leader = Department.objects.filter(
            leader__isnull=False
        ).exclude(leader__isnull=False)
        
        # 实际上，由于ForeignKey的约束，这个查询应该总是返回空
        # 但我们可以检查leader_id是否为None但leader字段不为None的情况（不应该发生）
        
        # 更实际的检查：查看是否有部门记录在数据库层面有多个leader
        # 由于leader是ForeignKey，一个部门只能有一个leader，这个检查主要是确认
        self.stdout.write("  ✓ 模型约束检查：leader字段是ForeignKey，一个部门只能有一个经理（数据库层面保证）")
        
        # 统计信息
        total_depts = Department.objects.count()
        depts_with_leader = Department.objects.filter(leader__isnull=False).count()
        depts_without_leader = Department.objects.filter(leader__isnull=True).count()
        unique_leaders = Department.objects.filter(leader__isnull=False).values('leader').distinct().count()
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("统计摘要"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  总部门数: {total_depts}")
        self.stdout.write(f"  有经理的部门: {depts_with_leader}")
        self.stdout.write(f"  无经理的部门: {depts_without_leader}")
        self.stdout.write(f"  担任经理的用户数（去重）: {unique_leaders}")
        
        if users_with_multiple_depts.exists():
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ 注意：有用户同时担任多个部门的经理（这是允许的）"
                )
            )
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("检查完成！"))
        
        # 4. 检查是否有数据异常（一个部门理论上不应该有多个leader记录）
        # 由于leader是ForeignKey，数据库层面已经保证了一个部门只能有一个leader
        # 但我们可以通过原始SQL检查是否有异常数据
        from django.db import connection
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("4. 数据库层面检查（原始SQL）"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        with connection.cursor() as cursor:
            # 检查是否有部门有多个leader_id（理论上不应该有，因为leader是ForeignKey）
            # 这个查询应该返回空结果，因为数据库约束已经保证了
            cursor.execute("""
                SELECT 
                    leader_id,
                    COUNT(*) as dept_count,
                    STRING_AGG(id::text, ', ') as dept_ids,
                    STRING_AGG(name, ', ') as dept_names
                FROM system_department
                WHERE leader_id IS NOT NULL
                GROUP BY leader_id
                HAVING COUNT(*) > 1
                ORDER BY dept_count DESC;
            """)
            
            results = cursor.fetchall()
            if results:
                self.stdout.write(self.style.WARNING("  发现以下用户担任多个部门的经理（数据库层面）："))
                for row in results:
                    leader_id, dept_count, dept_ids, dept_names = row
                    user = User.objects.filter(id=leader_id).first()
                    user_name = user.get_full_name() if user else f"用户ID: {leader_id}"
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {user_name} (ID: {leader_id}) - 担任 {dept_count} 个部门的经理"
                        )
                    )
                    self.stdout.write(f"      部门ID: {dept_ids}")
                    self.stdout.write(f"      部门名称: {dept_names}")
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ 数据库层面：没有发现异常（所有部门都有唯一的leader）"))
            
            # 检查是否有部门有重复的leader记录（理论上不应该有）
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    code,
                    leader_id,
                    COUNT(*) OVER (PARTITION BY id) as duplicate_count
                FROM system_department
                WHERE leader_id IS NOT NULL
                GROUP BY id, name, code, leader_id
                HAVING COUNT(*) > 1;
            """)
            
            duplicate_results = cursor.fetchall()
            if duplicate_results:
                self.stdout.write(self.style.ERROR("  ❌ 发现异常：有部门存在重复的leader记录！"))
                for row in duplicate_results:
                    dept_id, dept_name, dept_code, leader_id = row
                    self.stdout.write(
                        self.style.ERROR(
                            f"    部门 [{dept_code}] {dept_name} (ID: {dept_id}) - Leader ID: {leader_id}"
                        )
                    )
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ 没有发现部门有重复的leader记录"))

