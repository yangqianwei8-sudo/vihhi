from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from backend.apps.system_management.models import Department


class Command(BaseCommand):
    help = "Seed baseline departments, positions, and user accounts"

    DEPARTMENT_STRUCTURE = [
        {
            "name": "综合办",
            "code": "GENERAL",
            "order": 10,
            "children": [],
        },
        {
            "name": "商务部",
            "code": "BUSINESS",
            "order": 20,
            "children": [],
        },
        {
            "name": "技术部",
            "code": "TECH",
            "order": 30,
            "children": [],
        },
        {
            "name": "造价部",
            "code": "COST",
            "order": 40,
            "children": [],
        },
        {
            "name": "合作技术",
            "code": "EXTERNAL_TECH",
            "order": 50,
            "children": [],
        },
        {
            "name": "合作造价",
            "code": "EXTERNAL_COST",
            "order": 60,
            "children": [],
        },
    ]

    USERS = [
        {
            "username": "admin",
            "password": "Admin@123456",
            "first_name": "系统",
            "last_name": "管理员",
            "email": "admin@vihhi.com",
            "position": "系统管理员",
            "department": "GENERAL",
            "is_superuser": True,
            "is_staff": True,
        },
        {
            "username": "ceo",
            "password": "Vihhi@123",
            "first_name": "维海",
            "last_name": "总经理",
            "email": "ceo@vihhi.com",
            "position": "总经理",
            "department": "GENERAL",
        },
        {
            "username": "admin_manager",
            "password": "Vihhi@123",
            "first_name": "综合办",
            "last_name": "行政主管",
            "email": "admin.manager@vihhi.com",
            "position": "行政主管",
            "department": "GENERAL",
        },
        {
            "username": "finance_manager",
            "password": "Vihhi@123",
            "first_name": "综合办",
            "last_name": "财务主管",
            "email": "finance.manager@vihhi.com",
            "position": "财务主管",
            "department": "GENERAL",
        },
        {
            "username": "business_head",
            "password": "Vihhi@123",
            "first_name": "商务部",
            "last_name": "经理",
            "email": "business.head@vihhi.com",
            "position": "商务部经理",
            "department": "BUSINESS",
        },
        {
            "username": "tx",
            "password": "123456",
            "first_name": "商务经理",
            "last_name": "唐晓",
            "email": "tx@vihhi.com",
            "position": "商务经理",
            "department": "BUSINESS",
        },
        {
            "username": "business_assistant",
            "password": "Vihhi@123",
            "first_name": "商务部",
            "last_name": "助理",
            "email": "business.assistant@vihhi.com",
            "position": "商务助理",
            "department": "BUSINESS",
        },
        {
            "username": "tech_head",
            "password": "Vihhi@123",
            "first_name": "技术部",
            "last_name": "经理",
            "email": "tech.head@vihhi.com",
            "position": "技术部经理",
            "department": "TECH",
        },
        {
            "username": "project_lead",
            "password": "Vihhi@123",
            "first_name": "技术部",
            "last_name": "项目负责人",
            "email": "project.lead@vihhi.com",
            "position": "项目负责人",
            "department": "TECH",
        },
        {
            "username": "yx",
            "password": "123456",
            "first_name": "专业工程师",
            "last_name": "杨欣",
            "email": "yx@vihhi.com",
            "position": "专业工程师",
            "department": "TECH",
        },
        {
            "username": "tech_assistant",
            "password": "Vihhi@123",
            "first_name": "技术部",
            "last_name": "技术助理",
            "email": "tech.assistant@vihhi.com",
            "position": "技术助理",
            "department": "TECH",
        },
        {
            "username": "cost_head",
            "password": "Vihhi@123",
            "first_name": "造价部",
            "last_name": "经理",
            "email": "cost.head@vihhi.com",
            "position": "造价部经理",
            "department": "COST",
        },
        {
            "username": "cost_checker_civil",
            "password": "Vihhi@123",
            "first_name": "造价部",
            "last_name": "土建审核",
            "email": "cost.checker.civil@vihhi.com",
            "position": "土建造价审核人",
            "department": "COST",
        },
        {
            "username": "cost_checker_mechanical",
            "password": "Vihhi@123",
            "first_name": "造价部",
            "last_name": "安装审核",
            "email": "cost.checker.mechanical@vihhi.com",
            "position": "安装造价审核人",
            "department": "COST",
        },
        {
            "username": "cost_engineer_civil",
            "password": "Vihhi@123",
            "first_name": "造价部",
            "last_name": "土建造价师",
            "email": "cost.engineer.civil@vihhi.com",
            "position": "土建造价师",
            "department": "COST",
        },
        {
            "username": "cost_engineer_mechanical",
            "password": "Vihhi@123",
            "first_name": "造价部",
            "last_name": "安装造价师",
            "email": "cost.engineer.mechanical@vihhi.com",
            "position": "安装造价师",
            "department": "COST",
        },
        {
            "username": "external_lead",
            "password": "Vihhi@123",
            "first_name": "合作技术",
            "last_name": "负责人",
            "email": "external.lead@vihhi.com",
            "position": "专业负责人",
            "department": "EXTERNAL_TECH",
            "user_type": "external",
        },
        {
            "username": "external_engineer",
            "password": "Vihhi@123",
            "first_name": "合作技术",
            "last_name": "工程师",
            "email": "external.engineer@vihhi.com",
            "position": "专业工程师",
            "department": "EXTERNAL_TECH",
            "user_type": "external",
        },
        {
            "username": "external_cost_engineer",
            "password": "Vihhi@123",
            "first_name": "合作造价",
            "last_name": "工程师",
            "email": "external.cost.engineer@vihhi.com",
            "position": "造价工程师",
            "department": "EXTERNAL_COST",
            "user_type": "external",
        },
    ]

    DEPARTMENT_LEADERS = {
        "GENERAL": "ceo",
        "BUSINESS": "business_head",
        "TECH": "tech_head",
        "COST": "cost_head",
        "EXTERNAL_TECH": "external_lead",
        "EXTERNAL_COST": "external_cost_engineer",
    }

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding organization structure..."))

        dept_map = self._create_departments()
        user_map = self._create_users(dept_map)
        self._assign_department_leaders(dept_map, user_map)

        self.stdout.write(self.style.SUCCESS("Organization structure seeding completed."))

    def _create_departments(self):
        dept_map = {}

        def create_dept(entry, parent=None):
            department, created = Department.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry["name"],
                    "parent": parent,
                    "order": entry.get("order", 0),
                    "is_active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  - {action} department: {department.name}")
            dept_map[entry["code"]] = department

            for child in entry.get("children", []):
                create_dept(child, department)

        for entry in self.DEPARTMENT_STRUCTURE:
            create_dept(entry)

        return dept_map

    def _create_users(self, dept_map):
        User = get_user_model()
        user_map = {}

        for item in self.USERS:
            dept = dept_map.get(item["department"])
            defaults = {
                "first_name": item.get("first_name", ""),
                "last_name": item.get("last_name", ""),
                "email": item.get("email", ""),
                "department": dept,
                "position": item.get("position", ""),
                "user_type": item.get("user_type", "internal"),
                "is_staff": item.get("is_staff", False),
                "is_active": True,
            }
            user, created = User.objects.update_or_create(
                username=item["username"],
                defaults=defaults,
            )
            if created or item.get("reset_password", True):
                user.set_password(item["password"])

            if item.get("is_superuser"):
                user.is_superuser = True
                user.is_staff = True

            user.save()
            user_map[item["username"]] = user

            action = "Created" if created else "Updated"
            self.stdout.write(f"  - {action} user: {user.username} ({user.position})")

        return user_map

    def _assign_department_leaders(self, dept_map, user_map):
        for dept_code, username in self.DEPARTMENT_LEADERS.items():
            dept = dept_map.get(dept_code)
            user = user_map.get(username)
            if dept and user:
                dept.leader = user
                dept.save(update_fields=["leader"])
                self.stdout.write(f"  - Set leader for {dept.name}: {user.get_full_name() or user.username}")

