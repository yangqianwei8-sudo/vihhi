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
    def query_tracking(cls, company_name: str, tracking_number: str) -> Tuple[bool, Dict, str]:
        """
        查询快递物流信息（快递100 API）
        
        快递100 API文档：https://www.kuaidi100.com/openapi/api_post.shtml
        """
        try:
            # 获取配置
            customer = getattr(settings, 'KUAIDI100_CUSTOMER', '')
            key = getattr(settings, 'KUAIDI100_KEY', '')
            
            if not customer or not key:
                logger.warning("快递100 API配置未设置，请配置KUAIDI100_CUSTOMER和KUAIDI100_KEY")
                return False, {}, "快递100 API配置未设置"
            
            # 获取快递公司代码
            company_code = cls.get_company_code(company_name)
            if not company_code:
                return False, {}, f"不支持的快递公司：{company_name}"
            
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
            response = requests.post(cls.API_URL, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查结果
            if result.get('status') == '200':
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

