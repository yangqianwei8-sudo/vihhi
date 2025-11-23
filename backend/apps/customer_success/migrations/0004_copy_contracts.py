from django.db import migrations


def forward(apps, schema_editor):
    Project = apps.get_model('project_center', 'Project')
    PaymentPlan = apps.get_model('project_center', 'PaymentPlan')
    BusinessContract = apps.get_model('customer_success', 'BusinessContract')
    BusinessPaymentPlan = apps.get_model('customer_success', 'BusinessPaymentPlan')

    contracts = {}
    for project in Project.objects.all():
        contract, _ = BusinessContract.objects.get_or_create(
            project_id=project.id,
            defaults={
                'contract_number': getattr(project, 'contract_number', ''),
                'amount': getattr(project, 'contract_amount', None),
                'contract_date': getattr(project, 'contract_date', None),
                'attachment': getattr(project, 'contract_file', ''),
                'notes': '',
            }
        )
        # 如果合同已存在但还没有值，则补充一次
        changed = False
        if not contract.contract_number and getattr(project, 'contract_number', ''):
            contract.contract_number = project.contract_number
            changed = True
        if contract.amount in (None, 0) and getattr(project, 'contract_amount', None):
            contract.amount = project.contract_amount
            changed = True
        if not contract.contract_date and getattr(project, 'contract_date', None):
            contract.contract_date = project.contract_date
            changed = True
        if not contract.attachment and getattr(project, 'contract_file', None):
            contract.attachment = project.contract_file
            changed = True
        if changed:
            contract.save(update_fields=['contract_number', 'amount', 'contract_date', 'attachment'])
        contracts[project.id] = contract

    plan_objs = []
    for plan in PaymentPlan.objects.all():
        contract = contracts.get(plan.project_id)
        if not contract:
            contract = BusinessContract.objects.create(project_id=plan.project_id)
            contracts[plan.project_id] = contract
        plan_objs.append(BusinessPaymentPlan(
            contract=contract,
            phase_name=plan.phase_name,
            phase_description=plan.phase_description,
            planned_amount=plan.planned_amount,
            planned_date=plan.planned_date,
            actual_amount=plan.actual_amount,
            actual_date=plan.actual_date,
            status=plan.status,
            trigger_condition=plan.trigger_condition,
            condition_detail=plan.condition_detail,
            notes=plan.notes,
        ))
    if plan_objs:
        BusinessPaymentPlan.objects.bulk_create(plan_objs, batch_size=500)


def backward(apps, schema_editor):
    BusinessContract = apps.get_model('customer_success', 'BusinessContract')
    BusinessPaymentPlan = apps.get_model('customer_success', 'BusinessPaymentPlan')
    BusinessPaymentPlan.objects.all().delete()
    BusinessContract.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('project_center', '0012_project_flow_deadline_project_flow_payload_and_more'),
        ('customer_success', '0003_businesscontract_businesspaymentplan'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
