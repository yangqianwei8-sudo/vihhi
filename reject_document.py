#!/usr/bin/env python
"""
拒绝发文审批的脚本
用法: python reject_document.py FW20250016 "拒绝原因"
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from backend.apps.delivery_customer.models import OutgoingDocument
from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
from backend.apps.workflow_engine.services import ApprovalEngine
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

def reject_document(document_number, comment="审批退回", approver_username=None):
    """拒绝发文审批"""
    try:
        # 查找发文
        document = OutgoingDocument.objects.get(document_number=document_number)
        print(f"找到发文: {document.document_number} - {document.title}")
        print(f"当前状态: {document.get_status_display()}")
        
        # 查找审批实例
        content_type = ContentType.objects.get_for_model(OutgoingDocument)
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=document.id,
            status='pending'
        ).first()
        
        if not approval_instance:
            # 检查是否有已完成的审批实例
            all_instances = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=document.id
            )
            if all_instances.exists():
                print(f"警告: 该发文有审批记录，但当前没有进行中的审批流程")
                for inst in all_instances:
                    print(f"  - 审批编号: {inst.instance_number}, 状态: {inst.get_status_display()}")
            else:
                print(f"警告: 该发文没有审批流程记录")
            
            # 如果状态是审核中但没有审批实例，可能是数据不一致
            if document.status == 'reviewing':
                print(f"状态是审核中，但没有找到审批实例，可能是数据不一致")
                print(f"将直接更新状态为草稿")
                document.transition_to('draft', actor=None, comment=comment)
                document.save()
                print(f"✓ 发文已退回草稿")
                return True
            else:
                print(f"错误: 发文状态为 {document.get_status_display()}，无法退回")
                return False
        
        print(f"找到审批实例: {approval_instance.instance_number}")
        print(f"审批状态: {approval_instance.get_status_display()}")
        
        # 获取审批人
        if approver_username:
            approver = User.objects.get(username=approver_username)
        else:
            # 查找当前节点的待审批记录
            pending_records = ApprovalRecord.objects.filter(
                instance=approval_instance,
                result='pending'
            )
            if pending_records.exists():
                approver = pending_records.first().approver
                print(f"使用当前审批人: {approver.username}")
            else:
                # 如果没有待审批记录，使用管理员或第一个审批人
                approver = User.objects.filter(is_superuser=True).first() or User.objects.first()
                print(f"警告: 没有找到待审批记录，使用管理员: {approver.username if approver else '无'}")
        
        if not approver:
            print("错误: 无法找到审批人")
            return False
        
        # 通过审批流程引擎拒绝
        success = ApprovalEngine.approve(
            instance=approval_instance,
            approver=approver,
            result='rejected',
            comment=comment
        )
        
        if not success:
            print("错误: 审批拒绝操作失败")
            return False
        
        # 刷新审批实例
        approval_instance.refresh_from_db()
        print(f"审批流程状态: {approval_instance.get_status_display()}")
        
        # 更新发文状态为草稿
        document.transition_to('draft', actor=approver, comment=comment, reviewer=approver)
        print(f"✓ 发文已退回草稿")
        print(f"✓ 审批流程已拒绝")
        
        return True
        
    except OutgoingDocument.DoesNotExist:
        print(f"错误: 未找到编号为 {document_number} 的发文")
        return False
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python reject_document.py <发文编号> [拒绝原因] [审批人用户名]")
        print("示例: python reject_document.py FW20250016 '需要修改内容' admin")
        sys.exit(1)
    
    document_number = sys.argv[1]
    comment = sys.argv[2] if len(sys.argv) > 2 else "审批退回"
    approver_username = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = reject_document(document_number, comment, approver_username)
    sys.exit(0 if success else 1)

