from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from backend.apps.org.models import Company, Department
from backend.apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = "Initialize default Company/Department data and bind demo users (idempotent)."

    def handle(self, *args, **options):
        # 1) Company
        company, company_created = Company.objects.get_or_create(
            code="VIHHI",
            defaults={"name": "维海科技", "is_active": True}
        )

        # 2) Departments (minimal set)
        hq, hq_created = Department.objects.get_or_create(
            company=company,
            name="总部",
            parent=None,
            defaults={"is_active": True}
        )

        # 你也可以按需加更多一级部门（可删减）
        dept_names = ["生产部", "财务部", "行政部", "市场部", "风控部"]
        created_depts = 0
        for name in dept_names:
            _, created = Department.objects.get_or_create(
                company=company,
                name=name,
                parent=None,
                defaults={"is_active": True}
            )
            if created:
                created_depts += 1

        # 3) Bind demo users
        User = get_user_model()

        # 先确保"生产部"存在
        prod_dept, _ = Department.objects.get_or_create(
            company=company,
            name="生产部",
            parent=None,
            defaults={"is_active": True}
        )

        # ✅ 按真实存在的用户名绑定
        bind_map = {
            "admin": hq,               # admin -> 总部
            "18113091627": prod_dept,  # 示例：手机号账号 -> 生产部（可改）
        }

        bound = 0
        missing = []

        for username, dept in bind_map.items():
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                missing.append(username)
                continue

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.company = company
            profile.department = dept
            profile.is_enabled = True
            profile.save(update_fields=["company", "department", "is_enabled", "updated_at"])
            bound += 1

        self.stdout.write(self.style.SUCCESS(
            "Init org data done."
        ))
        self.stdout.write(
            f"company={'created' if company_created else 'exists'}: {company.name}({company.code})"
        )
        self.stdout.write(
            f"department={'created' if hq_created else 'exists'}: {hq.name}"
        )
        self.stdout.write(
            f"extra_departments_created={created_depts}"
        )
        self.stdout.write(
            f"bound_profiles={bound}, missing_users={missing}"
        )

