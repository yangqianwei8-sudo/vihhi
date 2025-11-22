from django.db import migrations


def _detect_category(code: str, name: str) -> str:
    code_lower = (code or "").lower()
    name_lower = (name or "").lower()
    if any(keyword in code_lower for keyword in ["struct", "frame", "steel"]) or any(
        keyword in name_lower for keyword in ["结构", "钢"]
    ):
        return "structure"
    if any(keyword in code_lower for keyword in ["arch", "facade"]) or any(
        keyword in name_lower for keyword in ["建筑", "立面"]
    ):
        return "architecture"
    if any(keyword in code_lower for keyword in ["mep", "hvac", "water", "elec", "elect"]) or any(
        keyword in name_lower for keyword in ["机电", "暖通", "给排水", "电"]
    ):
        return "mep"
    if any(keyword in code_lower for keyword in ["landscape", "park"]) or "景观" in name_lower:
        return "landscape"
    return "other"


def seed_professional_categories(apps, schema_editor):
    ProfessionalCategory = apps.get_model("resource_standard", "ProfessionalCategory")
    ServiceProfession = apps.get_model("project_center", "ServiceProfession")

    existing_codes = set(
        ProfessionalCategory.objects.values_list("code", flat=True)
    )

    categories_to_create = []
    for profession in ServiceProfession.objects.select_related("service_type").all():
        if profession.code in existing_codes:
            continue
        service_type_code = (
            profession.service_type.code if profession.service_type_id else None
        )
        categories_to_create.append(
            ProfessionalCategory(
                code=profession.code,
                name=profession.name,
                category=_detect_category(profession.code, profession.name),
                order=profession.order,
                service_types=[service_type_code] if service_type_code else [],
                workflow_template="__auto_seeded__",
            )
        )

    if categories_to_create:
        ProfessionalCategory.objects.bulk_create(categories_to_create, ignore_conflicts=True)


def unseed_professional_categories(apps, schema_editor):
    ProfessionalCategory = apps.get_model("resource_standard", "ProfessionalCategory")
    ProfessionalCategory.objects.filter(workflow_template="__auto_seeded__").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("project_center", "0011_projectdrawingreview_projectdrawingsubmission_and_more"),
        ("resource_standard", "0004_systemparameter_professionalcategory"),
    ]

    operations = [
        migrations.RunPython(
            seed_professional_categories,
            unseed_professional_categories,
        ),
    ]

