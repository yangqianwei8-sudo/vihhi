#!/usr/bin/env python3
"""
发票OCR识别功能 - 安装验证脚本
用于验证OCR相关依赖是否正确安装
"""
import sys
import os

def check_system_dependencies():
    """检查系统依赖"""
    print("=" * 50)
    print("检查系统依赖...")
    print("=" * 50)
    
    # 检查poppler-utils
    if os.system("which pdftoppm > /dev/null 2>&1") == 0:
        print("✅ poppler-utils 已安装")
    else:
        print("❌ poppler-utils 未安装")
        print("   安装命令: sudo apt-get install poppler-utils")
        return False
    
    # 检查tesseract（可选）
    if os.system("which tesseract > /dev/null 2>&1") == 0:
        print("✅ tesseract-ocr 已安装")
        os.system("tesseract --version 2>&1 | head -1")
    else:
        print("⚠️  tesseract-ocr 未安装（可选，备选OCR引擎）")
    
    return True

def check_python_modules():
    """检查Python模块"""
    print("\n" + "=" * 50)
    print("检查Python模块...")
    print("=" * 50)
    
    modules = {
        'paddleocr': 'PaddleOCR（主要OCR引擎）',
        'paddle': 'PaddlePaddle（PaddleOCR依赖，导入名为paddle）',
        'pdf2image': 'pdf2image（PDF转图片）',
        'pytesseract': 'pytesseract（Tesseract OCR接口）',
    }
    
    all_ok = True
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"✅ {module} 已安装 - {desc}")
        except ImportError:
            # paddlepaddle的导入名是paddle
            if module == 'paddle':
                try:
                    import paddlepaddle
                    print(f"✅ paddlepaddle 已安装 - {desc}")
                except ImportError:
                    print(f"❌ paddlepaddle 未安装 - {desc}")
                    all_ok = False
            else:
                print(f"❌ {module} 未安装 - {desc}")
                all_ok = False
    
    return all_ok

def test_ocr_service():
    """测试OCR服务初始化"""
    print("\n" + "=" * 50)
    print("测试OCR服务...")
    print("=" * 50)
    
    try:
        # 添加项目路径到sys.path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from backend.apps.financial_management.invoice_ocr_service import get_ocr_service
        
        print("正在初始化OCR服务...")
        service = get_ocr_service()
        
        if service.ocr_engine:
            if isinstance(service.ocr_engine, str):
                print(f"✅ OCR服务初始化成功 - 使用引擎: {service.ocr_engine}")
            else:
                print(f"✅ OCR服务初始化成功 - 使用引擎: {type(service.ocr_engine).__name__}")
            return True
        else:
            print("⚠️  OCR引擎未初始化，请检查依赖安装")
            return False
            
    except Exception as e:
        print(f"❌ OCR服务初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("发票OCR识别功能 - 安装验证")
    print("=" * 50 + "\n")
    
    # 检查系统依赖
    sys_ok = check_system_dependencies()
    
    # 检查Python模块
    py_ok = check_python_modules()
    
    # 测试OCR服务
    if sys_ok and py_ok:
        ocr_ok = test_ocr_service()
    else:
        print("\n⚠️  由于依赖未完全安装，跳过OCR服务测试")
        ocr_ok = False
    
    # 总结
    print("\n" + "=" * 50)
    print("验证结果总结")
    print("=" * 50)
    
    if sys_ok and py_ok and ocr_ok:
        print("✅ 所有检查通过！OCR功能已就绪")
        print("\n📝 使用说明:")
        print("   1. 在发票创建/编辑页面")
        print("   2. 上传发票文件（PDF或图片）")
        print("   3. 点击'智能识别'按钮")
        print("   4. 系统会自动识别并填充表单")
        return 0
    else:
        print("❌ 部分检查未通过，请参考以下建议:")
        if not sys_ok:
            print("   - 安装系统依赖: sudo apt-get install poppler-utils")
        if not py_ok:
            print("   - 安装Python依赖: pip install paddleocr paddlepaddle pdf2image pytesseract")
        if not ocr_ok:
            print("   - 检查OCR服务初始化错误信息")
        print("\n💡 提示: 运行 install_ocr_dependencies.sh 脚本可自动安装所有依赖")
        return 1

if __name__ == '__main__':
    sys.exit(main())

