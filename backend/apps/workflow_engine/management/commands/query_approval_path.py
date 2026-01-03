"""
查询审批路径脚本
用于查询指定用户提交的审批流程的完整审批路径
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord, ApprovalNode
from backend.apps.customer_management.models import Client
from collections import defaultdict

User = get_user_model()


class Command(BaseCommand):
    help = '查询指定用户提交的审批流程的审批路径'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='申请人用户名',
            required=True
        )
        parser.add_argument(
            '--workflow-code',
            type=str,
            default='customer_management_approval',
            help='审批流程代码（默认：customer_management_approval）'
        )

    def handle(self, *args, **options):
        username = options['username']
        workflow_code = options['workflow_code']
        
        self.stdout.write('='*80)
        self.stdout.write(f'查询用户 "{username}" 提交的审批路径')
        self.stdout.write('='*80)
        
        # 查找用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'错误：未找到用户 "{username}"'))
            return
        
        self.stdout.write(f'\n用户信息：')
        self.stdout.write(f'  用户名：{user.username}')
        self.stdout.write(f'  姓名：{user.get_full_name() or user.username}')
        self.stdout.write(f'  ID：{user.id}')
        
        # 查找该用户提交的审批实例
        instances = ApprovalInstance.objects.filter(
            applicant=user,
            workflow__code=workflow_code
        ).select_related(
            'workflow', 'applicant', 'current_node'
        ).prefetch_related(
            'records__node', 'records__approver', 'records__transferred_to'
        ).order_by('-created_time')
        
        if not instances.exists():
            self.stdout.write(self.style.WARNING(f'\n未找到用户 "{username}" 提交的审批实例（流程代码：{workflow_code}）'))
            return
        
        self.stdout.write(f'\n找到 {instances.count()} 个审批实例：')
        
        for idx, instance in enumerate(instances, 1):
            self.stdout.write('\n' + '-'*80)
            self.stdout.write(self.style.SUCCESS(f'\n审批实例 #{idx}'))
            self.stdout.write('-'*80)
            
            # 显示审批实例基本信息
            self.stdout.write(f'\n基本信息：')
            self.stdout.write(f'  审批编号：{instance.instance_number}')
            self.stdout.write(f'  流程名称：{instance.workflow.name}')
            self.stdout.write(f'  审批状态：{instance.get_status_display()}')
            self.stdout.write(f'  申请时间：{instance.apply_time.strftime("%Y-%m-%d %H:%M:%S") if instance.apply_time else "未设置"}')
            self.stdout.write(f'  申请说明：{instance.apply_comment or "无"}')
            
            if instance.current_node:
                self.stdout.write(f'  当前节点：{instance.current_node.name}（顺序：{instance.current_node.sequence}）')
            else:
                self.stdout.write(f'  当前节点：无（审批已完成或已终止）')
            
            if instance.completed_time:
                self.stdout.write(f'  完成时间：{instance.completed_time.strftime("%Y-%m-%d %H:%M:%S")}')
            
            # 获取关联的业务对象
            try:
                content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
                self.stdout.write(f'\n关联业务对象：')
                if isinstance(content_obj, Client):
                    self.stdout.write(f'  对象类型：客户（Client）')
                    self.stdout.write(f'  客户名称：{content_obj.name}')
                    self.stdout.write(f'  客户编码：{content_obj.code}')
                    self.stdout.write(f'  客户ID：{content_obj.id}')
                else:
                    self.stdout.write(f'  对象类型：{instance.content_type.model}')
                    self.stdout.write(f'  对象ID：{instance.object_id}')
                    self.stdout.write(f'  对象：{str(content_obj)}')
            except Exception as e:
                self.stdout.write(f'\n关联业务对象：无法获取（可能已被删除）')
            
            # 显示审批路径
            self.stdout.write(f'\n审批路径：')
            self.stdout.write('-'*80)
            
            # 获取所有审批节点（按顺序）
            workflow_nodes = instance.workflow.nodes.all().order_by('sequence')
            
            # 获取所有审批记录（按审批时间排序）
            all_records = instance.records.all().select_related('node', 'approver', 'transferred_to').order_by('approval_time')
            
            # 按节点分组审批记录
            records_by_node = defaultdict(list)
            for record in all_records:
                records_by_node[record.node_id].append(record)
            
            # 显示每个节点的审批情况
            for node in workflow_nodes:
                node_records = records_by_node.get(node.id, [])
                
                # 节点信息
                self.stdout.write(f'\n节点：{node.name}（顺序：{node.sequence}，类型：{node.get_node_type_display()}）')
                
                if node_records:
                    for record in node_records:
                        result_display = record.get_result_display()
                        result_color = {
                            'approved': '通过',
                            'rejected': '驳回',
                            'pending': '待审批',
                            'transferred': '转交',
                            'withdrawn': '撤回'
                        }.get(record.result, record.result)
                        
                        # 状态标识
                        if record.result == 'approved':
                            status_icon = '✅'
                            status_color = 'SUCCESS'
                        elif record.result == 'rejected':
                            status_icon = '❌'
                            status_color = 'ERROR'
                        elif record.result == 'pending':
                            status_icon = '⏳'
                            status_color = 'WARNING'
                        elif record.result == 'transferred':
                            status_icon = '🔄'
                            status_color = 'WARNING'
                        else:
                            status_icon = '⏸️'
                            status_color = 'WARNING'
                        
                        self.stdout.write(f'  {status_icon} 审批人：{record.approver.get_full_name() or record.approver.username} ({record.approver.username})')
                        result_msg = result_display
                        if status_color == 'SUCCESS':
                            self.stdout.write(self.style.SUCCESS(f'     结果：{result_msg}'))
                        elif status_color == 'ERROR':
                            self.stdout.write(self.style.ERROR(f'     结果：{result_msg}'))
                        elif status_color == 'WARNING':
                            self.stdout.write(self.style.WARNING(f'     结果：{result_msg}'))
                        else:
                            self.stdout.write(f'     结果：{result_msg}')
                        
                        if record.approval_time:
                            self.stdout.write(f'     时间：{record.approval_time.strftime("%Y-%m-%d %H:%M:%S")}')
                        
                        if record.comment:
                            self.stdout.write(f'     意见：{record.comment}')
                        
                        if record.transferred_to:
                            self.stdout.write(f'     转交给：{record.transferred_to.get_full_name() or record.transferred_to.username}')
                        
                        self.stdout.write('')
                else:
                    # 没有审批记录，显示节点配置信息
                    self.stdout.write(f'  ⏸️  暂无审批记录')
                    if node.node_type == 'approval':
                        approver_info = '未配置'
                        if node.approver_type == 'role' and node.approver_roles.exists():
                            roles = ', '.join([r.name for r in node.approver_roles.all()])
                            approver_info = f'角色：{roles}'
                        elif node.approver_type == 'department_manager':
                            approver_info = '部门经理'
                        elif node.approver_type == 'user' and node.approver_users.exists():
                            users = ', '.join([u.username for u in node.approver_users.all()])
                            approver_info = f'指定用户：{users}'
                        
                        self.stdout.write(f'     预期审批人：{approver_info}')
                    self.stdout.write('')
            
            # 显示审批流程总结
            self.stdout.write('\n' + '-'*80)
            self.stdout.write('审批流程总结：')
            self.stdout.write('-'*80)
            
            approved_nodes = set()
            pending_nodes = set()
            rejected_nodes = set()
            
            for record in all_records:
                if record.result == 'approved':
                    approved_nodes.add(record.node.name)
                elif record.result == 'pending':
                    pending_nodes.add(record.node.name)
                elif record.result == 'rejected':
                    rejected_nodes.add(record.node.name)
            
            if approved_nodes:
                self.stdout.write(f'\n✅ 已通过的节点：{", ".join(approved_nodes)}')
            if pending_nodes:
                self.stdout.write(f'\n⏳ 待审批的节点：{", ".join(pending_nodes)}')
            if rejected_nodes:
                self.stdout.write(f'\n❌ 已驳回的节点：{", ".join(rejected_nodes)}')
            
            # 审批路径可视化
            self.stdout.write(f'\n审批路径可视化：')
            self.stdout.write('  ', ending='')
            for i, node in enumerate(workflow_nodes):
                if node.node_type == 'start':
                    self.stdout.write('【开始】', ending='')
                elif node.node_type == 'end':
                    self.stdout.write('【结束】', ending='')
                else:
                    has_approved = any(r.result == 'approved' for r in records_by_node.get(node.id, []))
                    has_rejected = any(r.result == 'rejected' for r in records_by_node.get(node.id, []))
                    has_pending = any(r.result == 'pending' for r in records_by_node.get(node.id, []))
                    
                    if has_rejected:
                        self.stdout.write(f'【{node.name}❌】', ending='')
                    elif has_approved:
                        self.stdout.write(f'【{node.name}✅】', ending='')
                    elif has_pending:
                        self.stdout.write(f'【{node.name}⏳】', ending='')
                    else:
                        self.stdout.write(f'【{node.name}】', ending='')
                
                if i < len(workflow_nodes) - 1:
                    self.stdout.write(' → ', ending='')
            
            self.stdout.write('')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('查询完成！'))
        self.stdout.write('='*80)

