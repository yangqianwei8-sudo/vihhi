"""
现状评估：审批人规则配置化整改前的风险评估

产出两张表：
1. 存量流程风险清单：列出所有使用 user/custom 的节点
2. 组织链路完备度：统计 User.manager 的填充率、环检测等
"""
from django.core.management.base import BaseCommand
from django.db.models import Q, Count, Exists, OuterRef, F
from django.utils import timezone
from datetime import timedelta
from backend.apps.workflow_engine.models import ApprovalNode, WorkflowTemplate, ApprovalInstance, WorkflowBinding
from backend.apps.system_management.models import User
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = '评估审批人规则配置化整改前的风险（存量流程风险清单 + 组织链路完备度）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('审批人规则配置化整改 - 现状评估'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 表1：存量流程风险清单
        self._assess_workflow_risks()

        self.stdout.write('')
        self.stdout.write('')

        # 表2：组织链路完备度
        self._assess_organization_completeness()

    def _assess_workflow_risks(self):
        """表1：存量流程风险清单"""
        self.stdout.write(self.style.WARNING('【表1】存量流程风险清单'))
        self.stdout.write('-' * 80)

        # 查找所有使用 user/custom 的节点
        risky_nodes = ApprovalNode.objects.filter(
            approver_type__in=['user', 'custom']
        ).select_related('workflow').prefetch_related('approver_users')

        if not risky_nodes.exists():
            self.stdout.write(self.style.SUCCESS('✓ 未发现使用 user/custom 类型的节点，系统已完全配置化'))
            return

        self.stdout.write(f'发现 {risky_nodes.count()} 个风险节点（使用 user/custom 类型）')
        self.stdout.write('')

        # 获取最近30天的实例统计
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_instances = ApprovalInstance.objects.filter(
            created_time__gte=thirty_days_ago
        ).values_list('workflow_id', flat=True).distinct()

        # 按流程模板分组
        workflows_with_risks = {}
        for node in risky_nodes:
            workflow = node.workflow
            if workflow.id not in workflows_with_risks:
                workflows_with_risks[workflow.id] = {
                    'workflow': workflow,
                    'nodes': [],
                    'has_recent_instances': workflow.id in recent_instances,
                }

            # 获取审批人列表
            approver_users = list(node.approver_users.all())
            approver_info = []
            if approver_users:
                approver_info = [f"{u.username} ({u.get_full_name() or '无姓名'})" for u in approver_users[:5]]
                if len(approver_users) > 5:
                    approver_info.append(f'... 等共 {len(approver_users)} 人')

            # 获取业务流程名称（通过 WorkflowBinding）
            business_workflow_name = None
            try:
                # 尝试从 WorkflowBinding 获取业务流程名称
                bindings = WorkflowBinding.objects.filter(workflow_template=workflow, is_active=True)
                if bindings.exists():
                    binding = bindings.first()
                    if binding.content_type and binding.action:
                        from backend.apps.workflow_engine.admin import WorkflowBindingAdmin
                        model = binding.content_type.model
                        action = binding.action
                        workflow_name = WorkflowBindingAdmin.BUSINESS_WORKFLOW_NAMES.get((model, action))
                        if workflow_name:
                            business_workflow_name = workflow_name
            except:
                pass

            if not business_workflow_name:
                business_workflow_name = f"{workflow.name}（未绑定业务流程）"

            workflows_with_risks[workflow.id]['nodes'].append({
                'node': node,
                'approver_users': approver_users,
                'approver_info': approver_info,
            })

        # 输出清单
        self.stdout.write(f'{"业务流程":<30} {"模板ID":<10} {"节点ID":<10} {"节点名称":<30} {"类型":<15} {"写死人对象":<40} {"最近使用":<10}')
        self.stdout.write('-' * 150)

        total_risky_nodes = 0
        high_risk_workflows = []

        for workflow_id, data in sorted(workflows_with_risks.items(), key=lambda x: (not x[1]['has_recent_instances'], x[1]['workflow'].name)):
            workflow = data['workflow']
            has_recent = '是（高风险）' if data['has_recent_instances'] else '否'

            for node_data in data['nodes']:
                node = node_data['node']
                approver_info_str = ', '.join(node_data['approver_info']) if node_data['approver_info'] else '（无审批人）'

                self.stdout.write(
                    f'{business_workflow_name:<30} '
                    f'{workflow.id:<10} '
                    f'{node.id:<10} '
                    f'{node.name[:28]:<30} '
                    f'{node.get_approver_type_display():<15} '
                    f'{approver_info_str[:38]:<40} '
                    f'{has_recent:<10}'
                )
                total_risky_nodes += 1

            if data['has_recent_instances']:
                high_risk_workflows.append(workflow)

        self.stdout.write('-' * 150)
        self.stdout.write(f'总计：{total_risky_nodes} 个风险节点，涉及 {len(workflows_with_risks)} 个流程模板')
        if high_risk_workflows:
            self.stdout.write(self.style.ERROR(f'⚠️  高风险流程（最近30天有实例）：{len(high_risk_workflows)} 个'))
            for wf in high_risk_workflows:
                self.stdout.write(f'   - {wf.name} (ID: {wf.id})')

    def _assess_organization_completeness(self):
        """表2：组织链路完备度"""
        self.stdout.write(self.style.WARNING('【表2】组织链路完备度'))
        self.stdout.write('-' * 80)

        # 统计参与审批的用户（申请人集合）
        applicants = User.objects.filter(
            applied_approvals__isnull=False
        ).distinct()

        total_applicants = applicants.count()
        applicants_with_manager = applicants.filter(manager__isnull=False).count()
        applicants_without_manager = total_applicants - applicants_with_manager

        self.stdout.write(f'参与审批的用户总数：{total_applicants}')
        self.stdout.write(f'已设置 manager 的用户：{applicants_with_manager} ({applicants_with_manager/total_applicants*100:.1f}%)' if total_applicants > 0 else '已设置 manager 的用户：0')
        self.stdout.write(f'未设置 manager 的用户：{applicants_without_manager} ({applicants_without_manager/total_applicants*100:.1f}%)' if total_applicants > 0 else '未设置 manager 的用户：0')
        self.stdout.write('')

        # 按部门统计
        self.stdout.write('按部门统计（仅显示有审批用户的部门）：')
        self.stdout.write(f'{"部门名称":<30} {"用户总数":<10} {"有manager":<12} {"缺失率":<10}')
        self.stdout.write('-' * 70)

        from backend.apps.system_management.models import Department
        departments = Department.objects.filter(
            members__applied_approvals__isnull=False
        ).annotate(
            total_users=Count('members', distinct=True),
            users_with_manager=Count('members', filter=Q(members__manager__isnull=False), distinct=True)
        ).distinct()

        for dept in departments.order_by('-total_users')[:20]:  # 只显示前20个部门
            missing_count = dept.total_users - dept.users_with_manager
            missing_rate = (missing_count / dept.total_users * 100) if dept.total_users > 0 else 0
            self.stdout.write(
                f'{dept.name[:28]:<30} '
                f'{dept.total_users:<10} '
                f'{dept.users_with_manager:<12} '
                f'{missing_rate:.1f}%'
            )

        self.stdout.write('')

        # 环检测
        self.stdout.write('环检测：')
        self._detect_manager_cycles()

        self.stdout.write('')

        # 缺失 manager 的用户列表（按部门分组）
        if applicants_without_manager > 0:
            self.stdout.write(f'缺失 manager 的用户列表（前50个）：')
            missing_manager_users = applicants.filter(manager__isnull=True)[:50]
            self.stdout.write(f'{"用户名":<20} {"姓名":<20} {"部门":<30}')
            self.stdout.write('-' * 70)
            for user in missing_manager_users:
                dept_name = user.department.name if user.department else '（无部门）'
                self.stdout.write(
                    f'{user.username:<20} '
                    f'{(user.get_full_name() or "无姓名"):<20} '
                    f'{dept_name[:28]:<30}'
                )
            if applicants_without_manager > 50:
                self.stdout.write(f'... 还有 {applicants_without_manager - 50} 个用户未显示')

    def _detect_manager_cycles(self):
        """检测 manager 链中的环"""
        # 检测自引用（manager 指向自己）
        self_refs = User.objects.filter(manager=F('id'))
        if self_refs.exists():
            self.stdout.write(self.style.ERROR(f'⚠️  发现 {self_refs.count()} 个用户 manager 指向自己：'))
            for user in self_refs[:10]:
                self.stdout.write(f'   - {user.username} (ID: {user.id})')
            if self_refs.count() > 10:
                self.stdout.write(f'   ... 还有 {self_refs.count() - 10} 个')
        else:
            self.stdout.write(self.style.SUCCESS('✓ 未发现 manager 指向自己的情况'))

        # 检测环（A->B->A 或更长的环）
        # 简单检测：遍历每个用户，向上追溯 manager 链，看是否回到起点
        cycles = []
        checked = set()

        for user in User.objects.filter(manager__isnull=False).select_related('manager'):
            if user.id in checked:
                continue

            chain = []
            current = user
            visited = set()

            while current and current.manager:
                if current.id in visited:
                    # 发现环
                    cycle_start = visited.index(current.id) if current.id in [u.id for u in chain] else None
                    if cycle_start is not None:
                        cycle = [u.username for u in chain[cycle_start:]] + [current.username]
                        cycles.append(cycle)
                        checked.update([u.id for u in chain])
                    break

                visited.add(current.id)
                chain.append(current)
                current = current.manager

                # 防止无限循环（最多追溯10级）
                if len(chain) > 10:
                    break

            checked.add(user.id)

        if cycles:
            self.stdout.write(self.style.ERROR(f'⚠️  发现 {len(cycles)} 个 manager 链环：'))
            for i, cycle in enumerate(cycles[:5], 1):
                self.stdout.write(f'   环 {i}: {" -> ".join(cycle)} -> ...')
            if len(cycles) > 5:
                self.stdout.write(f'   ... 还有 {len(cycles) - 5} 个环')
        else:
            self.stdout.write(self.style.SUCCESS('✓ 未发现 manager 链环'))

        # 统计 manager 链长度分布
        self.stdout.write('')
        self.stdout.write('Manager 链长度分布（向上追溯，最多10级）：')
        length_distribution = {}
        for user in User.objects.filter(manager__isnull=False)[:1000]:  # 采样前1000个用户
            length = 0
            current = user
            while current and current.manager and length < 10:
                length += 1
                current = current.manager

            length_distribution[length] = length_distribution.get(length, 0) + 1

        self.stdout.write(f'{"链长度":<10} {"用户数":<10}')
        self.stdout.write('-' * 20)
        for length in sorted(length_distribution.keys()):
            self.stdout.write(f'{length} 级{"":<6} {length_distribution[length]:<10}')
