from collections import Counter

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = "Clean existing role assignments and sync default roles based on department and position"

    EXACT_ROLE_MAP = {
        "总经理": ["general_manager"],
        "系统管理员": ["system_admin"],
        "行政主管": ["admin_office"],
        "财务主管": ["finance_supervisor"],
        "商务部经理": ["business_team"],
        "商务经理": ["business_team"],
        "商务助理": ["business_assistant"],
        "技术部经理": ["technical_manager"],
        "造价部经理": ["cost_team"],
    }

    KEYWORD_ROLE_MAP = [
        ("商务经理", ["business_team"]),
        ("项目经理", ["project_manager"]),
        ("项目负责人", ["project_manager"]),
        ("专业负责人", ["professional_lead"]),
        ("专业工程师", ["professional_engineer"]),
        ("技术助理", ["technical_assistant"]),
        ("造价审核人", ["cost_team"]),
        ("审核人", ["cost_team"]),
        ("造价工程师", ["cost_engineer"]),
        ("造价师", ["cost_engineer"]),
    ]

    CONTROL_KEYWORD_ROLE_MAP = [
        ("项目负责人", ["client_project_lead"]),
        ("专业负责人", ["client_professional_lead"]),
        ("专业工程师", ["client_engineer"]),
        ("审核人", ["cost_team"]),
    ]

    DESIGN_KEYWORD_ROLE_MAP = [
        ("项目负责人", ["design_project_lead"]),
        ("专业负责人", ["design_professional_lead"]),
        ("专业工程师", ["design_engineer"]),
    ]

    CLIENT_KEYWORD_ROLE_MAP = [
        ("项目负责人", ["client_project_lead"]),
        ("专业负责人", ["client_professional_lead"]),
        ("专业工程师", ["client_engineer"]),
    ]

    def handle(self, *args, **options):
        User = get_user_model()
        role_lookup = {role.code: role for role in Role.objects.filter(is_active=True)}

        updated_counter = Counter()
        skipped_users = []

        for user in User.objects.all():
            target_codes = self._infer_roles(user)
            if not target_codes:
                skipped_users.append(user.username)
                continue

            missing_codes = [code for code in target_codes if code not in role_lookup]
            if missing_codes:
                self.stderr.write(
                    self.style.ERROR(
                        f"User {user.username} references undefined roles: {', '.join(missing_codes)}"
                    )
                )
                continue

            user.roles.set([role_lookup[code] for code in target_codes])
            updated_counter[tuple(sorted(target_codes))] += 1
            self.stdout.write(
                f"[OK] {user.username} -> {', '.join(target_codes)}"
            )

        self.stdout.write(self.style.SUCCESS("Role synchronization completed."))
        for role_combo, count in updated_counter.items():
            self.stdout.write(f"  - {count} user(s) assigned: {', '.join(role_combo)}")

        if skipped_users:
            self.stdout.write(self.style.WARNING(
                f"Skipped {len(skipped_users)} user(s) without matching position: {', '.join(skipped_users[:10])}"
                + (" ..." if len(skipped_users) > 10 else "")
            ))

    def _infer_roles(self, user):
        if user.is_superuser:
            return ["system_admin"]

        position = (user.position or "").strip()
        if not position:
            return []

        if position in self.EXACT_ROLE_MAP:
            return self.EXACT_ROLE_MAP[position]

        if user.user_type == "design_partner":
            return self._match_keyword(position, self.DESIGN_KEYWORD_ROLE_MAP)

        if user.user_type == "client_owner":
            return self._match_keyword(position, self.CLIENT_KEYWORD_ROLE_MAP)

        if user.user_type == "control_partner":
            codes = self._match_keyword(position, self.CONTROL_KEYWORD_ROLE_MAP)
            if codes:
                return codes
            return self._match_keyword(position, self.KEYWORD_ROLE_MAP)

        return self._match_keyword(position, self.KEYWORD_ROLE_MAP)

    @staticmethod
    def _match_keyword(position, keyword_map):
        for keyword, roles in keyword_map:
            if keyword in position:
                return roles
        return []

