"""
AI顾问服务
使用API管理系统中的DeepSeek API配置
集成CAD图纸解析功能，用于优化咨询分析
"""
import json
import logging
import requests
import os
import base64
from typing import Dict, Optional, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AIAdvisorService:
    """AI顾问服务类"""
    
    def __init__(self):
        try:
            # 从API管理系统中加载配置
            self.api_key, self.api_base_url, self.model = self._load_api_config()
            
            if not self.api_key:
                logger.warning("⚠ DeepSeek API Key未配置，AI顾问功能将不可用。请在后台API管理中配置：/admin/api_management/externalsystem/")
            else:
                logger.info(f"✓ AI顾问服务初始化成功，API Key已配置 (长度: {len(self.api_key)} 字符)")
        except Exception as e:
            logger.exception(f"AI顾问服务初始化失败: {str(e)}")
            # 即使初始化失败，也设置默认值，避免后续调用出错
            self.api_key = ''
            self.api_base_url = getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com')
            self.model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 初始化CAD解析服务
        try:
            from .cad_parser_service import CADParserService
            self.cad_parser = CADParserService()
            logger.info("✓ CAD解析服务已初始化")
        except Exception as e:
            logger.warning(f"⚠ CAD解析服务初始化失败: {str(e)}")
            self.cad_parser = None
    
    def _load_api_config(self):
        """
        从API管理系统中加载DeepSeek API配置
        优先使用API管理系统中的配置，如果没有则回退到settings
        """
        try:
            from backend.apps.api_management.models import ExternalSystem, ApiInterface
            
            # 查找DeepSeek外部系统
            deepseek_system = ExternalSystem.objects.filter(
                code='DEEPSEEK',
                is_active=True
            ).first()
            
            if deepseek_system:
                # 优先查找Chat API接口（编码：DEEPSEEK-00001）
                chat_api = ApiInterface.objects.filter(
                    external_system=deepseek_system,
                    code='DEEPSEEK-00001',
                    is_active=True
                ).first()
                
                # 如果Chat API不存在，查找任意一个激活的API接口
                if not chat_api:
                    chat_api = ApiInterface.objects.filter(
                        external_system=deepseek_system,
                        is_active=True
                    ).first()
                
                if chat_api and chat_api.auth_config:
                    # 从认证配置中获取API Key
                    auth_config = chat_api.auth_config
                    api_key = auth_config.get('token', '')
                    
                    # 检查API Key是否有效（不是占位符）
                    if api_key and api_key not in ['请在后台配置API Key', '', 'None']:
                        # 从请求体结构中获取模型名称
                        request_schema = chat_api.request_body_schema or {}
                        model = request_schema.get('model', getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'))
                        
                        logger.info(f"✓ 从API管理系统加载DeepSeek配置成功: 系统={deepseek_system.name}, 接口={chat_api.name}, 模型={model}")
                        return (
                            api_key,
                            deepseek_system.base_url,
                            model
                        )
                    else:
                        logger.warning(f"API管理系统中的DeepSeek API Key未配置或为占位符 (接口: {chat_api.name}, Key: {api_key[:20] if api_key else 'None'}...)")
                else:
                    if chat_api:
                        logger.warning(f"API接口 {chat_api.name} 存在但认证配置为空")
                    else:
                        logger.warning("未找到激活的DeepSeek API接口")
            
            # 如果API管理系统中没有配置，回退到settings
            logger.info("API管理系统中未找到有效的DeepSeek配置，使用settings中的配置")
            return (
                getattr(settings, 'DEEPSEEK_API_KEY', ''),
                getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com'),
                getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
            )
            
        except Exception as e:
            logger.warning(f"从API管理系统加载配置失败: {str(e)}，使用settings中的配置")
            # 如果加载失败，回退到settings
            return (
                getattr(settings, 'DEEPSEEK_API_KEY', ''),
                getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com'),
                getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
            )
    
    def call_chat_api(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """
        调用DeepSeek Chat API
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数（0-1）
            max_tokens: 最大token数
        
        Returns:
            AI返回的内容，如果失败返回None
        """
        if not self.api_key:
            logger.warning("DeepSeek API Key未配置")
            return None
        
        try:
            # 根据DeepSeek官方文档，端点应该是 /chat/completions
            # base_url 可以是 https://api.deepseek.com 或 https://api.deepseek.com/v1
            # 无论哪种情况，都使用 /chat/completions 作为端点
            base_url_clean = self.api_base_url.rstrip('/')
            url = f"{base_url_clean}/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False  # 非流式输出，符合DeepSeek官方文档示例
            }
            
            # 增加超时时间到60秒，因为AI分析可能需要较长时间
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            logger.info("DeepSeek API调用成功")
            return content
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # 尝试从响应中获取更详细的错误信息
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_msg = error_json.get('error', {}).get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            
            logger.error(f"DeepSeek API调用失败: {error_msg}")
            return None
        except Exception as e:
            logger.exception(f"处理API响应失败: {str(e)}")
            return None
    
    def call_vision_api(self, prompt: str, image_base64: str, system_prompt: Optional[str] = None, temperature: float = 0.1, max_tokens: int = 4000) -> Optional[str]:
        """
        调用DeepSeek Vision API识别图片
        
        Args:
            prompt: 用户提示词（描述需要从图片中提取什么信息）
            image_base64: base64编码的图片数据（不包含data:image前缀）
            system_prompt: 系统提示词（可选）
            temperature: 温度参数（0-1），Vision API通常使用较低的值
            max_tokens: 最大token数
        
        Returns:
            AI返回的内容，如果失败返回None
        """
        if not self.api_key:
            logger.warning("DeepSeek API Key未配置")
            return None
        
        if not image_base64:
            logger.warning("图片数据为空")
            return None
        
        try:
            # 根据DeepSeek官方文档，Vision API使用相同的端点
            base_url_clean = self.api_base_url.rstrip('/')
            url = f"{base_url_clean}/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 构建消息，包含文本和图片
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Vision API的content是数组格式，包含文本和图片
            content_items = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
            
            messages.append({
                "role": "user",
                "content": content_items
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Vision API可能需要更长的超时时间
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            logger.info("DeepSeek Vision API调用成功")
            return content
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_msg = error_json.get('error', {}).get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            
            logger.error(f"DeepSeek Vision API调用失败: {error_msg}")
            return None
        except Exception as e:
            logger.exception(f"处理Vision API响应失败: {str(e)}")
            return None
    
    def analyze_design_problem(
        self, 
        problem: str, 
        constraints: str = '', 
        problem_type: str = 'structural', 
        images: Optional[list] = None,
        cad_files: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        分析设计优化问题
        
        Args:
            problem: 优化前做法
            constraints: 约束条件
            problem_type: 问题类型
            images: 图片列表，每个元素是base64编码的图片字符串（不包含data:image前缀）
            cad_files: CAD文件列表，每个元素包含 {'path': 文件路径, 'type': 文件类型}
        
        Returns:
            包含分析结果的字典
        """
        if not problem:
            return {
                'success': False,
                'error': '优化前做法不能为空'
            }
        
        # 构建系统提示词
        system_prompt = """你是一位专业的设计优化顾问，擅长建筑、结构、机电等专业的设计优化。
你的任务是：
1. 仔细分析用户提出的设计问题和CAD图纸中的设计参数
2. 基于实际的设计参数（尺寸、材料、荷载等）提供多个可行的优化方案
3. 评估每个方案的成本节省潜力、技术风险和可行性
4. 给出详细的实施建议和注意事项

请用JSON格式返回结果，包含以下字段：
- summary: 简要总结（应提及从CAD图纸中提取的关键设计参数）
- solutions: 优化方案数组，每个方案包含：
  * title: 方案标题
  * description: 详细描述（应基于CAD图纸中的实际参数）
  * savings: 节省金额（单位：万元，基于实际参数计算）
  * risk: 风险等级（low/medium/high）
  * advantages: 优势数组
  * disadvantages: 注意事项数组
- analysis_report: 分析报告对象，包含content字段（HTML格式）
- risk_assessment: 风险评估数组，每个风险包含title, level, description

重要要求：
1. 如果CAD图纸中提供了具体的设计参数（如构件尺寸、材料规格、荷载等），必须基于这些实际参数进行分析
2. 节省金额的计算应基于实际的材料用量和价格
3. 如果CAD参数不完整，可以结合行业经验给出合理估算，但需说明
4. 优化方案应具体、可操作，避免泛泛而谈"""
        
        # 处理CAD文件，提取结构化参数
        cad_params_text = ""
        if cad_files and self.cad_parser:
            cad_params_text = self._process_cad_files(cad_files)
        
        # 构建用户提示词
        user_prompt = f"""问题类型：{problem_type}
优化前做法：{problem}
约束条件：{constraints if constraints else '无特殊约束'}"""
        
        # 如果有CAD参数，添加到提示词中
        if cad_params_text:
            user_prompt += f"""

【CAD图纸解析结果】
{cad_params_text}

请仔细分析上述CAD图纸中的设计参数，包括：
1. 构件尺寸和材料规格
2. 结构布置和连接方式
3. 设计参数和荷载情况
4. 可能的优化空间和成本节约潜力

请结合CAD图纸中的具体设计参数和上述问题描述，提供详细的设计优化建议。每个优化方案应：
- 明确指出可以优化的具体构件或设计参数
- 基于CAD图纸中的实际尺寸和材料进行计算
- 提供具体的节省金额估算（单位：万元）
- 评估技术可行性和实施风险"""
        else:
            user_prompt += "\n\n请基于以上信息，提供详细的设计优化建议。"
        
        # 如果有图片，使用Vision API；否则使用Chat API
        if images and len(images) > 0:
            # 使用第一张图片进行分析（DeepSeek Vision API目前支持单张图片）
            image_base64 = images[0]
            # 在提示词中添加图片说明
            vision_prompt = f"""{user_prompt}

请仔细查看上传的设计图纸，识别图纸中的关键信息，包括：
1. 结构类型、构件尺寸、材料规格
2. 设计参数、荷载情况
3. 可能存在的优化空间
4. 成本节约潜力

请结合图纸信息、CAD解析参数（如有）和上述问题描述，提供详细的设计优化建议。"""
            
            ai_response = self.call_vision_api(vision_prompt, image_base64, system_prompt, temperature=0.7, max_tokens=4000)
        else:
            # 调用DeepSeek Chat API
            ai_response = self.call_chat_api(user_prompt, system_prompt, temperature=0.7, max_tokens=2000)
        
        if not ai_response:
            return {
                'success': False,
                'error': 'DeepSeek API调用失败，请检查API配置'
            }
        
        # 尝试解析JSON响应
        try:
            # 如果AI返回的是JSON格式
            if ai_response.strip().startswith('{'):
                result = json.loads(ai_response)
            else:
                # 如果AI返回的是文本，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # 如果无法解析，使用默认格式
                    result = {
                        'summary': ai_response[:200] + '...' if len(ai_response) > 200 else ai_response,
                        'solutions': [],
                        'analysis_report': {'content': f'<p>{ai_response}</p>'},
                        'risk_assessment': []
                    }
            
            return {
                'success': True,
                **result
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 内容: {ai_response[:200]}")
            # JSON解析失败，使用文本内容
            return {
                'success': True,
                'summary': 'AI分析完成',
                'solutions': [],
                'analysis_report': {'content': f'<p>{ai_response}</p>'},
                'risk_assessment': []
            }
        except Exception as e:
            logger.exception(f"处理AI响应失败: {str(e)}")
            return {
                'success': False,
                'error': f'处理响应失败: {str(e)}'
            }
    
    def _process_cad_files(self, cad_files: List[Dict[str, str]]) -> str:
        """
        处理CAD文件，提取设计参数
        
        Args:
            cad_files: CAD文件列表，每个元素包含 {'path': 文件路径, 'type': 文件类型}
        
        Returns:
            格式化的参数文本，用于AI分析
        """
        if not self.cad_parser:
            return ""
        
        results = []
        for cad_file in cad_files:
            file_path = cad_file.get('path')
            file_type = cad_file.get('type')
            
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"CAD文件不存在: {file_path}")
                continue
            
            try:
                # 提取优化分析所需的关键信息
                result = self.cad_parser.extract_for_optimization(file_path)
                
                if result.get('success'):
                    opt_data = result.get('optimization_data', {})
                    summary = opt_data.get('summary', '')
                    key_params = opt_data.get('key_params', {})
                    
                    # 格式化输出
                    file_info = f"文件: {os.path.basename(file_path)} ({opt_data.get('file_type', 'unknown')})\n"
                    file_info += f"摘要: {summary}\n"
                    
                    # 添加关键参数
                    if key_params.get('dimensions'):
                        file_info += f"尺寸标注数量: {len(key_params['dimensions'])}\n"
                    
                    if key_params.get('materials'):
                        file_info += f"材料信息: {', '.join(key_params['materials'])}\n"
                    
                    if key_params.get('structural_info'):
                        for elem in key_params['structural_info']:
                            file_info += f"结构元素 - {elem['category']}: {elem['count']}个\n"
                    
                    results.append(file_info)
                else:
                    logger.warning(f"CAD文件解析失败: {result.get('error')}")
            except Exception as e:
                logger.error(f"处理CAD文件失败: {str(e)}", exc_info=True)
        
        return "\n\n".join(results) if results else ""

