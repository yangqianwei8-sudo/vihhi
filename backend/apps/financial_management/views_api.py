"""
财务管理API视图
用于处理AJAX请求
"""
import os
import tempfile
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings

from .invoice_ocr_service import get_ocr_service

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def recognize_invoice(request):
    """
    识别发票信息API
    
    接收发票文件（PDF或图片），返回识别结果
    """
    try:
        # 检查是否有上传文件
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '请上传发票文件'
            })
        
        uploaded_file: UploadedFile = request.FILES['file']
        
        # 检查文件类型
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'message': f'不支持的文件格式，支持格式：{", ".join(allowed_extensions)}'
            })
        
        # 检查文件大小（限制10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': '文件大小不能超过10MB'
            })
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # 调用OCR服务识别发票
            ocr_service = get_ocr_service()
            result = ocr_service.recognize_invoice(tmp_file_path)
            
            if result.get('success'):
                # 格式化返回数据
                invoice_data = {
                    'success': True,
                    'data': {
                        'invoice_code': result.get('invoice_code', ''),
                        'invoice_number': result.get('invoice_number', ''),
                        'invoice_date': result.get('invoice_date', ''),
                        'amount': str(result.get('amount', '')) if result.get('amount') else '',
                        'tax_amount': str(result.get('tax_amount', '')) if result.get('tax_amount') else '',
                        'total_amount': str(result.get('total_amount', '')) if result.get('total_amount') else '',
                        'customer_name': result.get('customer_name', ''),
                        'supplier_name': result.get('supplier_name', ''),
                        'invoice_type': result.get('invoice_type', ''),
                    },
                    'message': '识别成功'
                }
                return JsonResponse(invoice_data)
            else:
                return JsonResponse({
                    'success': False,
                    'message': result.get('message', '识别失败')
                })
        
        finally:
            # 删除临时文件
            try:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")
    
    except Exception as e:
        logger.exception(f"发票识别API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        })

