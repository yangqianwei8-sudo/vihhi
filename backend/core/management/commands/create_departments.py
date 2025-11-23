from django.core.management.base import BaseCommand
from backend.apps.system_management.models import Department

class Command(BaseCommand):
    help = '创建部门数据：总经理办公室、造价部、技术部、商务部'
    
    def handle(self, *args, **options):
        self.stdout.write('开始创建部门数据...')
        
        # 定义部门数据
        departments = [
            {
                'name': '总经理办公室',
                'code': 'GM_OFFICE',
                'description': '总经理办公室，负责公司整体战略规划和管理决策',
                'order': 1
            },
            {
                'name': '造价部',
                'code': 'COST',
                'description': '造价部门，负责项目造价审核、成本控制等工作',
                'order': 2
            },
            {
                'name': '技术部',
                'code': 'TECH',
                'description': '技术部门，负责技术研发和项目执行',
                'order': 3
            },
            {
                'name': '商务部',
                'code': 'BUSINESS',
                'description': '商务部门，负责商务洽谈和客户管理',
                'order': 4
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'description': dept_data['description'],
                    'order': dept_data['order'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 创建部门：{dept.name} ({dept.code})')
                )
            else:
                existing_count += 1
                # 更新现有部门信息（如果需要）
                dept.name = dept_data['name']
                dept.description = dept_data['description']
                dept.order = dept_data['order']
                dept.is_active = True
                dept.save()
                self.stdout.write(
                    self.style.WARNING(f'→ 部门已存在，已更新：{dept.name} ({dept.code})')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'部门创建完成！\n'
                f'  新建：{created_count} 个\n'
                f'  已存在：{existing_count} 个\n'
                f'  总计：{created_count + existing_count} 个'
            )
        )
        
        # 显示所有部门列表
        self.stdout.write('\n当前所有部门列表：')
        all_depts = Department.objects.all().order_by('order', 'id')
        for dept in all_depts:
            status = '✓' if dept.is_active else '✗'
            leader_info = f' - 负责人：{dept.leader.get_full_name()}' if dept.leader else ''
            self.stdout.write(
                f'  {status} [{dept.code}] {dept.name}{leader_info}'
            )

