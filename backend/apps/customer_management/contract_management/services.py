"""
合同管理模块业务逻辑服务层

将业务逻辑从视图中分离出来，提高代码的可维护性和可测试性。
"""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from backend.apps.production_management.models import BusinessContract
from .utils import (
    generate_contract_number,
    calculate_contract_period,
    calculate_unpaid_amount,
)
from .constants import CONTRACT_STATUS_DRAFT


class ContractService:
    """合同服务类"""
    
    @staticmethod
    def create_contract(form_data, user, post_data=None, **kwargs):
        """
        创建合同
        
        Args:
            form_data: 表单数据（字典，包含合同基本字段）
            user: 创建用户
            post_data: POST请求数据（QueryDict或字典），用于处理关联数据
            **kwargs: 其他参数（如authorization_letter等）
            
        Returns:
            tuple: (contract对象, 是否成功, 错误消息)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            with transaction.atomic():
                # 生成合同编号（如果未提供）
                if not form_data.get('contract_number'):
                    form_data['contract_number'] = generate_contract_number()
                
                # 设置创建人
                form_data['created_by'] = user
                
                # 设置默认状态
                if not form_data.get('status'):
                    form_data['status'] = CONTRACT_STATUS_DRAFT
                
                # 计算合同期限
                if form_data.get('start_date') and form_data.get('end_date'):
                    form_data['contract_period'] = calculate_contract_period(
                        form_data['start_date'],
                        form_data['end_date']
                    )
                
                # 处理项目编号：优先从商机赢单的项目编号获取，其次从业务委托书获取
                # 1. 如果关联了商机且商机有项目编号（赢单后生成），使用商机的项目编号
                if form_data.get('opportunity'):
                    from backend.apps.customer_management.models import BusinessOpportunity
                    try:
                        opportunity = BusinessOpportunity.objects.get(id=form_data['opportunity'])
                        if opportunity.project_number:
                            form_data['project_number'] = opportunity.project_number
                    except BusinessOpportunity.DoesNotExist:
                        pass
                
                # 2. 如果从业务委托书转换，且还没有项目编号，使用业务委托书的项目编号
                if not form_data.get('project_number'):
                    authorization_letter = kwargs.get('authorization_letter')
                    if authorization_letter and hasattr(authorization_letter, 'project_number'):
                        if authorization_letter.project_number:
                            form_data['project_number'] = authorization_letter.project_number
                
                # 创建合同
                contract = BusinessContract.objects.create(**form_data)
                
                # 处理关联数据（如果提供了post_data）
                if post_data:
                    # 处理签约主体
                    ContractService._save_contract_parties(contract, post_data, logger)
                    
                    # 注意：服务信息、价款信息等目前可能没有对应的模型
                    # 如果需要保存，可以在这里添加相应的处理逻辑
                
                return contract, True, None
                
        except Exception as e:
            logger.exception('创建合同失败: %s', str(e))
            return None, False, str(e)
    
    @staticmethod
    def _save_contract_parties(contract, post_data, logger):
        """
        保存合同签约主体
        
        Args:
            contract: 合同对象
            post_data: POST请求数据
            logger: 日志记录器
        """
        try:
            from backend.apps.production_management.models import ContractParty
            
            # 删除旧的签约主体
            ContractParty.objects.filter(contract=contract).delete()
            
            # 解析POST数据中的签约主体信息
            # 格式：party[0][party_name], party[0][party_contact], ...
            party_index = 0
            parties_data = []
            
            while True:
                party_key_prefix = f'party[{party_index}]'
                party_name_key = f'{party_key_prefix}[party_name]'
                
                # 检查是否存在该索引的签约主体数据
                if party_name_key not in post_data:
                    break
                
                party_data = {
                    'contract': contract,
                    'party_name': post_data.get(party_name_key, '').strip(),
                    'party_type': post_data.get(f'{party_key_prefix}[party_type]', 'party_a'),
                    'credit_code': post_data.get(f'{party_key_prefix}[credit_code]', '').strip(),
                    'legal_representative': post_data.get(f'{party_key_prefix}[legal_representative]', '').strip(),
                    'project_manager': post_data.get(f'{party_key_prefix}[project_manager]', '').strip(),
                    'party_contact': post_data.get(f'{party_key_prefix}[party_contact]', '').strip(),
                    'contact_phone': post_data.get(f'{party_key_prefix}[contact_phone]', '').strip(),
                    'contact_email': post_data.get(f'{party_key_prefix}[contact_email]', '').strip(),
                    'address': post_data.get(f'{party_key_prefix}[address]', '').strip(),
                    'order': party_index,
                    'is_active': True,
                }
                
                # 只有当单位名称不为空时才创建
                if party_data['party_name']:
                    parties_data.append(party_data)
                
                party_index += 1
            
            # 批量创建签约主体
            if parties_data:
                ContractParty.objects.bulk_create([
                    ContractParty(**data) for data in parties_data
                ])
                logger.info(f'合同 {contract.contract_number} 创建了 {len(parties_data)} 个签约主体')
            
        except Exception as e:
            logger.warning(f'保存合同签约主体失败: {str(e)}')
            # 不抛出异常，允许合同创建继续
    
    @staticmethod
    def update_contract(contract, form_data, user):
        """
        更新合同
        
        Args:
            contract: 合同对象
            form_data: 表单数据
            user: 更新用户
            
        Returns:
            tuple: (contract对象, 是否成功, 错误消息)
        """
        try:
            with transaction.atomic():
                # 计算合同期限
                if form_data.get('start_date') and form_data.get('end_date'):
                    form_data['contract_period'] = calculate_contract_period(
                        form_data['start_date'],
                        form_data['end_date']
                    )
                
                # 更新合同
                for key, value in form_data.items():
                    setattr(contract, key, value)
                
                contract.save()
                
                return contract, True, None
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新合同失败: %s', str(e))
            return None, False, str(e)
    
    @staticmethod
    def submit_for_approval(contract, user):
        """
        提交合同审核
        
        Args:
            contract: 合同对象
            user: 提交用户
            
        Returns:
            tuple: (是否成功, 错误消息)
        """
        try:
            if contract.status != CONTRACT_STATUS_DRAFT:
                return False, '只有草稿状态的合同可以提交审核'
            
            # 更新状态为待审核
            contract.status = 'pending_review'
            contract.save()
            
            return True, None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('提交审核失败: %s', str(e))
            return False, str(e)
    
    @staticmethod
    def approve_contract(contract, user, approval_comment=''):
        """
        审核通过合同
        
        Args:
            contract: 合同对象
            user: 审核用户
            approval_comment: 审核意见
            
        Returns:
            tuple: (是否成功, 错误消息)
        """
        try:
            if contract.status not in ['pending_review', 'reviewing']:
                return False, '当前状态不允许审核'
            
            # 更新状态为已审核
            contract.status = 'approved'
            contract.save()
            
            # TODO: 记录审核历史
            
            return True, None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审核合同失败: %s', str(e))
            return False, str(e)
    
    @staticmethod
    def reject_contract(contract, user, rejection_reason=''):
        """
        拒绝合同审核
        
        Args:
            contract: 合同对象
            user: 审核用户
            rejection_reason: 拒绝原因
            
        Returns:
            tuple: (是否成功, 错误消息)
        """
        try:
            if contract.status not in ['pending_review', 'reviewing']:
                return False, '当前状态不允许拒绝'
            
            # 更新状态为草稿
            contract.status = CONTRACT_STATUS_DRAFT
            contract.save()
            
            # TODO: 记录审核历史
            
            return True, None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('拒绝合同失败: %s', str(e))
            return False, str(e)
    
    @staticmethod
    def get_contract_list(filters=None, ordering='-created_time'):
        """
        获取合同列表
        
        Args:
            filters: 筛选条件字典
            ordering: 排序字段
            
        Returns:
            QuerySet: 合同查询集
        """
        queryset = BusinessContract.objects.select_related(
            'client', 'project', 'created_by'
        ).all()
        
        if filters:
            # 应用筛选条件
            if filters.get('search'):
                search = filters['search']
                queryset = queryset.filter(
                    Q(contract_number__icontains=search) |
                    Q(contract_name__icontains=search) |
                    Q(client__name__icontains=search)
                )
            
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            
            if filters.get('contract_type'):
                queryset = queryset.filter(contract_type=filters['contract_type'])
            
            if filters.get('client_id'):
                queryset = queryset.filter(client_id=filters['client_id'])
            
            if filters.get('project_id'):
                queryset = queryset.filter(project_id=filters['project_id'])
        
        return queryset.order_by(ordering)

