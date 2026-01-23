"""
初始化计划管理审批流程模板
运行方式：python manage.py init_plan_approval_workflows
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '初始化计划管理审批流程模板'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建已存在的流程模板',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.SUCCESS('开始初始化计划管理审批流程模板...'))

        # 获取Plan的ContentType
        try:
            plan_content_type = ContentType.objects.get(app_label='plan_management', model='plan')
        except ContentType.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'获取ContentType失败: {e}'))
            self.stdout.write(self.style.WARNING('请先运行数据库迁移: python manage.py migrate'))
            return

        # 获取创建人（超级用户或第一个用户）
        creator = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not creator:
            self.stdout.write(self.style.ERROR('系统中没有用户，无法创建流程模板'))
            return

        workflows_to_create = [
            {
                'code': 'plan_start_approval',
                'name': '计划启动审批',
                'description': '计划启动的审批流程，审批通过后计划状态从草稿变为已发布',
                'category': '计划管理',
                'content_types': [plan_content_type],
                'timeout_hours': 24,
                'nodes': [
                    {
                        'name': '部门经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'department_manager',
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'can_transfer': True,
                        'timeout_hours': 24,
                    },
                ],
            },
            {
                'code': 'plan_cancel_approval',
                'name': '计划取消审批',
                'description': '计划取消的审批流程，审批通过后计划状态从执行中变为已取消',
                'category': '计划管理',
                'content_types': [plan_content_type],
                'timeout_hours': 24,
                'nodes': [
                    {
                        'name': '部门经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'department_manager',
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'can_transfer': True,
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
                        if key not in ['nodes', 'content_types', 'timeout_hours']:
                            setattr(workflow, key, value)
                    workflow.timeout_hours = workflow_data.get('timeout_hours', 24)
                    workflow.status = 'active'
                    workflow.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'更新流程模板: {code}'))
                else:
                    # 创建新流程模板
                    # 注意：applicable_models 字段在数据库中是必填的，但模型定义中没有
                    # 需要通过 raw SQL 插入
                    from django.db import connection
                    from django.utils import timezone
                    cursor = connection.cursor()
                    
                    # 获取适用的模型名称（格式：逗号分隔的模型名称，如 "plan"）
                    applicable_models_value = 'plan'
                    now = timezone.now()
                    
                    # 使用 raw SQL 插入以设置所有必填字段
                    # 注意：数据库中有一些必填字段但模型定义中没有，需要直接设置
                    cursor.execute("""
                        INSERT INTO workflow_template 
                        (name, code, description, category, status, allow_withdraw, allow_reject, 
                         allow_transfer, timeout_hours, timeout_action, created_by_id, 
                         created_time, updated_time, applicable_models, sub_workflow_trigger_condition)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        workflow_data['name'], code, workflow_data['description'], workflow_data['category'],
                        'active', True, True, True,
                        workflow_data.get('timeout_hours', 24), 'notify',
                        creator.id, now, now,
                        applicable_models_value, ''  # sub_workflow_trigger_condition 设置为空字符串
                    ])
                    workflow_id = cursor.fetchone()[0]
                    # 获取创建的对象
                    workflow = WorkflowTemplate.objects.get(id=workflow_id)
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'创建流程模板: {code}'))

                # 注意：WorkflowTemplate 模型中没有 content_types 字段
                # ContentType 关联通过 applicable_models 字段已经设置（值为 'plan'）

                # 创建审批节点
                for node_data in workflow_data['nodes']:
                    try:
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
                                from backend.apps.system_management.models import Role
                                role = Role.objects.get(name=node_data['approver_role_name'])
                                node.approver_roles.add(role)
                                self.stdout.write(f'  ✓ 创建节点: {node_data["name"]} (关联角色: {role.name})')
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  ⚠ 创建节点: {node_data["name"]} (角色 "{node_data["approver_role_name"]}" 不存在，请手动配置)'))
                        else:
                            self.stdout.write(f'  ✓ 创建节点: {node_data["name"]} (审批人类型: {node_data.get("approver_type", "user")})')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  创建节点失败 {node_data["name"]}: {e}'))
                        logger.error(f'创建节点失败 {node_data["name"]}: {e}', exc_info=True)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'创建流程模板失败 {code}: {e}'))
                logger.error(f'创建流程模板失败 {code}: {e}', exc_info=True)

        self.stdout.write(self.style.SUCCESS(f'\n完成！创建: {created_count}, 更新: {updated_count}, 跳过: {skipped_count}'))
        self.stdout.write(self.style.WARNING('\n注意：'))
        self.stdout.write(self.style.WARNING('1. 审批节点默认使用部门经理（department_manager）作为审批人。'))
        self.stdout.write(self.style.WARNING('2. 如果需要指定特定用户或角色，请在后台管理系统中手动配置审批节点。'))
        self.stdout.write(self.style.WARNING('3. 审批流程模板创建后，计划审批将自动使用审批引擎进行管理。'))

