#!/usr/bin/env python
"""
OCR服务测试脚本
用于验证发票OCR识别功能是否正常工作
"""
import os
import sys
import django

# 设置Django环境
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.financial_management.invoice_ocr_service import get_ocr_service


def test_ocr_service():
    """测试OCR服务"""
    print("=" * 60)
    print("发票OCR服务测试")
    print("=" * 60)
    
    # 获取OCR服务实例
    print("\n1. 初始化OCR服务...")
    try:
        ocr_service = get_ocr_service()
        if ocr_service.ocr_engine is None:
            print("❌ OCR引擎未初始化")
            print("   请确保已安装PaddleOCR或Tesseract OCR")
            return False
        elif isinstance(ocr_service.ocr_engine, str) and ocr_service.ocr_engine == 'tesseract':
            print("✓ Tesseract OCR引擎已初始化")
        else:
            print("✓ PaddleOCR引擎已初始化")
    except Exception as e:
        print(f"❌ OCR服务初始化失败: {str(e)}")
        return False
    
    # 测试PDF转图片功能
    print("\n2. 测试PDF转图片功能...")
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image模块可用")
        
        # 检查poppler工具
        import subprocess
        result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ poppler工具已安装")
        else:
            print("⚠️  poppler工具未找到，PDF转图片功能可能不可用")
    except ImportError:
        print("❌ pdf2image模块未安装")
        return False
    except Exception as e:
        print(f"⚠️  检查poppler工具时出错: {str(e)}")
    
    # 测试OCR识别功能（如果有测试图片）
    print("\n3. OCR识别功能测试...")
    print("   提示：OCR识别需要实际的发票图片或PDF文件")
    print("   您可以在发票管理页面上传发票文件进行测试")
    
    print("\n" + "=" * 60)
    print("✓ OCR服务测试完成！")
    print("=" * 60)
    print("\n使用说明：")
    print("1. 在发票创建/编辑页面，选择发票文件（PDF或图片）")
    print("2. 点击'智能识别'按钮")
    print("3. 系统会自动识别并填充发票信息")
    print("\n注意事项：")
    print("- 识别准确率受图片质量影响，建议使用清晰的发票图片")
    print("- 识别结果仅供参考，重要信息请人工核对")
    print("- 首次使用PaddleOCR时会下载模型文件，需要一些时间")
    
    return True


if __name__ == '__main__':
    success = test_ocr_service()
    sys.exit(0 if success else 1)

