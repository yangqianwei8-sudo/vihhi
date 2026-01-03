"""
短信验证码服务
用于用户注册时的手机号验证
"""
import random
import string
import logging
import json
from typing import Tuple, Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class SmsVerificationService:
    """短信验证码服务"""
    
    # 验证码有效期（秒）
    CODE_EXPIRE_TIME = 300  # 5分钟
    
    # 验证码长度
    CODE_LENGTH = 6
    
    # 发送间隔（秒）
    SEND_INTERVAL = 60  # 1分钟内只能发送一次
    
    @classmethod
    def generate_code(cls) -> str:
        """生成6位数字验证码"""
        return ''.join([str(random.randint(0, 9)) for _ in range(cls.CODE_LENGTH)])
    
    @classmethod
    def send_verification_code(cls, phone: str) -> Tuple[bool, str]:
        """
        发送短信验证码
        
        Args:
            phone: 手机号
            
        Returns:
            (success, message)
        """
        try:
            # 验证手机号格式
            import re
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, phone):
                return False, "手机号格式不正确"
            
            # 检查发送频率限制
            send_key = f'sms_send_{phone}'
            last_send_time = cache.get(send_key)
            if last_send_time:
                elapsed = (timezone.now() - last_send_time).total_seconds()
                if elapsed < cls.SEND_INTERVAL:
                    remaining = int(cls.SEND_INTERVAL - elapsed)
                    return False, f"发送过于频繁，请{remaining}秒后再试"
            
            # 生成验证码
            code = cls.generate_code()
            
            # 检查阿里云短信配置
            access_key_id = getattr(settings, 'ALIYUN_SMS_ACCESS_KEY_ID', '')
            access_key_secret = getattr(settings, 'ALIYUN_SMS_ACCESS_KEY_SECRET', '')
            sign_name = getattr(settings, 'ALIYUN_SMS_SIGN_NAME', '维海科技')
            # 注册验证码模板代码（如果配置了专门的模板）
            template_code = getattr(settings, 'ALIYUN_SMS_REGISTER_TEMPLATE_CODE', '')
            # 如果没有配置注册模板，使用通用模板
            if not template_code:
                template_code = getattr(settings, 'ALIYUN_SMS_TEMPLATE_CODE', '')
            region = getattr(settings, 'ALIYUN_SMS_REGION', 'cn-hangzhou')
            
            if not access_key_id or not access_key_secret:
                logger.error("阿里云短信服务未配置：缺少 AccessKey ID 或 AccessKey Secret")
                return False, "短信服务未配置，请联系管理员"
            
            # 尝试导入阿里云SDK
            try:
                from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
                from alibabacloud_tea_openapi import models as open_api_models
                from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
            except ImportError:
                logger.error("阿里云短信SDK未安装")
                return False, "短信服务SDK未安装，请联系管理员"
            
            # 创建阿里云短信客户端
            config = open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                region_id=region
            )
            config.endpoint = 'dysmsapi.aliyuncs.com'
            client = DysmsapiClient(config)
            
            # 构建短信内容
            # 如果没有配置注册模板，尝试使用通用模板
            if not template_code:
                template_code = getattr(settings, 'ALIYUN_SMS_TEMPLATE_CODE', '')
            
            if template_code:
                # 使用模板发送（推荐方式）
                # 根据图片中的模板，验证码模板应该是：尊敬的用户,您正在注册账号,验证码为${code},5分钟内有效
                template_params = {
                    'code': code
                }
                
                request = dysmsapi_models.SendSmsRequest(
                    phone_numbers=phone,
                    sign_name=sign_name,
                    template_code=template_code,
                    template_param=json.dumps(template_params)
                )
            else:
                # 如果没有配置任何模板，返回错误
                logger.error("未配置短信模板代码，无法发送验证码")
                return False, "短信服务未配置模板，请联系管理员配置短信模板"
            
            # 发送短信
            response = client.send_sms(request)
            
            # 检查响应
            if response.status_code == 200 and response.body.code == 'OK':
                # 发送成功，保存验证码到缓存
                code_key = f'sms_code_{phone}'
                cache.set(code_key, code, cls.CODE_EXPIRE_TIME)
                
                # 记录发送时间
                cache.set(send_key, timezone.now(), cls.SEND_INTERVAL)
                
                logger.info(f"验证码发送成功: phone={phone}, code={code}")
                # 开发环境可以返回验证码，生产环境应该注释掉
                if settings.DEBUG:
                    return True, f"验证码已发送（开发模式：{code}）"
                return True, "验证码已发送，请查收短信"
            else:
                # 发送失败
                error_code = response.body.code if response.body else 'UNKNOWN'
                error_message = response.body.message if response.body else '发送失败'
                logger.error(f"验证码发送失败: phone={phone}, error={error_code}: {error_message}")
                return False, f"发送失败：{error_message}"
            
        except ImportError as e:
            logger.error(f"导入阿里云SDK失败: {str(e)}")
            return False, "短信服务SDK未安装"
        except Exception as e:
            logger.error(f"发送验证码失败: {str(e)}", exc_info=True)
            return False, f"发送失败：{str(e)}"
    
    @classmethod
    def verify_code(cls, phone: str, code: str) -> Tuple[bool, str]:
        """
        验证短信验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            (success, message)
        """
        try:
            # 验证手机号格式
            import re
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, phone):
                return False, "手机号格式不正确"
            
            # 验证验证码格式
            if not code or len(code) != cls.CODE_LENGTH or not code.isdigit():
                return False, "验证码格式不正确"
            
            # 从缓存获取验证码
            code_key = f'sms_code_{phone}'
            cached_code = cache.get(code_key)
            
            if not cached_code:
                return False, "验证码已过期，请重新获取"
            
            if cached_code != code:
                return False, "验证码错误"
            
            # 验证成功，删除验证码（防止重复使用）
            cache.delete(code_key)
            
            logger.info(f"验证码验证成功: phone={phone}")
            return True, "验证成功"
            
        except Exception as e:
            logger.error(f"验证验证码失败: {str(e)}", exc_info=True)
            return False, f"验证失败：{str(e)}"

