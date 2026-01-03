#!/usr/bin/env python
"""
CAD解析依赖检查脚本
用于验证所有必需的依赖是否已正确安装
"""
import sys
import os

def check_ezdxf():
    """检查ezdxf库"""
    try:
        import ezdxf
        print(f"✓ ezdxf 已安装 (版本: {ezdxf.__version__})")
        return True
    except ImportError:
        print("✗ ezdxf 未安装")
        print("  安装命令: pip install ezdxf")
        return False

def check_pdf2image():
    """检查pdf2image库"""
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image 已安装")
        return True
    except ImportError:
        print("✗ pdf2image 未安装")
        print("  安装命令: pip install pdf2image")
        return False

def check_oda_converter():
    """检查ODA File Converter"""
    import shutil
    
    # 检查系统PATH
    if shutil.which('DWGConvert') or shutil.which('DWGConvert.exe'):
        print("✓ ODA File Converter 已安装 (在系统PATH中)")
        return True
    
    # 检查常见路径
    common_paths = []
    if os.name == 'nt':  # Windows
        import glob
        version_paths = glob.glob(r'C:\Program Files\ODA\ODAFileConverter*\bin\DWGConvert.exe')
        if version_paths:
            print(f"✓ ODA File Converter 已安装 ({version_paths[0]})")
            return True
        
        common_paths = [
            r'C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe',
            r'C:\Program Files (x86)\ODA\ODAFileConverter\bin\DWGConvert.exe',
        ]
    else:  # Linux/Mac
        common_paths = [
            '/usr/local/bin/DWGConvert',
            '/usr/bin/DWGConvert',
            '/opt/ODAFileConverter/bin/DWGConvert',
            '/opt/ODAFileConverter/ODAFileConverter',  # DEB包安装路径
            os.path.expanduser('~/ODAFileConverter/bin/DWGConvert'),
        ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ ODA File Converter 已安装 ({path})")
            return True
    
    print("✗ ODA File Converter 未安装")
    print("  安装说明: 请查看 ODA_FILE_CONVERTER_SETUP.md")
    print("  注意: 如果没有安装，DWG文件解析功能将不可用，但DXF和PDF仍可正常解析")
    return False

def check_cad_parser_service():
    """检查CAD解析服务"""
    try:
        # 添加路径以便导入
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.join(script_dir, '../../')
        sys.path.insert(0, os.path.abspath(backend_dir))
        
        from apps.production_management.services.cad_parser_service import CADParserService
        parser = CADParserService()
        
        print("\nCAD解析服务状态:")
        if parser.dxf_parser:
            print("  ✓ DXF解析器: 可用")
        else:
            print("  ✗ DXF解析器: 不可用")
        
        if parser.pdf2image:
            print("  ✓ PDF转图片: 可用")
        else:
            print("  ✗ PDF转图片: 不可用")
        
        if parser.cad2image_available:
            print("  ✓ DWG转换器: 可用")
        else:
            print("  ✗ DWG转换器: 不可用 (需要ODA File Converter)")
        
        return True
    except Exception as e:
        print(f"✗ CAD解析服务检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("CAD解析依赖检查")
    print("=" * 60)
    print()
    
    results = []
    
    print("Python库检查:")
    print("-" * 60)
    results.append(("ezdxf", check_ezdxf()))
    results.append(("pdf2image", check_pdf2image()))
    
    print("\n系统工具检查:")
    print("-" * 60)
    results.append(("ODA File Converter", check_oda_converter()))
    
    print("\n服务检查:")
    print("-" * 60)
    check_cad_parser_service()
    
    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print("=" * 60)
    
    all_ok = True
    for name, status in results:
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {name}")
        if not status:
            all_ok = False
    
    print()
    if all_ok:
        print("✓ 所有依赖已安装，CAD解析功能完全可用！")
    else:
        print("⚠ 部分依赖未安装，某些功能可能受限：")
        print("  - DXF文件: 需要ezdxf")
        print("  - PDF文件: 需要pdf2image")
        print("  - DWG文件: 需要ODA File Converter（可选）")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())

