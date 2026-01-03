"""
测试客户管理审批流程
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.customer_management.models import Client
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    help = '测试客户管理审批流程'

    def handle(self, *args, **options):
        self.stdout.write('开始测试客户管理审批流程...\n')
        
        # 1. 检查审批流程配置
        self.stdout.write('1. 检查审批流程配置...')
        workflow = WorkflowTemplate.objects.filter(
            code='customer_management_approval',
            status='active'
        ).first()
        
        if not workflow:
            self.stdout.write(self.style.ERROR('❌ 审批流程未找到或未启用'))
            self.stdout.write('   请运行: python manage.py setup_customer_approval_workflow')
            return
        
        self.stdout.write(self.style.SUCCESS(f'   ✓ 找到审批流程：{workflow.name}'))
        self.stdout.write(f'   节点数量：{workflow.nodes.count()}')
        for node in workflow.nodes.all().order_by('sequence'):
            approver_info = '未配置'
            if node.approver_roles.exists():
                roles = ', '.join([r.name for r in node.approver_roles.all()])
                approver_info = f'角色：{roles}'
            self.stdout.write(f'   - {node.sequence}. {node.name} ({approver_info})')
        
        # 2. 检查审批人
        self.stdout.write('\n2. 检查审批人配置...')
        all_approvers = []
        for node in workflow.nodes.all():
            if node.approver_roles.exists():
                for role in node.approver_roles.all():
                    users = role.users.filter(is_active=True)
                    if users.exists():
                        self.stdout.write(self.style.SUCCESS(f'   ✓ {node.name} - {role.name}：{users.count()}个用户'))
                        for user in users[:3]:
                            self.stdout.write(f'      - {user.username}')
                        all_approvers.extend(list(users))
                    else:
                        self.stdout.write(self.style.WARNING(f'   ⚠ {node.name} - {role.name}：没有激活的用户'))
        
        if not all_approvers:
            self.stdout.write(self.style.ERROR('   ❌ 没有找到任何审批人，请先为用户分配角色'))
            return
        
        # 3. 获取测试用户和客户
        self.stdout.write('\n3. 准备测试数据...')
        applicant = User.objects.filter(is_active=True).first()
        if not applicant:
            self.stdout.write(self.style.ERROR('   ❌ 没有找到可用的申请人'))
            return
        
        self.stdout.write(f'   申请人：{applicant.username}')
        
        # 获取一个测试客户（使用values避免字段问题）
        try:
            test_client = Client.objects.only('id', 'name', 'code').first()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   无法查询客户表：{str(e)}'))
            self.stdout.write('   请先执行数据库迁移或手动指定客户ID')
            # 尝试使用ID=1的客户
            try:
                test_client = Client.objects.only('id', 'name', 'code').get(id=1)
            except:
                self.stdout.write(self.style.ERROR('   ❌ 无法获取测试客户，请手动创建客户后再测试'))
                return
        
        if not test_client:
            self.stdout.write(self.style.WARNING('   没有找到客户，请先创建客户'))
            self.stdout.write('   可以访问 /business/customers/create/ 创建客户')
            return
        
        self.stdout.write(f'   使用客户：{test_client.name} (ID: {test_client.id}, 编码: {test_client.code})')
        
        # 4. 检查是否已有审批实例
        self.stdout.write('\n4. 检查现有审批实例...')
        content_type = ContentType.objects.get_for_model(Client)
        existing = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=test_client.id,
            status='pending'
        ).first()
        
        if existing:
            self.stdout.write(self.style.WARNING(f'   ⚠ 该客户已有正在进行的审批：{existing.instance_number}'))
            self.stdout.write('   跳过创建新审批实例')
            instance = existing
        else:
            # 5. 启动审批流程
            self.stdout.write('\n5. 启动审批流程...')
            try:
                instance = ApprovalEngine.start_approval(
                    workflow=workflow,
                    content_object=test_client,
                    applicant=applicant,
                    comment=f'测试审批流程 - 客户：{test_client.name}'
                )
                self.stdout.write(self.style.SUCCESS(f'   ✓ 审批流程已启动'))
                self.stdout.write(f'   审批编号：{instance.instance_number}')
                self.stdout.write(f'   当前状态：{instance.get_status_display()}')
                if instance.current_node:
                    self.stdout.write(f'   当前节点：{instance.current_node.name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ 启动审批流程失败：{str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())
                return
        
        # 6. 检查待审批记录
        self.stdout.write('\n6. 检查待审批记录...')
        pending_records = instance.records.filter(result='pending')
        if pending_records.exists():
            self.stdout.write(self.style.SUCCESS(f'   ✓ 找到 {pending_records.count()} 条待审批记录'))
            for record in pending_records:
                self.stdout.write(f'   - {record.node.name}：等待 {record.approver.username} 审批')
        else:
            self.stdout.write(self.style.WARNING('   ⚠ 没有找到待审批记录'))
        
        # 7. 显示审批流程状态
        self.stdout.write('\n7. 审批流程状态：')
        self.stdout.write(f'   审批编号：{instance.instance_number}')
        self.stdout.write(f'   审批状态：{instance.get_status_display()}')
        self.stdout.write(f'   申请人：{instance.applicant.username}')
        self.stdout.write(f'   申请时间：{instance.apply_time.strftime("%Y-%m-%d %H:%M:%S")}')
        if instance.current_node:
            self.stdout.write(f'   当前节点：{instance.current_node.name}')
        else:
            self.stdout.write('   当前节点：无（流程已完成或未开始）')
        
        # 8. 显示所有审批记录
        all_records = instance.records.all().order_by('approval_time')
        if all_records.exists():
            self.stdout.write(f'\n8. 审批记录（共{all_records.count()}条）：')
            for i, record in enumerate(all_records, 1):
                result_display = {
                    'pending': '待审批',
                    'approved': '通过',
                    'rejected': '驳回',
                    'transferred': '转交',
                    'withdrawn': '撤回',
                }.get(record.result, record.result)
                self.stdout.write(f'   {i}. {record.node.name} - {record.approver.username}：{result_display}')
                if record.comment:
                    self.stdout.write(f'      意见：{record.comment}')
                self.stdout.write(f'      时间：{record.approval_time.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # 9. 测试总结
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ 测试完成！'))
        self.stdout.write('='*60)
        self.stdout.write('\n下一步操作：')
        self.stdout.write('1. 使用审批人账号登录系统')
        self.stdout.write('2. 访问 /workflow/approvals/ 查看待审批事项')
        self.stdout.write(f'3. 或直接访问审批详情：/workflow/approvals/{instance.id}/')
        self.stdout.write(f'4. 在客户详情页查看审批状态：/business/customers/{test_client.id}/')
        self.stdout.write('='*60)

