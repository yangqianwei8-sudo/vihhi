"""
检查审批流程问题：为什么总经理审批节点会有多个审批人
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '检查审批流程问题：为什么总经理审批节点会有多个审批人'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("检查审批流程问题..."))
        self.stdout.write("")

        # 1. 检查总经理角色和用户
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("1. 检查总经理角色配置"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        gm_role = Role.objects.filter(code='general_manager').first()
        if gm_role:
            self.stdout.write(f"  总经理角色: {gm_role.name} (code: {gm_role.code})")
            users = User.objects.filter(roles=gm_role, is_active=True)
            self.stdout.write(f"  具有总经理角色的用户数: {users.count()}")
            for u in users:
                self.stdout.write(f"    - {u.get_full_name() or u.username} (ID: {u.id}, 用户名: {u.username})")
        else:
            self.stdout.write(self.style.ERROR("  ❌ 未找到总经理角色（general_manager）"))
        
        self.stdout.write("")

        # 2. 检查客户管理审批流程配置
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("2. 检查客户管理审批流程配置"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        workflow = WorkflowTemplate.objects.filter(code='customer_management_approval').first()
        if not workflow:
            self.stdout.write(self.style.ERROR("  ❌ 未找到客户管理审批流程"))
            return
        
        self.stdout.write(f"  流程名称: {workflow.name}")
        self.stdout.write(f"  流程代码: {workflow.code}")
        self.stdout.write(f"  流程状态: {workflow.status}")
        self.stdout.write("")

        # 检查总经理审批节点
        gm_node = workflow.nodes.filter(name='总经理审批').first()
        if gm_node:
            self.stdout.write(f"  总经理审批节点:")
            self.stdout.write(f"    - 节点名称: {gm_node.name}")
            self.stdout.write(f"    - 节点顺序: {gm_node.sequence}")
            self.stdout.write(f"    - 审批人类型: {gm_node.get_approver_type_display()}")
            self.stdout.write(f"    - 审批模式: {gm_node.get_approval_mode_display()}")
            
            # 检查审批人角色
            if gm_node.approver_type == 'role':
                roles = gm_node.approver_roles.all()
                self.stdout.write(f"    - 审批人角色数: {roles.count()}")
                for role in roles:
                    self.stdout.write(f"      * {role.name} (code: {role.code})")
                    role_users = User.objects.filter(roles=role, is_active=True)
                    self.stdout.write(f"        用户数: {role_users.count()}")
                    for u in role_users:
                        self.stdout.write(f"          - {u.get_full_name() or u.username} (ID: {u.id})")
            
            # 检查审批人用户
            if gm_node.approver_users.exists():
                self.stdout.write(f"    - 指定审批人用户数: {gm_node.approver_users.count()}")
                for u in gm_node.approver_users.all():
                    self.stdout.write(f"      - {u.get_full_name() or u.username} (ID: {u.id})")
        else:
            self.stdout.write(self.style.ERROR("  ❌ 未找到总经理审批节点"))
        
        self.stdout.write("")

        # 3. 检查具体的审批实例
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("3. 检查审批实例 customer_management_approval-20251203-0003"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        instance = ApprovalInstance.objects.filter(instance_number='customer_management_approval-20251203-0003').first()
        if instance:
            self.stdout.write(f"  实例编号: {instance.instance_number}")
            self.stdout.write(f"  状态: {instance.status}")
            self.stdout.write(f"  当前节点: {instance.current_node.name if instance.current_node else '无'}")
            self.stdout.write(f"  申请人: {instance.applicant.get_full_name() or instance.applicant.username}")
            self.stdout.write("")

            # 检查总经理审批节点的审批记录
            if gm_node:
                records = ApprovalRecord.objects.filter(
                    instance=instance,
                    node=gm_node
                ).order_by('approval_time')
                
                self.stdout.write(f"  总经理审批节点记录数: {records.count()}")
                for record in records:
                    self.stdout.write(f"    - 审批人: {record.approver.get_full_name() or record.approver.username} (ID: {record.approver.id})")
                    self.stdout.write(f"      结果: {record.get_result_display()}")
                    self.stdout.write(f"      时间: {record.approval_time}")
                    self.stdout.write(f"      意见: {record.comment or '无'}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ 未找到该审批实例，可能已被删除"))
        
        self.stdout.write("")

        # 4. 分析问题原因
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("4. 问题分析"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        if gm_node and gm_node.approver_type == 'role':
            if gm_role:
                role_users = User.objects.filter(roles=gm_role, is_active=True)
                if role_users.count() > 1:
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠ 问题原因：有 {role_users.count()} 个用户具有总经理角色"
                    ))
                    self.stdout.write(self.style.WARNING(
                        "    审批引擎在查找审批人时，会为所有具有该角色的用户创建审批记录"
                    ))
                    self.stdout.write("")
                    self.stdout.write("  解决方案：")
                    self.stdout.write("    1. 如果审批模式是'single'（单人审批），应该只创建一个审批记录")
                    self.stdout.write("    2. 检查 _create_pending_records 方法，看是否正确处理了'single'模式")
                    self.stdout.write("    3. 或者确保只有一个用户具有总经理角色")
                else:
                    self.stdout.write(self.style.SUCCESS("  ✓ 只有一个用户具有总经理角色，这是正常的"))
            else:
                self.stdout.write(self.style.ERROR("  ❌ 未找到总经理角色"))

