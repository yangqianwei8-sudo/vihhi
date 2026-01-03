"""
合同识别服务
使用DeepSeek API识别合同文档并提取结构化信息
"""
import os
import base64
import json
import logging
import requests
from typing import Dict, Optional, Any
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class ContractRecognitionService:
    """合同识别服务类"""
    
    def __init__(self):
        # 优先从API管理系统中读取配置
        self.api_key, self.api_base_url, self.model = self._load_api_config()
        
        if not self.api_key:
            logger.warning("DeepSeek API Key未配置，合同识别功能将不可用")
    
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
                # 优先查找Vision API接口（合同识别，编码：DEEPSEEK-00002）
                vision_api = ApiInterface.objects.filter(
                    external_system=deepseek_system,
                    code='DEEPSEEK-00002',
                    is_active=True
                ).first()
                
                # 如果Vision API不存在，查找Chat API（编码：DEEPSEEK-00001）
                if not vision_api:
                    vision_api = ApiInterface.objects.filter(
                        external_system=deepseek_system,
                        code='DEEPSEEK-00001',
                        is_active=True
                    ).first()
                
                # 如果还是不存在，查找任意一个激活的API接口
                if not vision_api:
                    vision_api = ApiInterface.objects.filter(
                        external_system=deepseek_system,
                        is_active=True
                    ).first()
                
                if vision_api and vision_api.auth_config:
                    # 从认证配置中获取API Key
                    auth_config = vision_api.auth_config
                    api_key = auth_config.get('token', '')
                    
                    # 检查API Key是否有效（不是占位符）
                    if api_key and api_key not in ['请在后台配置API Key', '']:
                        # 从请求体结构中获取模型名称
                        request_schema = vision_api.request_body_schema or {}
                        model = request_schema.get('model', getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'))
                        
                        logger.info(f"从API管理系统加载DeepSeek配置: 系统={deepseek_system.name}, 接口={vision_api.name}")
                        return (
                            api_key,
                            deepseek_system.base_url,
                            model
                        )
                    else:
                        logger.warning("API管理系统中的DeepSeek API Key未配置或为占位符")
            
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
    
    def recognize_contract(self, file_path: str, file_type: str = 'pdf') -> Dict[str, Any]:
        """
        识别合同文件并提取信息
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 ('pdf', 'image', 'docx')
        
        Returns:
            包含识别结果的字典
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'DeepSeek API Key未配置。请在后台API管理中配置：/admin/api_management/apiinterface/，找到"Vision API (合同识别)"，编辑后在"认证配置"的auth_config中设置token字段为您的API Key。或运行命令：python manage.py sync_deepseek_api_key --api-key YOUR_API_KEY'
            }
        
        try:
            # 构建识别提示词
            prompt = self._build_recognition_prompt()
            
            # DeepSeek Chat模型不支持直接处理图片/PDF，需要先提取文本
            # 先提取文本，再分析
            text = self._extract_text(file_path, file_type)
            if not text:
                return {
                    'success': False,
                    'error': '无法提取文件文本内容。请确保文件包含可提取的文本，或使用OCR功能处理扫描件。'
                }
            
            # 调用Chat API分析文本
            result = self._call_chat_api(text, prompt)
            
            # 解析结果
            if result.get('success'):
                contract_data = self._parse_recognition_result(result.get('content', ''))
                return {
                    'success': True,
                    'data': contract_data,
                    'raw_text': result.get('content', '')
                }
            else:
                return result
                
        except Exception as e:
            logger.exception(f"合同识别失败: {str(e)}")
            return {
                'success': False,
                'error': f'识别失败: {str(e)}'
            }
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """读取文件并转换为base64"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return None
    
    def _build_recognition_prompt(self) -> str:
        """构建合同识别提示词"""
        return """请仔细分析这份合同文档，提取以下信息并以JSON格式返回：

{
    "contract_name": "合同名称",
    "contract_number": "合同编号",
    "contract_type": "合同类型（如：技术服务合同、设计合同等）",
    "contract_amount": "合同金额（数字，不含货币符号）",
    "contract_date": "合同签订日期（YYYY-MM-DD格式）",
    "effective_date": "生效日期（YYYY-MM-DD格式）",
    "start_date": "开始日期（YYYY-MM-DD格式）",
    "end_date": "结束日期（YYYY-MM-DD格式）",
    "party_a": {
        "name": "甲方单位名称",
        "contact": "甲方联系人",
        "phone": "甲方联系电话",
        "email": "甲方联系邮箱",
        "address": "甲方地址",
        "credit_code": "统一社会信用代码",
        "legal_representative": "法定代表人"
    },
    "party_b": {
        "name": "乙方单位名称",
        "contact": "乙方联系人",
        "phone": "乙方联系电话",
        "email": "乙方联系邮箱",
        "address": "乙方地址",
        "credit_code": "统一社会信用代码",
        "legal_representative": "法定代表人"
    },
    "description": "合同主要内容描述",
    "notes": "其他备注信息"
}

注意：
1. 如果某个字段在合同中没有找到，请设置为空字符串
2. 日期格式必须为YYYY-MM-DD
3. 金额只提取数字，不要包含货币符号或单位
4. 只返回JSON，不要包含其他说明文字
5. 如果合同中有多个签约主体，party_a和party_b分别对应第一个和第二个主体"""
    
    
    def _call_chat_api(self, text: str, prompt: str) -> Dict[str, Any]:
        """调用DeepSeek Chat API分析文本"""
        try:
            url = f"{self.api_base_url}/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 如果文本太长，截取前8000字符（保留一些空间给prompt）
            if len(text) > 8000:
                text = text[:8000] + "\n\n[文本已截断，仅显示前8000字符]"
                logger.warning("合同文本过长，已截断")
            
            messages = [
                {
                    "role": "user",
                    "content": f"{prompt}\n\n合同文本内容：\n{text}"
                }
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4000  # 增加token数量以支持更长的响应
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            # 检查响应状态
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"DeepSeek API调用失败: {response.status_code} - {error_detail}")
                
                # 尝试解析错误信息
                try:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', error_detail)
                except:
                    error_msg = error_detail
                
                return {
                    'success': False,
                    'error': f'API调用失败 ({response.status_code}): {error_msg}'
                }
            
            response.raise_for_status()
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return {
                'success': True,
                'content': content
            }
            
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
            return {
                'success': False,
                'error': f'API调用失败: {error_msg}'
            }
        except Exception as e:
            logger.exception(f"处理API响应失败: {str(e)}")
            return {
                'success': False,
                'error': f'处理响应失败: {str(e)}'
            }
    
    def _extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """提取文件文本内容"""
        try:
            if file_type == 'pdf':
                # 尝试使用pdfplumber提取文本
                try:
                    import pdfplumber
                    text_parts = []
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                    if text_parts:
                        return '\n\n'.join(text_parts)
                except ImportError:
                    logger.warning("pdfplumber未安装，尝试使用PyPDF2")
                    try:
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file_path)
                        text_parts = []
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                        if text_parts:
                            return '\n\n'.join(text_parts)
                    except ImportError:
                        logger.warning("PyPDF2未安装，尝试使用OCR")
                        # 如果PDF是扫描件，使用OCR
                        return self._extract_text_with_ocr(file_path)
                except Exception as e:
                    logger.warning(f"PDF文本提取失败: {str(e)}，尝试使用OCR")
                    return self._extract_text_with_ocr(file_path)
            
            elif file_type in ['image', 'jpg', 'jpeg', 'png']:
                # 图片文件使用OCR提取文本
                return self._extract_text_with_ocr(file_path)
            
            elif file_type == 'docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text_parts = [paragraph.text for paragraph in doc.paragraphs]
                    return '\n'.join(text_parts)
                except ImportError:
                    logger.warning("python-docx未安装，无法提取DOCX文本")
                    return None
                except Exception as e:
                    logger.error(f"DOCX文本提取失败: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            logger.exception(f"提取文件文本失败: {str(e)}")
            return None
    
    def _extract_text_with_ocr(self, file_path: str) -> Optional[str]:
        """使用OCR提取文本（用于扫描PDF或图片）"""
        try:
            # 尝试使用PaddleOCR
            try:
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                
                # 如果是PDF，先转换为图片
                if file_path.lower().endswith('.pdf'):
                    try:
                        from pdf2image import convert_from_path
                        images = convert_from_path(file_path)
                        text_parts = []
                        for img in images:
                            result = ocr.ocr(img, cls=True)
                            if result and result[0]:
                                page_text = '\n'.join([line[1][0] for line in result[0]])
                                text_parts.append(page_text)
                        return '\n\n'.join(text_parts) if text_parts else None
                    except ImportError:
                        logger.warning("pdf2image未安装，无法转换PDF为图片")
                        return None
                else:
                    # 图片文件
                    result = ocr.ocr(file_path, cls=True)
                    if result and result[0]:
                        return '\n'.join([line[1][0] for line in result[0]])
                    return None
            except ImportError:
                logger.warning("PaddleOCR未安装，无法使用OCR功能")
                return None
            except Exception as e:
                logger.error(f"OCR提取失败: {str(e)}")
                return None
                
        except Exception as e:
            logger.exception(f"OCR处理失败: {str(e)}")
            return None
    
    def _parse_recognition_result(self, content: str) -> Dict[str, Any]:
        """解析识别结果"""
        try:
            # 尝试提取JSON部分
            # 如果返回的内容包含代码块，提取代码块内容
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                json_str = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                json_str = content[start:end].strip()
            else:
                # 尝试直接解析
                json_str = content.strip()
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 确保所有字段都存在
            result = {
                'contract_name': data.get('contract_name', ''),
                'contract_number': data.get('contract_number', ''),
                'contract_type': data.get('contract_type', ''),
                'contract_amount': data.get('contract_amount', ''),
                'contract_date': data.get('contract_date', ''),
                'effective_date': data.get('effective_date', ''),
                'start_date': data.get('start_date', ''),
                'end_date': data.get('end_date', ''),
                'party_a': data.get('party_a', {}),
                'party_b': data.get('party_b', {}),
                'description': data.get('description', ''),
                'notes': data.get('notes', '')
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 内容: {content[:200]}")
            # 如果JSON解析失败，返回空结果
            return {
                'contract_name': '',
                'contract_number': '',
                'contract_type': '',
                'contract_amount': '',
                'contract_date': '',
                'effective_date': '',
                'start_date': '',
                'end_date': '',
                'party_a': {},
                'party_b': {},
                'description': content[:500] if content else '',  # 至少保存部分原始内容
                'notes': ''
            }
        except Exception as e:
            logger.exception(f"解析识别结果失败: {str(e)}")
            return {
                'contract_name': '',
                'contract_number': '',
                'contract_type': '',
                'contract_amount': '',
                'contract_date': '',
                'effective_date': '',
                'start_date': '',
                'end_date': '',
                'party_a': {},
                'party_b': {},
                'description': '',
                'notes': ''
            }
