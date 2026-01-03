"""
快递查询服务
支持快递100、菜鸟等主流快递查询API
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ExpressQueryService:
    """快递查询服务基类"""
    
    # 快递公司代码映射表（快递100标准）
    EXPRESS_COMPANY_CODES = {
        '顺丰': 'shunfeng',
        '顺丰速运': 'shunfeng',
        'SF': 'shunfeng',
        '圆通': 'yuantong',
        '圆通速递': 'yuantong',
        'YTO': 'yuantong',
        '申通': 'shentong',
        '申通快递': 'shentong',
        'STO': 'shentong',
        '中通': 'zhongtong',
        '中通快递': 'zhongtong',
        'ZTO': 'zhongtong',
        '韵达': 'yunda',
        '韵达速递': 'yunda',
        'YD': 'yunda',
        'EMS': 'ems',
        '中国邮政': 'ems',
        '邮政': 'ems',
        '德邦': 'debangwuliu',
        '德邦物流': 'debangwuliu',
        'DBL': 'debangwuliu',
        '百世': 'huitongkuaidi',
        '百世快递': 'huitongkuaidi',
        '汇通': 'huitongkuaidi',
        '汇通快运': 'huitongkuaidi',
        '京东': 'jd',
        '京东物流': 'jd',
        'JD': 'jd',
        '极兔': 'jitu',
        '极兔速递': 'jitu',
        'J&T': 'jitu',
    }
    
    @classmethod
    def get_company_code(cls, company_name: str) -> Optional[str]:
        """获取快递公司代码"""
        company_name = company_name.strip()
        # 直接匹配
        if company_name in cls.EXPRESS_COMPANY_CODES:
            return cls.EXPRESS_COMPANY_CODES[company_name]
        # 模糊匹配
        for key, code in cls.EXPRESS_COMPANY_CODES.items():
            if key in company_name or company_name in key:
                return code
        return None
    
    @classmethod
    def query_tracking(cls, company_name: str, tracking_number: str) -> Tuple[bool, Dict, str]:
        """
        查询快递物流信息
        
        Args:
            company_name: 快递公司名称
            tracking_number: 快递单号
            
        Returns:
            (success, data, message)
            success: 是否成功
            data: 物流信息数据
            message: 错误信息或成功信息
        """
        raise NotImplementedError("子类必须实现此方法")


class Kuaidi100Service(ExpressQueryService):
    """快递100查询服务"""
    
    API_URL = "https://poll.kuaidi100.com/poll/query.do"
    
    @classmethod
    def _load_config(cls) -> Tuple[str, str]:
        """
        加载快递100 API配置
        优先从后台API管理系统读取，如果没有则从settings读取
        
        Returns:
            (customer, key)
        """
        customer = ''
        key = ''
        config_source = 'fallback'
        
        # 优先从后台API管理系统读取配置
        try:
            from backend.apps.api_management.models import ExternalSystem, ApiInterface
            
            # 查找快递100外部系统
            kuaidi100_system = ExternalSystem.objects.filter(
                code='KUAIDI100',
                is_active=True
            ).first()
            
            if not kuaidi100_system:
                logger.warning('未找到快递100外部系统（code=KUAIDI100），将使用环境变量配置')
            else:
                logger.info(f'找到快递100外部系统: {kuaidi100_system.name} (ID: {kuaidi100_system.id})')
                # 查找实时快递查询API接口（KUAIDI100-00001）
                api_interface = ApiInterface.objects.filter(
                    code='KUAIDI100-00001',
                    external_system=kuaidi100_system,
                    is_active=True
                ).first()
                
                if not api_interface:
                    logger.warning('未找到快递100实时查询API接口（code=KUAIDI100-00001），将使用环境变量配置')
                elif not api_interface.is_active:
                    logger.warning('快递100实时查询API接口未启用，将使用环境变量配置')
                else:
                    logger.info(f'找到快递100实时查询API接口: {api_interface.name} (ID: {api_interface.id})')
                    if not api_interface.auth_config:
                        logger.warning('快递100实时查询API接口的auth_config为空，将使用环境变量配置')
                    else:
                        auth_config = api_interface.auth_config
                        customer = auth_config.get('customer', '')
                        key = auth_config.get('key', '')
                        config_source = 'api_management'
                        
                        logger.info(f'从后台API管理系统读取配置: customer={"已设置" if customer else "未设置"}, key={"已设置" if key else "未设置"}')
                        
                        if customer and key:
                            logger.info(f'✓ 从后台API管理系统加载快递100配置成功 (customer前4位: {customer[:4]}...)')
                            return customer, key
                        else:
                            logger.warning(f'快递100配置不完整: customer={"已设置" if customer else "未设置"}, key={"已设置" if key else "未设置"}，将使用环境变量配置')
        except Exception as e:
            logger.error(f'从后台API管理系统加载快递100配置失败: {str(e)}，将使用环境变量配置', exc_info=True)
        
        # 如果后台没有配置，则从环境变量读取（向后兼容）
        customer = customer or getattr(settings, 'KUAIDI100_CUSTOMER', '')
        key = key or getattr(settings, 'KUAIDI100_KEY', '')
        
        if customer and key:
            logger.info(f'从环境变量加载快递100配置成功，来源={"后台API管理" if config_source == "api_management" else "环境变量"}')
        
        return customer, key
    
    @classmethod
    def query_tracking(cls, company_name: str, tracking_number: str) -> Tuple[bool, Dict, str]:
        """
        查询快递物流信息（快递100 API）
        
        快递100 API文档：https://www.kuaidi100.com/openapi/api_post.shtml
        """
        try:
            # 获取配置（优先从后台API管理系统读取）
            customer, key = cls._load_config()
            
            if not customer or not key:
                logger.error("快递100 API配置未设置，请配置KUAIDI100_CUSTOMER和KUAIDI100_KEY，或在后台API管理中配置")
                return False, {}, "快递100 API配置未设置（请检查后台API管理中的快递100配置，或联系管理员）"
            
            logger.debug(f"使用快递100配置: customer长度={len(customer)}, key长度={len(key) if key else 0}")
            
            # 获取快递公司代码
            # 优先从ExpressCompany模型获取代码
            company_code = None
            try:
                from backend.apps.delivery_customer.models import ExpressCompany
                express_company_obj = ExpressCompany.objects.filter(
                    name=company_name,
                    is_active=True
                ).first()
                if express_company_obj and express_company_obj.code:
                    company_code = express_company_obj.code
                    logger.debug(f"从ExpressCompany模型获取快递公司代码: {company_name} -> {company_code}")
            except Exception as e:
                logger.warning(f"从ExpressCompany模型获取快递公司代码失败: {str(e)}")
            
            # 如果模型中没有，则使用映射表
            if not company_code:
                company_code = cls.get_company_code(company_name)
            
            if not company_code:
                return False, {}, f"不支持的快递公司：{company_name}（请检查快递公司名称是否正确，或在后台快递公司管理中配置）"
            
            # 构建请求参数
            param = {
                'com': company_code,
                'num': tracking_number,
            }
            
            # 签名计算
            import hashlib
            sign_str = json.dumps(param, separators=(',', ':')) + key + customer
            sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
            
            data = {
                'customer': customer,
                'sign': sign,
                'param': json.dumps(param, separators=(',', ':')),
            }
            
            # 发送请求
            logger.debug(f"发送快递100 API请求: URL={cls.API_URL}, company_code={company_code}, tracking_number={tracking_number[:4]}...{tracking_number[-4:] if len(tracking_number) > 8 else ''}")
            response = requests.post(cls.API_URL, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            api_status = result.get('status', '')
            api_message = result.get('message', '')
            logger.info(f"快递100 API响应: status={api_status}, message={api_message[:200]}")
            
            # 检查结果
            if api_status == '200':
                # 成功
                logistics_data = {
                    'company': company_name,
                    'company_code': company_code,
                    'tracking_number': tracking_number,
                    'status': result.get('state', '0'),  # 0-在途，1-揽收，2-疑难，3-已签收，4-退签，5-派件，6-退回，7-转投，10-待清关，11-清关中，12-已清关，13-清关异常，14-收件人拒签
                    'status_text': cls._get_status_text(result.get('state', '0')),
                    'tracks': result.get('data', []),
                    'query_time': timezone.now().isoformat(),
                }
                return True, logistics_data, "查询成功"
            else:
                # 失败
                error_msg = result.get('message', '查询失败')
                error_code = result.get('status', '')
                
                # 提供更友好的错误提示
                if error_code == '400':
                    if '没该功能权限' in error_msg or '权限' in error_msg:
                        # 检查配置来源，提供更具体的提示
                        customer_check, key_check = cls._load_config()
                        config_source = '后台API管理' if customer_check and key_check else '环境变量'
                        error_msg = f"{error_msg}（提示：快递100返回'没该功能权限'错误。可能原因：1) 快递100账户未开通实时查询功能，请联系快递100客服开通；2) customer或key配置不正确，当前使用{config_source}配置，请检查后台API管理中KUAIDI100-00001接口的auth_config；3) 账户类型不支持实时查询，需要企业版账户）"
                    elif '单号格式' in error_msg or '格式' in error_msg:
                        error_msg = f"{error_msg}（提示：请检查快递单号格式是否正确）"
                    elif '不支持' in error_msg:
                        error_msg = f"{error_msg}（提示：请检查快递公司名称是否正确，或在后台快递公司管理中配置正确的公司代码）"
                
                logger.warning(f"快递100 API查询失败: status={error_code}, message={error_msg}, company={company_name}, number={tracking_number}")
                return False, {}, error_msg
                
        except requests.exceptions.RequestException as e:
            logger.error(f"快递100 API请求失败: {str(e)}")
            return False, {}, f"API请求失败：{str(e)}"
        except Exception as e:
            logger.error(f"快递100 API查询异常: {str(e)}")
            return False, {}, f"查询异常：{str(e)}"
    
    @classmethod
    def _get_status_text(cls, status_code: str) -> str:
        """获取状态文本"""
        status_map = {
            '0': '在途',
            '1': '揽收',
            '2': '疑难',
            '3': '已签收',
            '4': '退签',
            '5': '派件',
            '6': '退回',
            '7': '转投',
            '10': '待清关',
            '11': '清关中',
            '12': '已清关',
            '13': '清关异常',
            '14': '收件人拒签',
        }
        return status_map.get(status_code, '未知状态')


class ExpressQueryServiceFactory:
    """快递查询服务工厂"""
    
    @staticmethod
    def get_service(service_type: str = 'kuaidi100') -> ExpressQueryService:
        """
        获取快递查询服务实例
        
        Args:
            service_type: 服务类型，默认为'kuaidi100'
            
        Returns:
            快递查询服务实例
        """
        if service_type == 'kuaidi100':
            return Kuaidi100Service()
        else:
            raise ValueError(f"不支持的服务类型：{service_type}")


def query_express_tracking(company_name: str, tracking_number: str, service_type: str = 'kuaidi100') -> Tuple[bool, Dict, str]:
    """
    查询快递物流信息（便捷函数）
    
    Args:
        company_name: 快递公司名称
        tracking_number: 快递单号
        service_type: 服务类型，默认为'kuaidi100'
        
    Returns:
        (success, data, message)
    """
    service = ExpressQueryServiceFactory.get_service(service_type)
    return service.query_tracking(company_name, tracking_number)

