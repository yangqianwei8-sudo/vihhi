"""
发票OCR识别服务
支持多种OCR方案：PaddleOCR、Tesseract OCR、第三方API等
"""
import re
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from decimal import Decimal, InvalidOperation
import os

logger = logging.getLogger(__name__)


class InvoiceOCRService:
    """发票OCR识别服务基类"""
    
    def __init__(self):
        self.ocr_engine = None
        self._init_ocr_engine()
    
    def _init_ocr_engine(self):
        """初始化OCR引擎"""
        # 优先尝试使用PaddleOCR（中文识别效果好）
        try:
            from paddleocr import PaddleOCR
            # 新版本PaddleOCR不再支持use_gpu参数，使用默认参数
            self.ocr_engine = PaddleOCR(lang='ch')
            logger.info("已初始化PaddleOCR引擎")
        except ImportError:
            logger.warning("PaddleOCR未安装，尝试使用Tesseract OCR")
            try:
                import pytesseract
                from PIL import Image
                self.ocr_engine = 'tesseract'
                logger.info("已初始化Tesseract OCR引擎")
            except ImportError:
                logger.warning("OCR引擎未安装，请安装PaddleOCR或Tesseract OCR")
                self.ocr_engine = None
    
    def recognize_invoice(self, file_path: str) -> Dict[str, Any]:
        """
        识别发票信息
        
        Args:
            file_path: 发票文件路径（支持PDF、图片）
            
        Returns:
            识别结果字典，包含发票字段信息
        """
        if not self.ocr_engine:
            return {
                'success': False,
                'message': 'OCR引擎未初始化，请安装PaddleOCR或Tesseract OCR'
            }
        
        try:
            # 如果是PDF，先转换为图片
            if file_path.lower().endswith('.pdf'):
                images = self._pdf_to_images(file_path)
                if not images:
                    return {'success': False, 'message': 'PDF文件无法转换为图片'}
                # 使用第一页进行识别
                # 将PIL Image保存为临时文件
                import tempfile
                from PIL import Image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
                    images[0].save(tmp_img.name, 'PNG')
                    tmp_img_path = tmp_img.name
                try:
                    text = self._ocr_image(tmp_img_path)
                finally:
                    # 清理临时图片文件
                    try:
                        os.remove(tmp_img_path)
                    except:
                        pass
            else:
                # 直接识别图片
                text = self._ocr_image(file_path)
            
            # 记录识别的原始文本（用于调试）
            logger.debug(f"OCR识别文本长度: {len(text)} 字符")
            
            # 解析发票信息
            invoice_data = self._parse_invoice_text(text)
            invoice_data['success'] = True
            return invoice_data
            
        except Exception as e:
            logger.exception(f"发票识别失败: {str(e)}")
            return {
                'success': False,
                'message': f'发票识别失败: {str(e)}'
            }
    
    def _ocr_image(self, image_path: str) -> str:
        """OCR识别图片文字"""
        if isinstance(self.ocr_engine, str) and self.ocr_engine == 'tesseract':
            # 使用Tesseract OCR
            import pytesseract
            from PIL import Image
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text
        else:
            # 使用PaddleOCR
            result = self.ocr_engine.ocr(image_path, cls=True)
            # 提取所有文字
            text_lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        text_lines.append(line[1][0])  # line[1][0]是识别的文字
            return '\n'.join(text_lines)
    
    def _pdf_to_images(self, pdf_path: str) -> list:
        """将PDF转换为图片列表"""
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=300)
            return images
        except ImportError:
            logger.warning("pdf2image未安装，无法转换PDF")
            return []
        except Exception as e:
            logger.error(f"PDF转图片失败: {str(e)}，请确保已安装poppler-utils")
            return []
    
    def _parse_invoice_text(self, text: str) -> Dict[str, Any]:
        """
        解析发票文本，提取关键信息
        
        支持识别：
        - 发票代码
        - 发票号码
        - 开票日期
        - 金额（不含税）
        - 税额
        - 价税合计
        - 购买方名称（客户名称）
        - 销售方名称（供应商名称）
        """
        result = {
            'invoice_code': '',
            'invoice_number': '',
            'invoice_date': '',
            'amount': None,
            'tax_amount': None,
            'total_amount': None,
            'customer_name': '',
            'supplier_name': '',
            'invoice_type': '',  # 'incoming' 或 'outgoing'
        }
        
        # 保存原始文本用于调试
        original_text = text
        
        # 清理文本，但保留换行符用于多行匹配
        # 先替换多个空格为单个空格
        text = re.sub(r'\s+', ' ', text)
        # 保留换行符，但统一换行符格式
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 识别发票代码（通常是10-12位数字）
        invoice_code_patterns = [
            r'发票代码[：:]\s*(\d{10,12})',
            r'代码[：:]\s*(\d{10,12})',
            r'发票代码\s*(\d{10,12})',
            r'代码\s*(\d{10,12})',
            # 更宽松的匹配，允许中间有空格
            r'发票代码[：:]\s*(\d{4,6}\s*\d{4,6})',
        ]
        for pattern in invoice_code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).replace(' ', '').replace('\n', '')
                if len(code) >= 10 and len(code) <= 12:
                    result['invoice_code'] = code
                    break
        
        # 识别发票号码（通常是8位数字，也可能是更多位）
        invoice_number_patterns = [
            r'发票号码[：:]\s*(\d{8,12})',
            r'号码[：:]\s*(\d{8,12})',
            r'发票号码\s*(\d{8,12})',
            r'号码\s*(\d{8,12})',
            r'No[\.：:]\s*(\d{8,12})',
            r'NO[\.：:]\s*(\d{8,12})',
        ]
        for pattern in invoice_number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1).replace(' ', '').replace('\n', '')
                if len(number) >= 8:
                    result['invoice_number'] = number
                    break
        
        # 识别开票日期（支持多种格式）
        date_patterns = [
            r'开票日期[：:]\s*(\d{4})[年\-/\s](\d{1,2})[月\-/\s](\d{1,2})[日]?',
            r'日期[：:]\s*(\d{4})[年\-/\s](\d{1,2})[月\-/\s](\d{1,2})[日]?',
            r'开票日期[：:]\s*(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',
            r'日期[：:]\s*(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',
            r'(\d{4})[年\-/\s](\d{1,2})[月\-/\s](\d{1,2})[日]?',
            r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                try:
                    # 验证日期有效性
                    year_int = int(year)
                    month_int = int(month)
                    day_int = int(day)
                    # 基本验证：年份在2000-2100之间，月份1-12，日期1-31
                    if 2000 <= year_int <= 2100 and 1 <= month_int <= 12 and 1 <= day_int <= 31:
                        result['invoice_date'] = f"{year}-{str(month_int).zfill(2)}-{str(day_int).zfill(2)}"
                        break
                except (ValueError, IndexError):
                    continue
        
        # 识别金额（不含税）- 改进正则表达式，支持更多格式
        amount_patterns = [
            r'不含税金额[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'金额[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'合计[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'小计[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    result['amount'] = Decimal(amount_str)
                    break
                except (ValueError, InvalidOperation):
                    pass
        
        # 识别税额
        tax_patterns = [
            r'税额[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'税[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'增值税[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    tax_str = match.group(1).replace(',', '').replace(' ', '')
                    result['tax_amount'] = Decimal(tax_str)
                    break
                except (ValueError, InvalidOperation):
                    pass
        
        # 识别价税合计（优先匹配，因为通常最明显）
        total_patterns = [
            r'价税合计[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'合计[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'总计[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'总计金额[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
            r'合计金额[：:]\s*[￥¥]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    total_str = match.group(1).replace(',', '').replace(' ', '')
                    result['total_amount'] = Decimal(total_str)
                    break
                except (ValueError, InvalidOperation):
                    pass
        
        # 如果识别到了价税合计和税额，但没有金额，可以计算
        if result['total_amount'] and result['tax_amount'] and not result['amount']:
            try:
                result['amount'] = result['total_amount'] - result['tax_amount']
            except:
                pass
        
        # 识别购买方名称（客户名称）- 支持多行匹配
        customer_patterns = [
            r'购买方[：:]\s*名称[：:]\s*([^\n\r]+)',
            r'购买方名称[：:]\s*([^\n\r]+)',
            r'客户名称[：:]\s*([^\n\r]+)',
            r'购买方\s*名称[：:]\s*([^\n\r]+)',
            # 多行匹配：购买方名称后可能换行
            r'购买方[：:]\s*名称[：:]\s*\n\s*([^\n\r]+)',
        ]
        for pattern in customer_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # 清理名称，移除多余的空格和特殊字符
                name = re.sub(r'\s+', '', name)
                # 移除常见的标点符号
                name = name.strip('：:，,。.')
                if len(name) > 0 and len(name) < 200:  # 合理的公司名称长度
                    result['customer_name'] = name
                    result['invoice_type'] = 'outgoing'  # 销项发票
                    break
        
        # 识别销售方名称（供应商名称）- 支持多行匹配
        supplier_patterns = [
            r'销售方[：:]\s*名称[：:]\s*([^\n\r]+)',
            r'销售方名称[：:]\s*([^\n\r]+)',
            r'供应商名称[：:]\s*([^\n\r]+)',
            r'销售方\s*名称[：:]\s*([^\n\r]+)',
            # 多行匹配：销售方名称后可能换行
            r'销售方[：:]\s*名称[：:]\s*\n\s*([^\n\r]+)',
        ]
        for pattern in supplier_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # 清理名称
                name = re.sub(r'\s+', '', name)
                name = name.strip('：:，,。.')
                if len(name) > 0 and len(name) < 200:
                    result['supplier_name'] = name
                    if not result['invoice_type']:
                        result['invoice_type'] = 'incoming'  # 进项发票
                    break
        
        # 如果没有识别到类型，根据是否有客户名称判断
        if not result['invoice_type']:
            if result['customer_name']:
                result['invoice_type'] = 'outgoing'
            elif result['supplier_name']:
                result['invoice_type'] = 'incoming'
        
        return result


# 全局OCR服务实例
_ocr_service = None

def get_ocr_service() -> InvoiceOCRService:
    """获取OCR服务实例（单例模式）"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = InvoiceOCRService()
    return _ocr_service

