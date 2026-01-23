"""
配置计划审批流程 V2（基于通用审批流程服务）
运行方式：python manage.py setup_plan_approval_workflow_v2
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置计划审批流程（基于通用审批流程服务）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建已存在的流程模板',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write(self.style.SUCCESS('开始配置计划审批流程...'))
        
        # 获取创建人
        creator = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not creator:
            self.stdout.write(self.style.ERROR('系统中没有用户，无法创建流程模板'))
            return
        
        # 配置计划启动审批流程
        self._setup_plan_start_approval(creator, force)
        
        # 配置计划取消审批流程
        self._setup_plan_cancel_approval(creator, force)
        
        self.stdout.write(self.style.SUCCESS('\n✓ 计划审批流程配置完成！'))
        self.stdout.write(self.style.WARNING('\n注意：'))
        self.stdout.write(self.style.WARNING('1. 审批节点使用部门经理（department_manager）作为审批人'))
        self.stdout.write(self.style.WARNING('2. 确保计划负责人的部门已设置负责人'))
        self.stdout.write(self.style.WARNING('3. 如果需要指定特定用户或角色，请在后台管理系统中手动配置审批节点'))
    
    def _setup_plan_start_approval(self, creator, force):
        """配置计划启动审批流程"""
        self.stdout.write('\n配置计划启动审批流程...')
        
        try:
            workflow = UniversalApprovalService.create_workflow_from_config(
                code='plan_start_approval',
                name='计划启动审批',
                description='计划启动的审批流程，审批通过后计划状态从草稿变为已发布',
                category='计划管理',
                creator=creator,
                applicable_models=['plan'],  # 设置适用的业务模型
                allow_withdraw=True,
                allow_reject=True,
                allow_transfer=True,
                timeout_hours=24,
                timeout_action='notify',
                nodes_config=[
                    {
                        'name': '部门经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'department_manager',  # 自动获取申请人所在部门的部门经理
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'can_transfer': True,
                        'timeout_hours': 24,
                        'description': '部门经理审批计划启动申请，审核计划内容、验收标准等',
                    },
                ],
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ 创建流程模板：{workflow.name} ({workflow.code})'))
            self.stdout.write(f'  节点数量：{workflow.nodes.count()}')
            for node in workflow.nodes.all():
                self.stdout.write(f'    - {node.name} (序号: {node.sequence}, 审批人类型: {node.approver_type})')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'配置计划启动审批流程失败：{str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def _setup_plan_cancel_approval(self, creator, force):
        """配置计划取消审批流程"""
        self.stdout.write('\n配置计划取消审批流程...')
        
        try:
            workflow = UniversalApprovalService.create_workflow_from_config(
                code='plan_cancel_approval',
                name='计划取消审批',
                description='计划取消的审批流程，审批通过后计划状态从执行中变为已取消',
                category='计划管理',
                creator=creator,
                applicable_models=['plan'],  # 设置适用的业务模型
                allow_withdraw=True,
                allow_reject=True,
                allow_transfer=True,
                timeout_hours=24,
                timeout_action='notify',
                nodes_config=[
                    {
                        'name': '部门经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'department_manager',  # 自动获取申请人所在部门的部门经理
                        'approval_mode': 'single',
                        'is_required': True,
                        'can_reject': True,
                        'can_transfer': True,
                        'timeout_hours': 24,
                        'description': '部门经理审批计划取消申请，审核取消原因等',
                    },
                ],
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ 创建流程模板：{workflow.name} ({workflow.code})'))
            self.stdout.write(f'  节点数量：{workflow.nodes.count()}')
            for node in workflow.nodes.all():
                self.stdout.write(f'    - {node.name} (序号: {node.sequence}, 审批人类型: {node.approver_type})')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'配置计划取消审批流程失败：{str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

