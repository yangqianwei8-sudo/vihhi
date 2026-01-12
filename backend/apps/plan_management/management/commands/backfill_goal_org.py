"""
回填 StrategicGoal 的 company 和 org_department 字段（历史数据）
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.plan_management.models import StrategicGoal
from backend.apps.org.models import Company, Department

User = get_user_model()


class Command(BaseCommand):
    help = "Backfill StrategicGoal.company/org_department for historical data"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="只显示将要更新的数据，不实际更新")
        parser.add_argument("--company-code", default="CD", help="默认公司代码（如 CD/CQ/XA）")
        parser.add_argument("--dept-name", default="总部", help="默认部门名称")

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        company_code = opts["company_code"]
        dept_name = opts["dept_name"]

        # 获取默认公司和部门
        try:
            default_company = Company.objects.get(code=company_code)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"默认公司代码 '{company_code}' 不存在"))
            # 尝试获取第一个活跃公司
            default_company = Company.objects.filter(is_active=True).first()
            if not default_company:
                self.stdout.write(self.style.ERROR("没有找到任何活跃的公司"))
                return
            self.stdout.write(self.style.WARNING(f"使用第一个活跃公司: {default_company.name} ({default_company.code})"))

        try:
            default_dept = Department.objects.get(company=default_company, name=dept_name)
        except Department.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"默认部门 '{dept_name}' 不存在，将创建"))
            if not dry_run:
                default_dept = Department.objects.create(
                    company=default_company,
                    name=dept_name
                )
            else:
                default_dept = None

        # 查找需要回填的目标
        qs = StrategicGoal.objects.filter(company__isnull=True).select_related(
            "created_by", "responsible_person"
        )
        total = qs.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("✓ 没有需要回填的目标（所有目标都已设置公司）"))
            return

        self.stdout.write(f"找到 {total} 个需要回填的目标")
        updated = 0
        skipped = 0

        for g in qs:
            company = None
            dept = None

            # 策略1: 从 created_by.profile 获取
            if g.created_by:
                try:
                    if hasattr(g.created_by, "profile") and g.created_by.profile:
                        if g.created_by.profile.company_id:
                            company = g.created_by.profile.company
                            # 尝试获取部门
                            if hasattr(g.created_by.profile, "department") and g.created_by.profile.department:
                                dept = g.created_by.profile.department
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  目标 {g.id} 获取 created_by.profile 失败: {e}"))

            # 策略2: 从 responsible_person.profile 获取
            if not company and g.responsible_person:
                try:
                    if hasattr(g.responsible_person, "profile") and g.responsible_person.profile:
                        if g.responsible_person.profile.company_id:
                            company = g.responsible_person.profile.company
                            if not dept and hasattr(g.responsible_person.profile, "department") and g.responsible_person.profile.department:
                                dept = g.responsible_person.profile.department
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  目标 {g.id} 获取 responsible_person.profile 失败: {e}"))

            # 策略3: 使用默认值
            if not company:
                company = default_company
            if not dept:
                dept = default_dept

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] 目标 {g.id} ({g.goal_number}): "
                    f"company={company.name if company else None}, "
                    f"dept={dept.name if dept else None}"
                )
            else:
                g.company = company
                g.org_department = dept
                g.save(update_fields=["company", "org_department"])
                self.stdout.write(
                    f"  ✓ 目标 {g.id} ({g.goal_number}): "
                    f"company={company.name}, dept={dept.name if dept else 'None'}"
                )
            
            updated += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n[DRY RUN] 将更新 {updated} 个目标"))
            transaction.set_rollback(True)
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ 完成！共处理 {total} 个目标，更新 {updated} 个"
            ))

