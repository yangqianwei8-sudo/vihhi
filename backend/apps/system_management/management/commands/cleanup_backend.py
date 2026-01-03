"""
清理后台数据的管理命令
1. 从部门中删除咨询单位、设计单位、委托单位
2. 设置田霞为商务部经理，袁鑫为技术部经理
3. 增加专业配置信息
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from backend.apps.system_management.models import Department, Role
from backend.apps.production_management.models import ServiceType, ServiceProfession

User = get_user_model()


class Command(BaseCommand):
    help = "清理后台：移除外部单位部门，设置部门经理，配置专业信息"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("开始清理后台..."))

        # 1. 删除外部单位部门（咨询单位、设计单位、委托单位、过控单位）
        self._delete_external_unit_departments()

        # 2. 从部门中删除咨询单位、设计单位、委托单位的用户
        self._remove_external_units_from_departments()

        # 3. 设置田霞为商务部经理，袁鑫为技术部经理
        self._set_department_managers()

        # 4. 确保专业配置信息存在
        self._ensure_profession_config()

        self.stdout.write(self.style.SUCCESS("后台清理完成！"))

    def _delete_external_unit_departments(self):
        """删除外部单位部门（咨询单位、设计单位、委托单位、过控单位）"""
        self.stdout.write("正在删除外部单位部门...")

        # 外部单位部门代码列表
        external_department_codes = [
            'dept_internal_root',  # 咨询单位
            'dept_design_root',    # 设计单位
            'dept_client_root',    # 委托单位
            'dept_control_root',   # 过控单位
        ]

        deleted_count = 0
        for code in external_department_codes:
            try:
                dept = Department.objects.get(code=code)
                # 先移除该部门的所有用户
                members_count = dept.members.count()
                if members_count > 0:
                    dept.members.update(department=None)
                    self.stdout.write(f"  - 移除了 {members_count} 个用户从部门 {dept.name}")
                
                # 删除部门
                dept_name = dept.name
                dept.delete()
                deleted_count += 1
                self.stdout.write(f"  - 删除了部门：{dept_name} (code: {code})")
            except Department.DoesNotExist:
                self.stdout.write(f"  - 部门不存在：{code}")
        
        self.stdout.write(self.style.SUCCESS(f"  共删除 {deleted_count} 个外部单位部门"))

    def _remove_external_units_from_departments(self):
        """从部门中删除咨询单位、设计单位、委托单位的用户"""
        self.stdout.write("正在从部门中移除外部单位用户...")

        # 查询所有用户类型为外部单位的用户
        external_users = User.objects.filter(
            user_type__in=['client_owner', 'design_partner', 'control_partner']
        )

        updated_count = 0
        for user in external_users:
            if user.department:
                old_dept = user.department.name
                user.department = None
                user.save(update_fields=['department'])
                updated_count += 1
                self.stdout.write(f"  - 移除了 {user.username} ({user.get_full_name()}) 从部门 {old_dept}")

        self.stdout.write(self.style.SUCCESS(f"  共移除 {updated_count} 个外部单位用户从部门"))

    def _set_department_managers(self):
        """设置田霞为商务部经理，袁鑫为技术部经理"""
        self.stdout.write("正在设置部门经理...")

        # 获取或创建部门（使用正确的部门代码）
        business_dept = Department.objects.filter(
            Q(code='BUSINESS') | Q(code='dept_consulting_business') | Q(name='商务部')
        ).first()
        
        if not business_dept:
            business_dept, _ = Department.objects.get_or_create(
                code='dept_consulting_business',
                defaults={
                    'name': '商务部',
                    'description': '商务部门，负责商务洽谈和客户管理',
                    'order': 20,
                    'is_active': True,
                }
            )
        
        tech_dept = Department.objects.filter(
            Q(code='TECH') | Q(code='dept_consulting_tech') | Q(name='技术部')
        ).first()
        
        if not tech_dept:
            tech_dept, _ = Department.objects.get_or_create(
                code='dept_consulting_tech',
                defaults={
                    'name': '技术部',
                    'description': '技术部门，负责技术研发和项目执行',
                    'order': 30,
                    'is_active': True,
                }
            )

        # 查找田霞（可能使用手机号作为用户名）
        tianxia = User.objects.filter(
            Q(username='tianxia') | Q(username='13666287899') | 
            Q(first_name='田', last_name='霞') | Q(phone='13666287899')
        ).first()
        
        if not tianxia:
            # 创建新用户
            tianxia = User.objects.create_user(
                username='tianxia',
                first_name='田',
                last_name='霞',
                email='tianxia@vihhi.com',
                phone='13666287899',
                position='商务部经理',
                department=business_dept,
                user_type='internal',
                is_active=True,
                password='123456',
            )
            self.stdout.write("  - 创建了用户：田霞")
        else:
            # 更新信息
            tianxia.first_name = '田'
            tianxia.last_name = '霞'
            tianxia.position = '商务部经理'
            tianxia.department = business_dept
            tianxia.user_type = 'internal'
            tianxia.is_active = True
            if not tianxia.phone:
                tianxia.phone = '13666287899'
            self.stdout.write(f"  - 更新了用户：田霞 (username: {tianxia.username})")

        # 设置田霞为商务部经理（部门负责人）
        business_dept.leader = tianxia
        business_dept.save()

        # 给田霞添加商务部经理角色
        business_manager_role, _ = Role.objects.get_or_create(
            code='business_manager',
            defaults={
                'name': '商务部经理',
                'description': '商务部经理角色',
            }
        )
        tianxia.roles.add(business_manager_role)

        tianxia.save()
        self.stdout.write(self.style.SUCCESS(f"  ✓ 设置田霞为商务部经理"))

        # 查找袁鑫（可能使用不同用户名）
        yuanxin = User.objects.filter(
            Q(username='yuanxin') | Q(username='yx') |
            Q(first_name='袁', last_name='鑫')
        ).first()
        
        if not yuanxin:
            # 创建新用户
            yuanxin = User.objects.create_user(
                username='yuanxin',
                first_name='袁',
                last_name='鑫',
                email='yuanxin@vihhi.com',
                position='技术部经理',
                department=tech_dept,
                user_type='internal',
                is_active=True,
                password='123456',
            )
            self.stdout.write("  - 创建了用户：袁鑫")
        else:
            # 更新信息
            yuanxin.first_name = '袁'
            yuanxin.last_name = '鑫'
            yuanxin.position = '技术部经理'
            yuanxin.department = tech_dept
            yuanxin.user_type = 'internal'
            yuanxin.is_active = True
            self.stdout.write(f"  - 更新了用户：袁鑫 (username: {yuanxin.username})")

        # 设置袁鑫为技术部经理（部门负责人）
        tech_dept.leader = yuanxin
        tech_dept.save()

        # 给袁鑫添加技术部经理角色
        technical_manager_role, _ = Role.objects.get_or_create(
            code='technical_manager',
            defaults={
                'name': '技术部经理',
                'description': '技术部经理角色',
            }
        )
        yuanxin.roles.add(technical_manager_role)

        yuanxin.save()
        self.stdout.write(self.style.SUCCESS(f"  ✓ 设置袁鑫为技术部经理"))

    def _ensure_profession_config(self):
        """确保专业配置信息存在"""
        self.stdout.write("正在配置专业信息...")

        # 专业配置数据
        PROFESSION_CONFIG = [
            {
                'service_type_code': 'result_optimization',
                'service_type_name': '结果优化',
                'professions': [
                    {'code': 'structure', 'name': '结构', 'order': 1},
                    {'code': 'construction', 'name': '构造', 'order': 2},
                    {'code': 'basement_reduce_area', 'name': '地库减面积', 'order': 3},
                    {'code': 'basement_add_parking', 'name': '地库加车位', 'order': 4},
                    {'code': 'parking_efficiency', 'name': '停车效率', 'order': 5},
                    {'code': 'energy_saving', 'name': '节能', 'order': 6},
                    {'code': 'doors_windows_railings', 'name': '门窗栏杆', 'order': 7},
                    {'code': 'curtain_wall', 'name': '幕墙', 'order': 8},
                    {'code': 'landscape', 'name': '总坪景观', 'order': 9},
                    {'code': 'electrical', 'name': '电气', 'order': 10},
                    {'code': 'water_supply_drainage', 'name': '给排水', 'order': 11},
                    {'code': 'hvac', 'name': '暖通', 'order': 12},
                    {'code': 'municipal_road', 'name': '市政道路', 'order': 13},
                ]
            },
            {
                'service_type_code': 'process_optimization',
                'service_type_name': '过程优化',
                'professions': [
                    {'code': 'structure', 'name': '结构', 'order': 1},
                    {'code': 'parking_efficiency', 'name': '停车效率', 'order': 2},
                ]
            },
            {
                'service_type_code': 'detailed_review',
                'service_type_name': '精细化审图',
                'professions': [
                    {'code': 'architecture', 'name': '建筑', 'order': 1},
                    {'code': 'structure', 'name': '结构', 'order': 2},
                    {'code': 'electrical', 'name': '电气', 'order': 3},
                    {'code': 'water_supply_drainage', 'name': '给排水', 'order': 4},
                    {'code': 'hvac', 'name': '暖通', 'order': 5},
                ]
            },
            {
                'service_type_code': 'full_process_consulting',
                'service_type_name': '全过程咨询',
                'professions': [
                    {'code': 'architecture', 'name': '建筑', 'order': 1},
                    {'code': 'structure', 'name': '结构', 'order': 2},
                    {'code': 'electrical', 'name': '电气', 'order': 3},
                    {'code': 'water_supply_drainage', 'name': '给排水', 'order': 4},
                    {'code': 'hvac', 'name': '暖通', 'order': 5},
                ]
            },
        ]

        created_types = 0
        created_professions = 0

        for config in PROFESSION_CONFIG:
            service_type, created = ServiceType.objects.update_or_create(
                code=config['service_type_code'],
                defaults={
                    'name': config['service_type_name'],
                    'order': PROFESSION_CONFIG.index(config) + 1,
                }
            )
            if created:
                created_types += 1
                self.stdout.write(f"  - 创建了服务类型：{service_type.name}")

            # 获取要保留的专业ID列表
            keep_ids = []
            for prof_config in config['professions']:
                profession, prof_created = ServiceProfession.objects.update_or_create(
                    service_type=service_type,
                    code=prof_config['code'],
                    defaults={
                        'name': prof_config['name'],
                        'order': prof_config['order'],
                    }
                )
                keep_ids.append(profession.id)
                if prof_created:
                    created_professions += 1
                    self.stdout.write(f"    - 创建了专业：{profession.name}")

            # 删除不在配置中的专业
            removed = ServiceProfession.objects.filter(
                service_type=service_type
            ).exclude(id__in=keep_ids)
            removed_count = removed.count()
            if removed_count > 0:
                removed.delete()
                self.stdout.write(f"    - 移除了 {removed_count} 个不在配置中的专业")

        self.stdout.write(self.style.SUCCESS(
            f"  专业配置完成：新增 {created_types} 个服务类型，{created_professions} 个专业"
        ))

