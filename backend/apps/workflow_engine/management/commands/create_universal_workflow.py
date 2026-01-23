"""
创建通用审批流程的命令

使用示例：
python manage.py create_universal_workflow \
    --code contract_approval \
    --name "合同审批流程" \
    --category "合同管理" \
    --nodes "部门经理审批:department_manager:1,财务总监审批:role:2,总经理审批:role:3"
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '创建通用审批流程模板'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            required=True,
            help='流程代码（唯一标识）',
        )
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='流程名称',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='通用审批',
            help='流程分类',
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='流程描述',
        )
        parser.add_argument(
            '--nodes',
            type=str,
            required=True,
            help='节点配置，格式：节点1名称:审批人类型:序号,节点2名称:审批人类型:序号',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='如果流程已存在，强制重新创建',
        )

    def handle(self, *args, **options):
        code = options['code']
        name = options['name']
        category = options['category']
        description = options['description']
        nodes_str = options['nodes']
        force = options['force']
        
        # 检查是否已存在
        from backend.apps.workflow_engine.models import WorkflowTemplate
        existing = WorkflowTemplate.objects.filter(code=code).first()
        
        if existing and not force:
            self.stdout.write(
                self.style.WARNING(f'流程模板 {code} 已存在，使用 --force 强制重新创建')
            )
            return
        
        # 解析节点配置
        nodes_config = self._parse_nodes(nodes_str)
        
        # 获取创建人
        creator = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not creator:
            self.stdout.write(self.style.ERROR('系统中没有用户，无法创建流程模板'))
            return
        
        try:
            # 创建审批流程
            workflow = UniversalApprovalService.create_workflow_from_config(
                code=code,
                name=name,
                description=description,
                category=category,
                creator=creator,
                nodes_config=nodes_config,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ 成功创建审批流程：{name} ({code})')
            )
            self.stdout.write(f'  流程ID：{workflow.id}')
            self.stdout.write(f'  节点数量：{len(nodes_config)}')
            
            # 显示节点信息
            for node in workflow.nodes.all():
                self.stdout.write(f'  - {node.name} (序号: {node.sequence}, 类型: {node.approver_type})')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建审批流程失败：{str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def _parse_nodes(self, nodes_str: str) -> list:
        """
        解析节点配置字符串
        
        格式：节点1名称:审批人类型:序号,节点2名称:审批人类型:序号
        
        审批人类型：
        - user: 指定用户（需要在后台手动配置）
        - role: 指定角色（需要提供角色代码）
        - department: 指定部门
        - department_manager: 部门经理（自动获取）
        """
        nodes_config = []
        node_parts = nodes_str.split(',')
        
        for i, node_part in enumerate(node_parts, 1):
            parts = node_part.strip().split(':')
            
            if len(parts) < 3:
                raise ValueError(f'节点配置格式错误：{node_part}，应为：节点名称:审批人类型:序号')
            
            node_name = parts[0].strip()
            approver_type = parts[1].strip()
            sequence = int(parts[2].strip())
            
            node_config = {
                'name': node_name,
                'node_type': 'approval',
                'sequence': sequence,
                'approver_type': approver_type,
                'approval_mode': 'single',
                'is_required': True,
                'can_reject': True,
                'can_transfer': approver_type == 'department_manager',
                'timeout_hours': 24,
            }
            
            # 如果是角色类型，尝试查找角色
            if approver_type == 'role' and len(parts) > 3:
                role_code = parts[3].strip()
                try:
                    role = Role.objects.get(code=role_code)
                    node_config['approver_roles'] = [role]
                    self.stdout.write(f'  找到角色：{role.name} ({role_code})')
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  警告：角色 {role_code} 不存在，请在后台手动配置')
                    )
            
            nodes_config.append(node_config)
        
        return nodes_config

