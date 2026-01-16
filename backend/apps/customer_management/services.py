"""
客户成功模块服务类
"""
import requests
import hashlib
import time
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class QixinbaoAPIService:
    """启信宝API服务类"""
    
    def __init__(self):
        # 优先从后台API管理系统读取配置
        self._load_config_from_api_management()
        
        # 如果后台没有配置，则从环境变量读取（向后兼容）
        if not self.app_key or not self.app_secret:
            self.app_key = self.app_key or getattr(settings, 'QIXINBAO_APP_KEY', '')
            self.app_secret = self.app_secret or getattr(settings, 'QIXINBAO_APP_SECRET', '')
            self.api_base_url = self.api_base_url or getattr(settings, 'QIXINBAO_API_BASE_URL', 'https://api.qixin.com')
            self.timeout = self.timeout or getattr(settings, 'QIXINBAO_API_TIMEOUT', 10)
        
        # 记录配置状态（用于调试）
        if self.app_key and self.app_secret:
            logger.info(f'启信宝API配置已加载: app_key={self.app_key[:20]}..., base_url={self.api_base_url}, 来源={"后台API管理" if hasattr(self, "_config_source") and self._config_source == "api_management" else "环境变量"}')
        else:
            logger.warning('启信宝API配置未完整: app_key={}, app_secret={}'.format(
                '已配置' if self.app_key else '未配置',
                '已配置' if self.app_secret else '未配置'
            ))
    
    def _load_config_from_api_management(self):
        """从后台API管理系统加载配置"""
        try:
            from backend.apps.api_management.models import ExternalSystem, ApiInterface
            
            # 查找启信宝外部系统
            qixinbao_system = ExternalSystem.objects.filter(
                code='QIXINBAO',
                is_active=True
            ).first()
            
            if qixinbao_system:
                # 查找任意一个激活的API接口（所有接口使用相同的认证配置）
                api_interface = ApiInterface.objects.filter(
                    external_system=qixinbao_system,
                    is_active=True
                ).first()
                
                if api_interface and api_interface.auth_config:
                    auth_config = api_interface.auth_config
                    self.app_key = auth_config.get('app_key', '')
                    self.app_secret = auth_config.get('app_secret', '')
                    self.api_base_url = qixinbao_system.base_url
                    self.timeout = api_interface.timeout or 10
                    self._config_source = "api_management"
                    logger.info('从后台API管理系统加载启信宝配置成功')
                    return
            
            # 如果未找到配置，初始化默认值
            self.app_key = ''
            self.app_secret = ''
            self.api_base_url = 'https://api.qixin.com'
            self.timeout = 10
            self._config_source = "fallback"
            
        except Exception as e:
            logger.warning(f'从后台API管理系统加载启信宝配置失败: {str(e)}，将使用环境变量配置')
            self.app_key = ''
            self.app_secret = ''
            self.api_base_url = 'https://api.qixin.com'
            self.timeout = 10
            self._config_source = "fallback"
    
    def _generate_sign(self, appkey: str, timestamp: str, secret_key: str) -> str:
        """
        生成签名
        加密规则：appkey + timestamp + secret_key 组成的32位md5加密的小写字符串
        """
        sign_str = f'{appkey}{timestamp}{secret_key}'
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
        return sign
    
    def _make_request(self, endpoint: str, query_params: Dict) -> Optional[Dict]:
        """
        发送API请求（GET方式）
        
        根据启信宝API文档：
        - 请求方式：HTTP/HTTPS GET
        - Headers需要：Auth-Version, appkey, timestamp, sign
        - Query参数：keyword等业务参数
        """
        if not self.app_key or not self.app_secret:
            logger.warning('启信宝API配置未设置，请配置QIXINBAO_APP_KEY和QIXINBAO_APP_SECRET')
            return None
        
        try:
            # 生成时间戳（精确到毫秒）
            timestamp = str(int(time.time() * 1000))
            
            # 生成签名
            sign = self._generate_sign(self.app_key, timestamp, self.app_secret)
            
            # 设置请求头
            headers = {
                'Auth-Version': '2.0',
                'appkey': self.app_key,
                'timestamp': timestamp,
                'sign': sign
            }
            
            # 发送GET请求
            url = f'{self.api_base_url}{endpoint}'
            response = requests.get(
                url,
                params=query_params,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 检查返回状态
            status = result.get('status', '')
            message = result.get('message', '未知错误')
            logger.info(f'启信宝API响应: status={status}, message={message}')
            
            if status == '200':
                data = result.get('data')
                logger.info(f'启信宝API返回数据: {data}')
                return data
            else:
                # 根据错误码提供更详细的错误信息
                error_info = {
                    'status': status,
                    'message': message
                }
                
                # 常见错误码说明
                if status == '113':
                    error_info['detail'] = '账户未激活，请在启信宝开放平台激活账户'
                elif status == '104':
                    error_info['detail'] = 'IP白名单未配置，请在启信宝开放平台配置API IP白名单'
                elif status == '101':
                    error_info['detail'] = 'AppKey无效，请检查API密钥配置'
                elif status == '102':
                    error_info['detail'] = '账户余额不足，请充值'
                elif status == '214':
                    error_info['detail'] = '接口调用鉴权失败，请检查签名算法'
                
                logger.warning(f'启信宝API返回错误: {error_info}')
                # 返回错误信息，让调用方可以显示更详细的错误
                return {'error': error_info}
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f'启信宝API请求失败: {error_msg}')
            # 如果是连接错误，可能是IP白名单未配置
            if '104' in error_msg or 'IP' in error_msg or '白名单' in error_msg:
                logger.error('可能的原因：IP白名单未配置，请在启信宝开放平台配置API IP白名单')
            return None
        except Exception as e:
            logger.error(f'启信宝API处理异常: {str(e)}', exc_info=True)
            return None
    
    def verify_credit_code(self, credit_code: str, company_name: str = None) -> Dict:
        """
        验证统一社会信用代码
        
        使用启信宝"企业模糊搜索"API（1.31）进行验证
        
        Args:
            credit_code: 统一社会信用代码（18位）
            company_name: 公司名称（可选，用于验证匹配）
        
        Returns:
            {
                'valid': bool,  # 是否有效
                'matched': bool,  # 是否与公司名称匹配（如果提供了公司名称）
                'company_info': dict,  # 企业信息
                'message': str  # 消息
            }
        """
        if not credit_code or len(credit_code) != 18:
            return {
                'valid': False,
                'matched': False,
                'company_info': None,
                'message': '统一社会信用代码必须为18位'
            }
        
        # 优先使用公司名称搜索（如果提供）
        search_keyword = company_name if company_name else credit_code
        
        # 调用启信宝"企业模糊搜索"API
        # 接口地址：https://api.qixin.com/APIService/v2/search/advSearch
        query_params = {
            'keyword': search_keyword,
            'matchType': 'ename,credit_no',  # 匹配公司名称和统一社会信用代码
        }
        
        data = self._make_request('/APIService/v2/search/advSearch', query_params)
        
        if data is None:
            # API调用失败，返回格式验证结果
            return {
                'valid': self._validate_format(credit_code),
                'matched': False,
                'company_info': None,
                'message': 'API调用失败，仅进行格式验证'
            }
        
        # 检查是否返回了错误信息
        if isinstance(data, dict) and 'error' in data:
            error_info = data['error']
            error_message = error_info.get('detail', error_info.get('message', '未知错误'))
            logger.warning(f'启信宝API返回错误: {error_info}')
            return {
                'valid': self._validate_format(credit_code),
                'matched': False,
                'company_info': None,
                'message': f'API调用失败：{error_message}，仅进行格式验证'
            }
        
        # 解析返回数据
        items = data.get('items', []) if isinstance(data, dict) else []
        if not items:
            return {
                'valid': False,
                'matched': False,
                'company_info': None,
                'message': '未找到匹配的企业信息'
            }
        
        # 查找匹配的统一社会信用代码
        matched_company = None
        for item in items:
            item_credit_no = item.get('credit_no', '')
            if item_credit_no and item_credit_no.upper() == credit_code.upper():
                matched_company = item
                break
        
        if not matched_company:
            # 如果没找到完全匹配的，返回第一个结果（可能是名称匹配）
            matched_company = items[0]
            return {
                'valid': False,
                'matched': False,
                'company_info': matched_company,
                'message': '未找到该统一社会信用代码对应的企业'
            }
        
        # 检查公司名称匹配
        found_name = matched_company.get('name', '')
        matched = False
        if company_name and found_name:
            # 简单匹配：检查公司名称是否包含在返回的名称中，或反之
            matched = (company_name in found_name) or (found_name in company_name)
        
        message = '验证通过'
        if company_name:
            if matched:
                message += '，公司名称匹配'
            else:
                message += '，但公司名称不匹配，请确认'
        
        return {
            'valid': True,
            'matched': matched,
            'company_info': matched_company,
            'message': message
        }
    
    def _validate_format(self, credit_code: str) -> bool:
        """验证统一社会信用代码格式"""
        if not credit_code or len(credit_code) != 18:
            return False
        
        # 统一社会信用代码格式：18位，前17位为数字或大写字母，最后一位为数字或大写字母
        import re
        pattern = r'^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$'
        return bool(re.match(pattern, credit_code))
    
    def _parse_registered_capital(self, capital_str: str) -> Optional[float]:
        """
        解析注册资本字符串，转换为万元数值
        
        支持的格式：
        - "6500 万人民币" -> 6500.0
        - "1203.2528 万美元" -> 1203.2528 * 汇率（约7.0） = 8422.77
        - "1000 万元" -> 1000.0
        
        Args:
            capital_str: 注册资本字符串，例如 "6500 万人民币"
        
        Returns:
            注册资本数值（万元），如果解析失败返回None
        """
        if not capital_str or capital_str == '-':
            return None
        
        import re
        try:
            # 提取数字部分
            match = re.search(r'([\d.]+)', capital_str)
            if not match:
                return None
            
            value = float(match.group(1))
            
            # 检查货币单位
            if '美元' in capital_str or 'USD' in capital_str.upper():
                # 美元转人民币，假设汇率为7.0（实际应该使用实时汇率）
                value = value * 7.0
            elif '港币' in capital_str or 'HKD' in capital_str.upper():
                # 港币转人民币，假设汇率为0.9
                value = value * 0.9
            elif '欧元' in capital_str or 'EUR' in capital_str.upper():
                # 欧元转人民币，假设汇率为7.5
                value = value * 7.5
            
            # 检查单位（万、元）
            if '万' in capital_str:
                # 已经是万元单位
                return value
            else:
                # 是元单位，转换为万元
                return value / 10000.0
                
        except (ValueError, AttributeError) as e:
            logger.warning(f'解析注册资本失败: {capital_str}, 错误: {str(e)}')
            return None
    
    def search_company(self, keyword: str, match_type: str = None, region: str = None, skip: int = 0) -> Optional[Dict]:
        """
        企业模糊搜索
        
        使用启信宝"企业模糊搜索"API（1.31）
        
        Args:
            keyword: 企业相关关键字，输入字数大于等于2个或以上
            match_type: 匹配类型（可选），多个类型使用,分隔
            region: 地区编码（可选）
            skip: 跳过条目数（默认为0，单页返回10条数据）
        
        Returns:
            搜索结果字典，包含items（企业列表）、total（总数）、num（当前返回数）
            如果返回错误，会包含error字段
        """
        if not keyword or len(keyword) < 2:
            logger.warning('搜索关键字必须至少2个字符')
            return None
        
        query_params = {
            'keyword': keyword,
        }
        
        if match_type:
            query_params['matchType'] = match_type
        if region:
            query_params['region'] = region
        if skip > 0:
            query_params['skip'] = skip
        
        result = self._make_request('/APIService/v2/search/advSearch', query_params)
        
        # 检查是否返回了错误信息
        if result and isinstance(result, dict) and 'error' in result:
            return result
        
        return result
    
    def get_company_detail(self, company_id: str = None, credit_code: str = None, company_name: str = None) -> Optional[Dict]:
        """
        获取企业详细信息
        
        使用启信宝"企业详情"API获取完整企业信息，包括：
        - 注册资本（reg_capital）
        - 联系电话（phone）
        - 邮箱（email）
        - 地址（address）
        
        Args:
            company_id: 企业ID（启信宝返回的企业编号）
            credit_code: 统一社会信用代码
            company_name: 企业全名
        
        Returns:
            企业详细信息字典，如果API调用失败返回None
        """
        # 确定查询参数：优先使用企业名称或统一社会信用代码（工商照面API不支持企业ID）
        # 注意：启信宝"工商照面"API只支持企业全名/注册号/统一社会信用代码，不支持企业ID
        query_param = None
        if company_name:
            query_param = company_name
        elif credit_code:
            query_param = credit_code
        # 企业ID不支持，跳过
        # elif company_id:
        #     query_param = company_id
        
        if not query_param:
            logger.warning('无法确定查询参数（企业ID、统一社会信用代码或企业名称），无法查询企业详情')
            return None
        
        # 调用启信宝"工商照面"API (1.41)
        # 接口地址：https://api.qixin.com/APIService/enterprise/getBasicInfo
        # 请求方式：GET
        # 请求参数：keyword（企业全名/注册号/统一社会信用代码）
        # API文档：https://data.qixin.com/api-detail?from=navigation&categoryId=27C4602EBB38429EK08QR7fy&apiId=1.41
        
        try:
            query_params = {
                'keyword': query_param
            }
            
            # 使用正确的API路径
            api_path = '/APIService/enterprise/getBasicInfo'
            
            result = self._make_request(api_path, query_params)
            
            if not result:
                logger.warning('企业详情API调用失败，返回空结果')
                return None
            
            # 检查是否返回了错误信息
            if result and isinstance(result, dict) and 'error' in result:
                logger.warning(f'获取企业详情失败: {result["error"]}')
                return None
            
            if result is None:
                logger.warning(f'获取企业详情失败: API返回空结果')
                return None
            
            # 解析并标准化返回的数据字段
            # API返回的字段名映射到前端需要的字段名
            normalized_data = {
                # 基本信息
                'id': result.get('id'),
                'name': result.get('name'),
                'credit_no': result.get('creditNo'),
                'reg_no': result.get('regNo'),
                
                # 法定代表人
                'legal_representative': result.get('operName'),
                
                # 成立日期
                'established_date': result.get('startDate'),
                
                # 注册资本（需要解析 "6500 万人民币" 格式）
                'reg_capital': result.get('registCapi'),
                'reg_capital_value': self._parse_registered_capital(result.get('registCapi')),
                
                # 地址
                'address': result.get('address'),
                
                # 联系电话和邮箱（工商照面API不返回，需要使用其他API）
                'phone': result.get('phone'),  # 可能为空
                'email': result.get('email'),  # 可能为空
                
                # 其他字段
                'status': result.get('status'),
                'new_status': result.get('new_status'),
                'scope': result.get('scope'),  # 经营范围
                'econ_kind': result.get('econKind'),  # 企业类型
                'belong_org': result.get('belongOrg'),  # 所属工商局
            }
            
            # 调用企业联系方式API (1.51) 获取联系电话和邮箱
            # 接口地址：https://api.qixin.com/APIService/enterprise/getContactInfo
            # API文档：https://data.qixin.com/api-detail?categoryId=27C4602EBB38429EK08QR7fy&apiId=1.51
            try:
                contact_result = self._make_request('/APIService/enterprise/getContactInfo', query_params)
                if contact_result and isinstance(contact_result, dict) and 'error' not in contact_result:
                    # 更新联系电话和邮箱
                    if contact_result.get('telephone'):
                        normalized_data['phone'] = contact_result.get('telephone')
                    if contact_result.get('email'):
                        normalized_data['email'] = contact_result.get('email')
                    # 如果联系方式API返回的地址更详细，也可以更新
                    if contact_result.get('address') and not normalized_data.get('address'):
                        normalized_data['address'] = contact_result.get('address')
                    logger.info(f'成功获取企业联系方式: 电话={normalized_data.get("phone")}, 邮箱={normalized_data.get("email")}')
                else:
                    logger.warning(f'企业联系方式API调用失败或返回错误: {contact_result}')
            except Exception as e:
                logger.warning(f'调用企业联系方式API异常: {str(e)}', exc_info=True)
                # 联系方式API失败不影响主流程，继续返回其他数据
            
            logger.info(f'获取企业详情成功: {query_param}')
            return normalized_data
            
        except Exception as e:
            logger.error(f'获取企业详情异常: {str(e)}', exc_info=True)
            return None
    
    def get_legal_risk_info(self, company_id: str = None, credit_code: str = None, company_name: str = None) -> Dict:
        """
        获取企业法律风险信息
        
        使用启信宝"整体诉讼"API (6.6) 获取：
        - 司法案件数量（立案信息数量 lian）
        - 被执行人数量（执行公告信息数量 zxgg）
        - 终本案件数量（terminationCaseResult）
        - 限制高消费数量（consumerResult）
        
        API文档：https://data.qixin.com/api-detail?categoryId=9738cf87422f43cba1850e00bc28f8c9&apiId=6.6
        
        Args:
            company_id: 企业ID（启信宝返回的企业编号）
            credit_code: 统一社会信用代码
            company_name: 企业全名
        
        Returns:
            {
                'litigation_count': int,  # 司法案件数量（立案信息数量）
                'executed_person_count': int,  # 被执行人数量（执行公告信息数量）
                'final_case_count': int,  # 终本案件数量
                'consumption_limit_count': int,  # 限制高消费数量
                'risk_level': str,  # 自动判断的风险等级
                'risk_level_label': str,  # 风险等级标签
            }
        """
        # 确定查询参数：优先使用企业名称或统一社会信用代码
        query_name = None
        if company_name:
            query_name = company_name
        elif credit_code:
            query_name = credit_code
        elif company_id:
            # 如果有企业ID但没有名称，先通过搜索获取企业信息
            search_result = self.search_company(company_id)
            if search_result and 'items' in search_result and search_result['items']:
                query_name = search_result['items'][0].get('name') or search_result['items'][0].get('credit_no')
        
        if not query_name:
            logger.warning('无法确定查询参数（企业名称或统一社会信用代码），无法查询法律风险信息')
            return {
                'litigation_count': 0,
                'executed_person_count': 0,
                'final_case_count': 0,
                'consumption_limit_count': 0,
                'risk_level': 'unknown',
                'risk_level_label': '未知',
            }
        
        # 调用启信宝"整体诉讼"API
        # 接口地址：https://api.qixin.com/APIService/sumLawsuit/sumLawsuit
        # 请求方式：GET
        # 请求参数：name（企业全名/统一社会信用代码）
        
        legal_risk_data = {
            'litigation_count': 0,
            'executed_person_count': 0,
            'final_case_count': 0,
            'consumption_limit_count': 0,
            'api_error': None,  # 记录API错误信息
        }
        
        try:
            # 构建查询参数
            query_params = {
                'name': query_name
            }
            
            # 调用API
            result = self._make_request('/APIService/sumLawsuit/sumLawsuit', query_params)
            
            # _make_request返回的可能是：
            # 1. data字段（当status='200'时）
            # 2. {'error': error_info}（当有错误时）
            # 3. None（当请求失败时）
            
            if result is None:
                logger.warning(f'API调用失败: {query_name}（网络错误或请求异常）')
                legal_risk_data['api_error'] = {
                    'type': 'network_error',
                    'message': 'API调用失败，可能是网络问题或IP白名单未配置'
                }
            elif isinstance(result, dict) and 'error' in result:
                # API返回了错误信息
                error_info = result['error']
                status = error_info.get('status', '')
                message = error_info.get('message', '未知错误')
                detail = error_info.get('detail', '')
                logger.warning(f'API返回错误: status={status}, message={message}, detail={detail}')
                legal_risk_data['api_error'] = {
                    'type': 'api_error',
                    'status': status,
                    'message': message,
                    'detail': detail
                }
            elif isinstance(result, dict):
                # 成功返回，result就是data字段
                # 立案信息数量（司法案件数量）
                legal_risk_data['litigation_count'] = int(result.get('lian', 0) or 0)
                # 执行公告信息数量（被执行人数量）
                legal_risk_data['executed_person_count'] = int(result.get('zxgg', 0) or 0)
                # 终本案件数量
                legal_risk_data['final_case_count'] = int(result.get('terminationCaseResult', 0) or 0)
                # 限制高消费数量
                legal_risk_data['consumption_limit_count'] = int(result.get('consumerResult', 0) or 0)
                
                logger.info(f'获取法律风险信息成功: {query_name}, 数据: {legal_risk_data}')
            else:
                logger.warning(f'API返回数据格式错误: {type(result)}')
                legal_risk_data['api_error'] = {
                    'type': 'format_error',
                    'message': f'API返回数据格式错误: {type(result)}'
                }
                
        except Exception as e:
            logger.error(f'获取法律风险信息失败: {str(e)}', exc_info=True)
            legal_risk_data['api_error'] = {
                'type': 'exception',
                'message': str(e)
            }
        
        # 根据规则自动判断风险等级
        risk_level, risk_level_label = self._calculate_risk_level(
            legal_risk_data['consumption_limit_count'],
            legal_risk_data['final_case_count'],
            legal_risk_data['executed_person_count'],
            legal_risk_data['litigation_count']
        )
        
        legal_risk_data['risk_level'] = risk_level
        legal_risk_data['risk_level_label'] = risk_level_label
        
        return legal_risk_data
    
    def _calculate_risk_level(self, consumption_limit_count: int, final_case_count: int, 
                              executed_person_count: int, litigation_count: int) -> tuple:
        """
        根据法律风险数据自动计算风险等级
        
        规则：
        1. 限制高消费 > 0 → 高风险
        2. 终本案件 > 0 → 中高风险
        3. 被执行人 > 0 → 中风险
        4. 司法案件 > 0（但没有上述情况）→ 中低风险
        5. 没有任何情况 → 低风险
        
        Returns:
            (risk_level, risk_level_label) 元组
        """
        if consumption_limit_count > 0:
            return ('high', '高风险')
        elif final_case_count > 0:
            return ('medium_high', '中高风险')
        elif executed_person_count > 0:
            return ('medium', '中风险')
        elif litigation_count > 0:
            return ('medium_low', '中低风险')
        else:
            return ('low', '低风险')
    
    def get_execution_records(self, company_id: str = None, credit_code: str = None, company_name: str = None) -> list:
        """
        获取被执行详细记录列表
        
        使用启信宝"被执行企业"API (17.5) 获取被执行详细记录
        API文档：https://data.qixin.com/api-detail?categoryId=9738cf87422f43cba1850e00bc28f8c9&apiId=17.5
        
        接口地址：https://api.qixin.com/APIService/execution/getExecutedpersonListByName
        请求方式：HTTP/HTTPS GET
        请求参数：name（企业全名/统一社会信用代码）
        
        Args:
            company_id: 企业ID（启信宝返回的企业编号）
            credit_code: 统一社会信用代码
            company_name: 企业全名
        
        Returns:
            [
                {
                    'case_number': str,  # 案号
                    'execution_status': str,  # 执行状态 (pending/executing/completed/terminated/unknown)
                    'execution_court': str,  # 执行法院
                    'filing_date': str,  # 立案日期 (YYYY-MM-DD)
                    'execution_amount': str,  # 执行金额
                },
                ...
            ]
        """
        # 确定查询参数：优先使用企业名称或统一社会信用代码
        query_name = None
        if company_name:
            query_name = company_name
        elif credit_code:
            query_name = credit_code
        elif company_id:
            # 如果有企业ID但没有名称，先通过搜索获取企业信息
            search_result = self.search_company(company_id)
            if search_result and 'items' in search_result and search_result['items']:
                query_name = search_result['items'][0].get('name') or search_result['items'][0].get('credit_no')
        
        if not query_name:
            logger.warning('无法确定查询参数（企业名称或统一社会信用代码），无法查询被执行记录')
            return []
        
        records = []
        
        # 使用正确的API接口路径（根据启信宝API文档17.5）
        endpoint = '/APIService/execution/getExecutedpersonListByName'
        
        try:
            # 构建查询参数
            query_params = {
                'name': query_name
            }
            
            # 调用API
            result = self._make_request(endpoint, query_params)
            
            if result is None:
                logger.warning(f'API调用失败: {query_name}（网络错误或请求异常）')
                return []
            
            if isinstance(result, dict) and 'error' in result:
                error_info = result.get('error', {})
                logger.warning(f'API返回错误: {error_info.get("message", "未知错误")}')
                return []
            
            # 解析返回数据
            # 根据启信宝API的常见格式，数据可能在以下位置：
            # 1. result 直接是列表
            # 2. result['list'] 或 result['data'] 或 result['items']
            # 3. result['result'] 或 result['records']
            
            data_list = None
            if isinstance(result, list):
                data_list = result
            elif isinstance(result, dict):
                # 尝试多个可能的字段名
                for key in ['list', 'data', 'items', 'result', 'records', 'executionRecords', 'executionList', 'executedList']:
                    if key in result and isinstance(result[key], list):
                        data_list = result[key]
                        break
                
                # 如果仍然没有找到列表，检查result本身是否包含记录数据
                if data_list is None and result:
                    # 可能result本身就是一条记录（单个对象）
                    if isinstance(result, dict) and any(k in result for k in ['case_number', 'caseNumber', 'execution_id', 'executionId']):
                        data_list = [result]
            
            if data_list and len(data_list) > 0:
                logger.info(f'成功获取被执行记录: {len(data_list)} 条，使用接口: {endpoint}')
                
                # 解析每条记录
                for item in data_list:
                    record = self._parse_execution_record(item)
                    if record:
                        records.append(record)
            else:
                logger.info(f'未获取到被执行记录: {query_name}（API返回数据为空）')
                    
        except Exception as e:
            logger.error(f'获取被执行记录异常: {str(e)}', exc_info=True)
            return []
        
        return records
    
    def _parse_execution_record(self, item: dict) -> Optional[dict]:
        """
        解析单条被执行记录
        
        根据启信宝API返回的数据格式，解析并标准化字段
        """
        try:
            # 提取案号（可能的字段名：caseNumber, case_number, caseNo, case_no, anhao）
            case_number = (
                item.get('caseNumber') or 
                item.get('case_number') or 
                item.get('caseNo') or 
                item.get('case_no') or 
                item.get('anhao') or 
                item.get('caseCode') or
                ''
            )
            
            # 提取立案日期（可能的字段名：filingDate, filing_date, caseDate, case_date, larq）
            filing_date = (
                item.get('filingDate') or 
                item.get('filing_date') or 
                item.get('caseDate') or 
                item.get('case_date') or 
                item.get('larq') or
                item.get('publishDate') or
                item.get('publish_date') or
                ''
            )
            
            # 格式化日期（如果是时间戳，转换为YYYY-MM-DD格式）
            if filing_date:
                try:
                    # 如果是时间戳（毫秒）
                    if filing_date.isdigit() and len(filing_date) == 13:
                        from datetime import datetime
                        filing_date = datetime.fromtimestamp(int(filing_date) / 1000).strftime('%Y-%m-%d')
                    # 如果是时间戳（秒）
                    elif filing_date.isdigit() and len(filing_date) == 10:
                        from datetime import datetime
                        filing_date = datetime.fromtimestamp(int(filing_date)).strftime('%Y-%m-%d')
                    # 如果已经是日期格式，尝试标准化
                    elif len(filing_date) >= 10:
                        filing_date = filing_date[:10]  # 取前10个字符（YYYY-MM-DD）
                except:
                    pass
            
            # 提取执行法院（可能的字段名：executionCourt, execution_court, court, courtName, zxfy）
            execution_court = (
                item.get('executionCourt') or 
                item.get('execution_court') or 
                item.get('court') or 
                item.get('courtName') or 
                item.get('court_name') or 
                item.get('zxfy') or
                item.get('executeCourt') or
                ''
            )
            
            # 提取执行金额（可能的字段名：amount, executionAmount, execution_amount, executionTarget, execution_target）
            # 注意：API 17.5返回的amount字段是字符串格式的数字（单位：元）
            execution_amount = '0'
            
            # 优先使用amount字段（API 17.5直接返回）
            amount_value = item.get('amount') or item.get('executionAmount') or item.get('execution_amount')
            
            if amount_value:
                try:
                    # 如果已经是数字字符串，直接使用
                    execution_amount = str(float(amount_value))
                except (ValueError, TypeError):
                    # 如果不是数字，尝试从执行标的中提取
                    execution_target = (
                        item.get('executionTarget') or 
                        item.get('execution_target') or 
                        item.get('zxbd') or
                        item.get('targetAmount') or
                        str(amount_value)
                    )
                    
                    if execution_target:
                        import re
                        # 提取数字
                        numbers = re.findall(r'\d+\.?\d*', execution_target)
                        if numbers:
                            try:
                                amount = float(numbers[0])
                                # 如果包含"万"，乘以10000
                                if '万' in execution_target:
                                    amount = amount * 10000
                                # 如果包含"亿"，乘以100000000
                                elif '亿' in execution_target:
                                    amount = amount * 100000000
                                execution_amount = str(amount)
                            except (ValueError, TypeError):
                                pass
            
            # 提取执行状态（可能的字段名：status, executionStatus, execution_status, state）
            # 注意：API 17.5返回的status字段可能是 '-'（未执行）或 '1'（已执行/已终止）
            # 如果没有，默认为unknown
            execution_status_raw = (
                item.get('executionStatus') or 
                item.get('execution_status') or 
                item.get('status') or 
                item.get('state') or
                'unknown'
            )
            
            # 标准化执行状态值
            status_mapping = {
                # 中文状态
                '待执行': 'pending',
                '执行中': 'executing',
                '已执行': 'completed',
                '已终止': 'terminated',
                '终止': 'terminated',
                '完成': 'completed',
                # 英文状态
                'pending': 'pending',
                'executing': 'executing',
                'completed': 'completed',
                'terminated': 'terminated',
                # API 17.5返回的状态值
                '-': 'executing',  # 未执行/执行中
                '0': 'executing',  # 执行中
                '1': 'completed',  # 已执行/已终止
                '2': 'terminated',  # 已终止
            }
            execution_status = status_mapping.get(execution_status_raw, 'unknown')
            
            return {
                'case_number': case_number,
                'execution_status': execution_status,
                'execution_court': execution_court,
                'filing_date': filing_date,
                'execution_amount': execution_amount,
            }
            
        except Exception as e:
            logger.error(f'解析被执行记录失败: {str(e)}', exc_info=True)
            return None
    
    def get_company_info_by_name(self, company_name: str) -> Optional[Dict]:
        """
        通过企业名称获取企业基本信息（四要素）
        
        使用启信宝"企业模糊搜索"API（1.31）获取企业信息，包括：
        - 统一社会信用代码（credit_no）
        - 法定代表人（oper_name）
        - 成立日期（start_date）
        - 注册资本（regist_capi）
        
        然后再调用企业详情API获取更详细的信息：
        - 联系电话（phone）
        - 邮箱（email）
        - 地址（address）
        
        Args:
            company_name: 企业全称
        
        Returns:
            {
                'name': str,  # 企业名称
                'credit_code': str,  # 统一社会信用代码
                'legal_representative': str,  # 法定代表人
                'established_date': str,  # 成立日期（YYYY-MM-DD格式）
                'registered_capital': str,  # 注册资本（原始字符串，如"6500 万人民币"）
                'registered_capital_value': float,  # 注册资本数值（万元）
                'phone': str,  # 联系电话
                'email': str,  # 邮箱
                'address': str,  # 地址
            }
            如果查询失败返回None
        """
        if not company_name or len(company_name) < 2:
            logger.warning('企业名称至少需要2个字符')
            return None
        
        try:
            # 第一步：使用企业模糊搜索API查找企业
            # 使用精确名称匹配
            search_result = self.search_company(keyword=company_name, match_type='ename')
            
            if not search_result:
                logger.warning(f'企业搜索失败: {company_name}')
                return None
            
            # 检查是否返回了错误
            if isinstance(search_result, dict) and 'error' in search_result:
                error_info = search_result['error']
                logger.warning(f'企业搜索返回错误: {error_info}')
                return None
            
            # 获取搜索结果
            items = search_result.get('items', [])
            if not items:
                logger.warning(f'未找到企业: {company_name}')
                return None
            
            # 使用第一个搜索结果（通常是最匹配的）
            company_info = items[0]
            
            # 提取基本信息
            result = {
                'name': company_info.get('name', ''),
                'credit_code': company_info.get('credit_no', ''),
                'legal_representative': company_info.get('oper_name', ''),
                'established_date': company_info.get('start_date', ''),
                'registered_capital': '',
                'registered_capital_value': None,
                'phone': '',
                'email': '',
                'address': '',
            }
            
            # 第二步：调用企业详情API获取更详细的信息
            detail_info = self.get_company_detail(
                credit_code=result['credit_code'],
                company_name=company_name
            )
            
            if detail_info:
                # 更新注册资本
                if detail_info.get('reg_capital'):
                    result['registered_capital'] = detail_info.get('reg_capital', '')
                    result['registered_capital_value'] = detail_info.get('reg_capital_value')
                
                # 更新联系信息
                if detail_info.get('phone'):
                    result['phone'] = detail_info.get('phone', '')
                if detail_info.get('email'):
                    result['email'] = detail_info.get('email', '')
                if detail_info.get('address'):
                    result['address'] = detail_info.get('address', '')
                
                # 如果搜索结果中没有法定代表人，从详情中获取
                if not result['legal_representative'] and detail_info.get('legal_representative'):
                    result['legal_representative'] = detail_info.get('legal_representative', '')
                
                # 如果搜索结果中没有成立日期，从详情中获取
                if not result['established_date'] and detail_info.get('established_date'):
                    result['established_date'] = detail_info.get('established_date', '')
            
            logger.info(f'成功获取企业信息: {company_name}')
            return result
            
        except Exception as e:
            logger.error(f'获取企业信息异常: {str(e)}', exc_info=True)
            return None


# 延迟初始化函数
def get_qixinbao_service():
    """获取启信宝API服务实例（延迟初始化）"""
    return QixinbaoAPIService()

# 创建全局实例（延迟初始化）
qixinbao_service = None

def get_service():
    """获取服务实例"""
    global qixinbao_service
    if qixinbao_service is None:
        qixinbao_service = QixinbaoAPIService()
    return qixinbao_service


# ==================== 客户管理服务函数（按《客户管理详细设计方案 v1.12》实现）====================

def auto_move_to_public_sea():
    """
    自动将超过90天没有拜访信息的客户移入公海
    
    规则：
    - 超过90天没有对客户人员有任何拜访信息的客户，自动进入客户公海
    - 进入原因：auto_entry
    - 清空负责人
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Client, CustomerRelationship
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # 查找所有有负责人的客户
    clients = Client.objects.filter(responsible_user__isnull=False)
    
    moved_count = 0
    for client in clients:
        # 检查是否有90天内的拜访记录
        has_recent_visit = CustomerRelationship.objects.filter(
            client=client,
            followup_time__gte=cutoff_date
        ).exists()
        
        if not has_recent_visit:
            # 移入公海
            client.responsible_user = None
            client.public_sea_entry_time = timezone.now()
            client.public_sea_reason = 'auto_entry'
            client.save(update_fields=['responsible_user', 'public_sea_entry_time', 'public_sea_reason'])
            moved_count += 1
    
    return moved_count


def find_related_contacts_by_education(contact):
    """
    根据教育背景查找关联的客户人员
    
    规则：
    - 同一时间段在同一学校、同一专业的其他客户人员
    """
    from .models import ClientContact, ContactEducation
    
    related_contacts = []
    
    # 获取该联系人的所有教育背景
    educations = ContactEducation.objects.filter(contact=contact)
    
    for edu in educations:
        if not edu.school or not edu.start_date or not edu.end_date:
            continue
        
        # 查找同一时间段、同一学校、同一专业的其他联系人
        overlapping_educations = ContactEducation.objects.filter(
            school=edu.school,
            major=edu.major if edu.major else '',
            start_date__lte=edu.end_date,
            end_date__gte=edu.start_date
        ).exclude(contact=contact).select_related('contact')
        
        for overlapping_edu in overlapping_educations:
            if overlapping_edu.contact not in related_contacts:
                related_contacts.append(overlapping_edu.contact)
    
    return related_contacts


def find_related_contacts_by_work_experience(contact):
    """
    根据工作经历查找关联的客户人员
    
    规则：
    - 同一时间段在同一公司、同一办公地址的其他客户人员
    """
    from django.utils import timezone
    from .models import ClientContact, ContactWorkExperience
    from datetime import date
    
    related_contacts = []
    
    # 获取该联系人的所有工作经历
    work_experiences = ContactWorkExperience.objects.filter(contact=contact)
    
    for exp in work_experiences:
        if not exp.company_name or not exp.start_date:
            continue
        
        # 确定结束日期
        end_date = exp.end_date if exp.end_date else date.today()
        
        # 查找同一时间段、同一公司、同一办公地址的其他联系人
        overlapping_experiences = ContactWorkExperience.objects.filter(
            company_name=exp.company_name,
            office_address=exp.office_address if exp.office_address else '',
            start_date__lte=end_date
        ).exclude(contact=contact)
        
        # 进一步过滤：结束日期必须大于等于开始日期
        for overlapping_exp in overlapping_experiences:
            overlapping_end_date = overlapping_exp.end_date if overlapping_exp.end_date else date.today()
            if overlapping_end_date >= exp.start_date:
                if overlapping_exp.contact not in related_contacts:
                    related_contacts.append(overlapping_exp.contact)
    
    return related_contacts


def find_all_related_contacts(contact):
    """
    查找所有关联的客户人员（综合教育背景、工作经历、工作变动、合作、跟踪等信息）
    
    返回：
    - 关联联系人列表
    - 关联原因（教育背景、工作经历等）
    """
    from .models import ContactJobChange, ContactCooperation, ContactTracking
    
    related_contacts = []
    relation_reasons = {}
    
    # 根据教育背景查找
    edu_related = find_related_contacts_by_education(contact)
    for related in edu_related:
        if related not in related_contacts:
            related_contacts.append(related)
            relation_reasons[related.id] = relation_reasons.get(related.id, []) + ['教育背景']
    
    # 根据工作经历查找
    work_related = find_related_contacts_by_work_experience(contact)
    for related in work_related:
        if related not in related_contacts:
            related_contacts.append(related)
            relation_reasons[related.id] = relation_reasons.get(related.id, []) + ['工作经历']
        elif related in related_contacts:
            relation_reasons[related.id] = relation_reasons.get(related.id, []) + ['工作经历']
    
    # 根据工作变动查找（同一公司、同一时间段）
    job_changes = ContactJobChange.objects.filter(contact=contact)
    for change in job_changes:
        if change.new_company:
            # 查找在同一公司工作的其他联系人
            related_changes = ContactJobChange.objects.filter(
                new_company=change.new_company,
                change_date__year=change.change_date.year
            ).exclude(contact=contact).select_related('contact')
            
            for related_change in related_changes:
                if related_change.contact not in related_contacts:
                    related_contacts.append(related_change.contact)
                    relation_reasons[related_change.contact.id] = relation_reasons.get(related_change.contact.id, []) + ['工作变动']
    
    # 根据合作信息查找（同一时间段、同一合作类型）
    cooperations = ContactCooperation.objects.filter(contact=contact)
    for coop in cooperations:
        if coop.cooperation_date:
            related_coops = ContactCooperation.objects.filter(
                cooperation_type=coop.cooperation_type,
                cooperation_date__year=coop.cooperation_date.year
            ).exclude(contact=contact).select_related('contact')
            
            for related_coop in related_coops:
                if related_coop.contact not in related_contacts:
                    related_contacts.append(related_coop.contact)
                    relation_reasons[related_coop.contact.id] = relation_reasons.get(related_coop.contact.id, []) + ['合作信息']
    
    return related_contacts, relation_reasons


class AmapAPIService:
    """高德地图API服务类
    
    提供地址、区域、定位等相关功能：
    - 地理编码（地址转坐标）
    - 逆地理编码（坐标转地址）
    - 行政区域查询
    - IP定位
    - 地址解析
    - 输入提示（搜索建议）
    """
    
    def __init__(self):
        # 优先从后台API管理系统读取配置
        self._load_config_from_api_management()
        
        # 如果后台没有配置，则从环境变量读取（向后兼容）
        if not self.api_key:
            self.api_key = self.api_key or getattr(settings, 'AMAP_API_KEY', '')
            self.api_base_url = self.api_base_url or getattr(settings, 'AMAP_API_BASE_URL', 'https://restapi.amap.com/v3')
            self.timeout = self.timeout or getattr(settings, 'AMAP_API_TIMEOUT', 10)
        
        # 记录配置状态（用于调试）
        if self.api_key:
            logger.info(f'高德地图API配置已加载: api_key={self.api_key[:20]}..., base_url={self.api_base_url}, 来源={"后台API管理" if hasattr(self, "_config_source") and self._config_source == "api_management" else "环境变量"}')
        else:
            logger.warning('高德地图API配置未设置，请在后台API管理中配置或设置环境变量AMAP_API_KEY')
    
    def _load_config_from_api_management(self):
        """从后台API管理系统加载配置"""
        try:
            from backend.apps.api_management.models import ExternalSystem, ApiInterface
            
            # 查找高德地图外部系统
            amap_system = ExternalSystem.objects.filter(
                code='AMAP',
                is_active=True
            ).first()
            
            if amap_system:
                # 查找任意一个激活的API接口（所有接口使用相同的API Key）
                api_interface = ApiInterface.objects.filter(
                    external_system=amap_system,
                    is_active=True
                ).first()
                
                if api_interface and api_interface.auth_config:
                    auth_config = api_interface.auth_config
                    self.api_key = auth_config.get('api_key', '')
                    self.api_base_url = amap_system.base_url
                    self.timeout = api_interface.timeout or 10
                    self._config_source = "api_management"
                    logger.info('从后台API管理系统加载高德地图配置成功')
                    return
            
            # 如果未找到配置，初始化默认值
            self.api_key = ''
            self.api_base_url = 'https://restapi.amap.com/v3'
            self.timeout = 10
            self._config_source = "fallback"
            
        except Exception as e:
            logger.warning(f'从后台API管理系统加载高德地图配置失败: {str(e)}，将使用环境变量配置')
            self.api_key = ''
            self.api_base_url = 'https://restapi.amap.com/v3'
            self.timeout = 10
            self._config_source = "fallback"
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        发送API请求（GET方式）
        
        Args:
            endpoint: API端点路径
            params: 请求参数字典
            
        Returns:
            API返回的JSON数据，失败返回None
        """
        if not self.api_key:
            logger.warning('高德地图API配置未设置，请配置AMAP_API_KEY')
            return None
        
        try:
            # 添加API Key到参数中
            params['key'] = self.api_key
            params['output'] = 'json'  # 默认返回JSON格式
            
            # 发送GET请求
            url = f'{self.api_base_url}{endpoint}'
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 检查返回状态
            status = result.get('status', '0')
            info = result.get('info', '未知错误')
            
            if status == '1':
                logger.info(f'高德地图API调用成功: {endpoint}')
                return result
            else:
                logger.warning(f'高德地图API调用失败: {endpoint}, status={status}, info={info}')
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f'高德地图API请求异常: {endpoint}, error={str(e)}')
            return None
        except Exception as e:
            logger.error(f'高德地图API处理异常: {endpoint}, error={str(e)}')
            return None
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Dict]:
        """
        地理编码：将地址转换为经纬度坐标
        
        Args:
            address: 地址字符串，如"北京市朝阳区阜通东大街6号"
            city: 可选，城市名称或城市编码，限制搜索范围，提高准确性
            
        Returns:
            {
                'location': '116.480881,39.989410',  # 经纬度
                'formatted_address': '北京市朝阳区阜通东大街6号',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'adcode': '110105',  # 区域编码
                'level': '门址'  # 地址级别
            }
        """
        params = {
            'address': address
        }
        if city:
            params['city'] = city
        
        result = self._make_request('/geocode/geo', params)
        if not result or not result.get('geocodes'):
            return None
        
        geocode = result['geocodes'][0]  # 取第一个结果
        
        location = geocode.get('location', '')
        if not location:
            return None
        
        # 解析经纬度
        lon, lat = location.split(',')
        
        return {
            'location': location,
            'longitude': float(lon),
            'latitude': float(lat),
            'formatted_address': geocode.get('formatted_address', address),
            'province': geocode.get('province', ''),
            'city': geocode.get('city', ''),
            'district': geocode.get('district', ''),
            'adcode': geocode.get('adcode', ''),
            'level': geocode.get('level', '')
        }
    
    def regeocode(self, longitude: float, latitude: float) -> Optional[Dict]:
        """
        逆地理编码：将经纬度坐标转换为地址
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            {
                'formatted_address': '北京市朝阳区阜通东大街6号',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'adcode': '110105',
                'township': '望京街道',
                'neighborhood': {'name': '方恒国际中心'},
                'building': {'name': '方恒国际中心A座'},
                'addressComponent': {
                    'province': '北京市',
                    'city': '北京市',
                    'district': '朝阳区',
                    'township': '望京街道',
                    'street': '阜通东大街',
                    'streetNumber': '6号'
                }
            }
        """
        params = {
            'location': f'{longitude},{latitude}',
            'extensions': 'all'  # 返回详细信息
        }
        
        result = self._make_request('/geocode/regeo', params)
        if not result or not result.get('regeocode'):
            return None
        
        regeocode = result['regeocode']
        address_component = regeocode.get('addressComponent', {})
        
        return {
            'formatted_address': regeocode.get('formatted_address', ''),
            'province': address_component.get('province', ''),
            'city': address_component.get('city', ''),
            'district': address_component.get('district', ''),
            'adcode': address_component.get('adcode', ''),
            'township': address_component.get('township', ''),
            'neighborhood': regeocode.get('neighborhood', {}),
            'building': regeocode.get('building', {}),
            'addressComponent': address_component
        }
    
    def district_search(self, keywords: str = '', subdistrict: int = 0, 
                       level: str = '', extensions: str = 'base') -> Optional[Dict]:
        """
        行政区域查询：查询省、市、区县信息
        
        Args:
            keywords: 查询关键字，支持：行政区名称、citycode、adcode
                     如：北京、110000（北京citycode）、110000（北京adcode）
            subdistrict: 子级行政区，0：不返回下级行政区；1：返回下一级行政区；2：返回下两级行政区；3：返回下三级行政区
            level: 查询行政级别，可选值：country、province、city、district、street
            extensions: 返回结果控制，base：返回基本信息；all：返回全部信息
            
        Returns:
            {
                'districts': [
                    {
                        'name': '北京市',
                        'adcode': '110000',
                        'citycode': '010',
                        'level': 'province',
                        'center': '116.407526,39.904030',
                        'districts': [...]  # 下级行政区
                    }
                ]
            }
        """
        params = {
            'keywords': keywords,
            'subdistrict': subdistrict,
            'extensions': extensions
        }
        if level:
            params['level'] = level
        
        return self._make_request('/config/district', params)
    
    def ip_location(self, ip: Optional[str] = None) -> Optional[Dict]:
        """
        IP定位：根据IP地址获取位置信息
        
        Args:
            ip: IP地址，不传则使用请求IP
            
        Returns:
            {
                'province': '北京市',
                'city': '北京市',
                'adcode': '110000',
                'rectangle': '116.011934,39.661271;116.782983,40.216496'  # 边界坐标
            }
        """
        params = {}
        if ip:
            params['ip'] = ip
        
        return self._make_request('/ip', params)
    
    def input_tips(self, keywords: str, city: Optional[str] = None, 
                   location: Optional[str] = None, datatype: str = 'all') -> Optional[Dict]:
        """
        输入提示：根据关键词获取搜索建议
        
        Args:
            keywords: 查询关键词
            city: 可选，城市名称或城市编码，限制搜索范围
            location: 可选，经纬度坐标，格式：经度,纬度，用于排序
            datatype: 返回数据类型，all：返回所有类型；poi：仅返回POI；bus：仅返回公交站；busline：仅返回公交线路
            
        Returns:
            {
                'tips': [
                    {
                        'name': '北京市朝阳区阜通东大街6号',
                        'district': '朝阳区',
                        'adcode': '110105',
                        'location': '116.480881,39.989410',
                        'type': '地名地址信息;门址信息'
                    }
                ]
            }
        """
        params = {
            'keywords': keywords,
            'datatype': datatype
        }
        if city:
            params['city'] = city
        if location:
            params['location'] = location
        
        return self._make_request('/assistant/inputtips', params)
    
    def distance(self, origins: str, destination: str, 
                type: int = 1) -> Optional[Dict]:
        """
        距离测量：计算两点或多点之间的距离
        
        Args:
            origins: 起点坐标，格式：经度,纬度，多个点用|分隔，如：116.481028,39.989643|116.481028,39.989643
            destination: 终点坐标，格式：经度,纬度，多个点用|分隔
            type: 计算类型，1：直线距离；0：驾车距离（需要路径规划服务）
            
        Returns:
            {
                'results': [
                    {
                        'origin_id': '1',
                        'dest_id': '1',
                        'distance': '1234.5',  # 距离（米）
                        'duration': '120'  # 时间（秒，仅驾车距离有）
                    }
                ]
            }
        """
        params = {
            'origins': origins,
            'destination': destination,
            'type': type
        }
        
        return self._make_request('/distance', params)
    
    def parse_address(self, address: str, city: Optional[str] = None) -> Optional[Dict]:
        """
        地址解析：智能解析地址字符串，提取省市区等信息
        
        这是一个便捷方法，结合地理编码和逆地理编码，提供更友好的地址解析结果
        
        Args:
            address: 地址字符串
            city: 可选，城市名称，限制搜索范围
            
        Returns:
            {
                'original_address': '北京市朝阳区阜通东大街6号',
                'formatted_address': '北京市朝阳区阜通东大街6号',
                'longitude': 116.480881,
                'latitude': 39.989410,
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'adcode': '110105',
                'level': '门址'
            }
        """
        # 先进行地理编码
        geocode_result = self.geocode(address, city)
        if not geocode_result:
            return None
        
        # 如果地理编码成功，再通过逆地理编码获取更详细的信息
        regeocode_result = self.regeocode(
            geocode_result['longitude'],
            geocode_result['latitude']
        )
        
        if regeocode_result:
            # 合并结果
            geocode_result.update({
                'township': regeocode_result.get('township', ''),
                'street': regeocode_result.get('addressComponent', {}).get('street', ''),
                'streetNumber': regeocode_result.get('addressComponent', {}).get('streetNumber', '')
            })
        
        geocode_result['original_address'] = address
        return geocode_result

