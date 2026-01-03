"""
审批流程连接示例代码

本文件展示了如何在业务代码中将审批流程模板连接到具体的审批实例。
"""

from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.delivery_customer.models import OutgoingDocument
import logging

logger = logging.getLogger(__name__)


def start_document_approval(document_id, applicant, comment=''):
    """
    启动发文审批流程示例
    
    Args:
        document_id: 发文ID
        applicant: 申请人（User对象）
        comment: 申请说明
    
    Returns:
        ApprovalInstance: 审批实例对象
    """
    # 1. 获取业务对象
    try:
        document = OutgoingDocument.objects.get(id=document_id)
    except OutgoingDocument.DoesNotExist:
        raise ValueError(f'发文 {document_id} 不存在')
    
    # 2. 检查是否已有审批实例
    content_type = ContentType.objects.get_for_model(OutgoingDocument)
    existing_instance = ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=document.id,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_instance:
        raise ValueError(f'该发文已有审批流程：{existing_instance.instance_number}')
    
    # 3. 获取流程模板（通过流程代码）
    try:
        workflow = WorkflowTemplate.objects.get(
            code='document_approval',  # 发文审批流程代码
            status='active'  # 必须是启用状态
        )
    except WorkflowTemplate.DoesNotExist:
        raise ValueError('未找到启用的发文审批流程（代码：document_approval）')
    
    # 4. 启动审批流程
    instance = ApprovalEngine.start_approval(
        workflow=workflow,
        content_object=document,  # 业务对象
        applicant=applicant,       # 申请人
        comment=comment or f'提交发文审批：{document.title}'  # 申请说明
    )
    
    # 5. 更新业务对象状态（可选）
    document.status = 'reviewing'  # 审核中
    document.save(update_fields=['status'])
    
    logger.info(f'审批流程已启动：实例编号={instance.instance_number}, 发文={document.document_number}')
    
    return instance


def get_document_approval_instance(document_id):
    """
    获取发文的审批实例
    
    Args:
        document_id: 发文ID
    
    Returns:
        ApprovalInstance or None
    """
    try:
        document = OutgoingDocument.objects.get(id=document_id)
    except OutgoingDocument.DoesNotExist:
        return None
    
    content_type = ContentType.objects.get_for_model(OutgoingDocument)
    return ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=document.id
    ).order_by('-created_time').first()


def check_approval_status(document_id):
    """
    检查发文的审批状态
    
    Args:
        document_id: 发文ID
    
    Returns:
        dict: {
            'has_approval': bool,  # 是否有审批流程
            'status': str,         # 审批状态
            'current_node': str,   # 当前节点名称
            'instance_number': str # 实例编号
        }
    """
    instance = get_document_approval_instance(document_id)
    
    if not instance:
        return {
            'has_approval': False,
            'status': None,
            'current_node': None,
            'instance_number': None
        }
    
    return {
        'has_approval': True,
        'status': instance.status,
        'status_display': instance.get_status_display(),
        'current_node': instance.current_node.name if instance.current_node else None,
        'instance_number': instance.instance_number,
        'workflow_name': instance.workflow.name,
        'applicant': instance.applicant.username,
        'apply_time': instance.apply_time
    }


# ==================== 在视图中使用的示例 ====================

"""
# 在 views_pages.py 中的使用示例

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from backend.apps.workflow_engine.examples.start_approval_example import start_document_approval

@login_required
def outgoing_document_submit_for_approval(request, document_id):
    '''提交发文审批'''
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    # 检查权限
    if document.status != 'draft':
        messages.error(request, '只能提交草稿状态的发文')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
    
    try:
        # 启动审批流程
        instance = start_document_approval(
            document_id=document_id,
            applicant=request.user,
            comment=f'用户 {request.user.username} 提交发文审批'
        )
        
        messages.success(request, f'审批流程已启动，实例编号：{instance.instance_number}')
        return redirect('workflow_engine:approval_detail', instance_id=instance.id)
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
    except Exception as e:
        logger.exception('启动审批流程失败')
        messages.error(request, f'启动审批流程失败：{str(e)}')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
"""


# ==================== 通用方法：通过流程代码启动审批 ====================

def start_approval_by_code(content_object, workflow_code, applicant, comment=''):
    """
    通过流程代码启动审批流程（通用方法）
    
    Args:
        content_object: 业务对象（如 OutgoingDocument、Contract等）
        workflow_code: 流程代码（如 'document_approval'）
        applicant: 申请人（User对象）
        comment: 申请说明
    
    Returns:
        ApprovalInstance: 审批实例对象
    """
    # 1. 检查是否已有审批实例
    content_type = ContentType.objects.get_for_model(content_object)
    existing_instance = ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=content_object.id,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_instance:
        raise ValueError(f'该对象已有审批流程：{existing_instance.instance_number}')
    
    # 2. 获取流程模板
    try:
        workflow = WorkflowTemplate.objects.get(
            code=workflow_code,
            status='active'
        )
    except WorkflowTemplate.DoesNotExist:
        raise ValueError(f'未找到启用的审批流程（代码：{workflow_code}）')
    
    # 3. 启动审批流程
    instance = ApprovalEngine.start_approval(
        workflow=workflow,
        content_object=content_object,
        applicant=applicant,
        comment=comment
    )
    
    logger.info(
        f'审批流程已启动：'
        f'流程={workflow.name}({workflow_code}), '
        f'实例={instance.instance_number}, '
        f'对象={content_type.model}#{content_object.id}'
    )
    
    return instance


# ==================== 在业务对象模型中添加便捷方法 ====================

"""
# 在 OutgoingDocument 模型中添加以下代码：

from django.contrib.contenttypes.fields import GenericRelation

class OutgoingDocument(models.Model):
    # ... 现有字段 ...
    
    # 添加通用关系（用于反向查询审批实例）
    approval_instances = GenericRelation(
        'workflow_engine.ApprovalInstance',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='outgoing_document'
    )
    
    def get_current_approval_instance(self):
        '''获取当前审批实例'''
        return self.approval_instances.filter(
            status__in=['pending', 'approved']
        ).order_by('-created_time').first()
    
    def start_approval(self, workflow_code='document_approval', applicant=None, comment=''):
        '''启动审批流程'''
        from backend.apps.workflow_engine.models import WorkflowTemplate
        from backend.apps.workflow_engine.services import ApprovalEngine
        
        # 检查是否已有审批实例
        if self.get_current_approval_instance():
            raise ValueError('该发文已有审批流程')
        
        # 获取流程模板
        try:
            workflow = WorkflowTemplate.objects.get(code=workflow_code, status='active')
        except WorkflowTemplate.DoesNotExist:
            raise ValueError(f'未找到启用的审批流程（代码：{workflow_code}）')
        
        # 启动审批
        instance = ApprovalEngine.start_approval(
            workflow=workflow,
            content_object=self,
            applicant=applicant,
            comment=comment
        )
        
        # 更新状态
        self.status = 'reviewing'
        self.save(update_fields=['status'])
        
        return instance

# 使用示例：
document = OutgoingDocument.objects.get(id=123)
instance = document.start_approval(
    workflow_code='document_approval',
    applicant=request.user,
    comment='请审批此发文'
)
"""

