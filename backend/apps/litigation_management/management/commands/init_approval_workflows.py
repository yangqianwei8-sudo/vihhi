"""
初始化诉讼管理审批流程模板
运行方式：python manage.py init_approval_workflows
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '初始化诉讼管理审批流程模板'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建已存在的流程模板',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.SUCCESS('开始初始化诉讼管理审批流程模板...'))

        # 获取LitigationCase和LitigationExpense的ContentType
        try:
            case_content_type = ContentType.objects.get(app_label='litigation_management', model='litigationcase')
            expense_content_type = ContentType.objects.get(app_label='litigation_management', model='litigationexpense')
        except ContentType.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'获取ContentType失败: {e}'))
            self.stdout.write(self.style.WARNING('请先运行数据库迁移: python manage.py migrate'))
            return

        workflows_to_create = [
            {
                'code': 'litigation_case_registration',
                'name': '案件登记审批',
                'description': '重大案件（金额超过50万或特定类型）的案件登记审批流程',
                'category': '诉讼管理',
                'content_types': [case_content_type],
                'nodes': [
                    {
                        'name': '法务经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'role',
                        'approver_role_name': '法务经理',  # 需要根据实际角色名称调整
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'can_transfer': True,
                        'timeout_hours': 24,
                    },
                    {
                        'name': '总经理审批',
                        'node_type': 'condition',
                        'sequence': 2,
                        'condition_expression': '{"field": "litigation_amount", "operator": ">=", "value": 500000}',  # 金额超过50万
                        'approver_type': 'role',
                        'approver_role_name': '总经理',  # 需要根据实际角色名称调整
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'timeout_hours': 48,
                    },
                ],
            },
            {
                'code': 'litigation_case_filing',
                'name': '立案申请审批',
                'description': '案件立案申请的审批流程',
                'category': '诉讼管理',
                'content_types': [case_content_type],
                'nodes': [
                    {
                        'name': '法务经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'role',
                        'approver_role_name': '法务经理',
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'timeout_hours': 24,
                    },
                ],
            },
            {
                'code': 'litigation_expense_reimbursement',
                'name': '费用报销审批',
                'description': '诉讼费用报销的审批流程',
                'category': '诉讼管理',
                'content_types': [expense_content_type],
                'nodes': [
                    {
                        'name': '法务经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'role',
                        'approver_role_name': '法务经理',
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'timeout_hours': 24,
                    },
                    {
                        'name': '财务经理审批',
                        'node_type': 'approval',
                        'sequence': 2,
                        'approver_type': 'role',
                        'approver_role_name': '财务经理',
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'timeout_hours': 24,
                    },
                ],
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for workflow_data in workflows_to_create:
            code = workflow_data['code']
            
            # 检查是否已存在
            existing = WorkflowTemplate.objects.filter(code=code).first()
            if existing and not force:
                self.stdout.write(self.style.WARNING(f'流程模板 {code} 已存在，跳过创建（使用 --force 强制重新创建）'))
                skipped_count += 1
                continue

            try:
                if existing and force:
                    # 删除现有节点
                    ApprovalNode.objects.filter(workflow=existing).delete()
                    # 更新流程模板
                    workflow = existing
                    for key, value in workflow_data.items():
                        if key not in ['nodes', 'content_types']:
                            setattr(workflow, key, value)
                    workflow.status = 'active'
                    workflow.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'更新流程模板: {code}'))
                else:
                    # 创建新流程模板
                    workflow = WorkflowTemplate.objects.create(
                        code=code,
                        name=workflow_data['name'],
                        description=workflow_data['description'],
                        category=workflow_data['category'],
                        status='active',
                        allow_withdraw=True,
                        allow_reject=True,
                        allow_transfer=True,
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'创建流程模板: {code}'))

                # 关联ContentType
                workflow.content_types.set(workflow_data['content_types'])

                # 创建审批节点
                for node_data in workflow_data['nodes']:
                    try:
                        from backend.apps.system_management.models import Role
                        
                        node = ApprovalNode.objects.create(
                            workflow=workflow,
                            name=node_data['name'],
                            node_type=node_data.get('node_type', 'approval'),
                            sequence=node_data['sequence'],
                            approver_type=node_data.get('approver_type', 'user'),
                            approval_mode=node_data.get('approval_mode', 'single'),
                            is_required=node_data.get('is_required', True),
                            can_reject=node_data.get('can_reject', True),
                            can_transfer=node_data.get('can_transfer', False),
                            timeout_hours=node_data.get('timeout_hours', 24),
                            condition_expression=node_data.get('condition_expression'),
                        )
                        
                        # 如果指定了角色，查找并关联角色
                        if node_data.get('approver_type') == 'role' and node_data.get('approver_role_name'):
                            try:
                                role = Role.objects.get(name=node_data['approver_role_name'])
                                node.approver_roles.add(role)
                                self.stdout.write(f'  ✓ 创建节点: {node_data["name"]} (关联角色: {role.name})')
                            except Role.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'  ⚠ 创建节点: {node_data["name"]} (角色 "{node_data["approver_role_name"]}" 不存在，请手动配置)'))
                        else:
                            self.stdout.write(f'  ✓ 创建节点: {node_data["name"]}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  创建节点失败 {node_data["name"]}: {e}'))
                        logger.error(f'创建节点失败 {node_data["name"]}: {e}', exc_info=True)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'创建流程模板失败 {code}: {e}'))
                logger.error(f'创建流程模板失败 {code}: {e}', exc_info=True)

        self.stdout.write(self.style.SUCCESS(f'\n完成！创建: {created_count}, 更新: {updated_count}, 跳过: {skipped_count}'))
        self.stdout.write(self.style.WARNING('\n注意：'))
        self.stdout.write(self.style.WARNING('1. 请检查并调整审批节点中的角色名称（approver_role_name），确保与实际系统中的角色名称一致。'))
        self.stdout.write(self.style.WARNING('2. 如果角色不存在，请先在系统管理中创建相应角色，然后手动关联到审批节点。'))
        self.stdout.write(self.style.WARNING('3. 条件节点的条件表达式需要根据实际业务逻辑调整。'))

