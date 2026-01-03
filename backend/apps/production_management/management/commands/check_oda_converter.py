"""
检查ODA File Converter是否已安装的Django管理命令
使用方法: python manage.py check_oda_converter
"""
from django.core.management.base import BaseCommand
import os
import shutil
import subprocess


class Command(BaseCommand):
    help = '检查ODA File Converter是否已正确安装'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('检查 ODA File Converter 安装状态'))
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # 检查1: 系统PATH中查找
        self.stdout.write('1. 检查系统PATH中的命令...')
        converter_found = False
        converter_path = None
        
        # Windows和Linux的命令名可能不同
        commands_to_check = ['DWGConvert', 'DWGConvert.exe']
        
        for cmd in commands_to_check:
            path = shutil.which(cmd)
            if path:
                converter_found = True
                converter_path = path
                self.stdout.write(self.style.SUCCESS(f'   ✓ 找到命令: {cmd}'))
                self.stdout.write(f'     路径: {path}')
                break
        
        if not converter_found:
            self.stdout.write(self.style.WARNING('   ✗ 未在系统PATH中找到DWGConvert命令'))
        
        self.stdout.write('')

        # 检查2: 检查常见安装路径
        self.stdout.write('2. 检查常见安装路径...')
        common_paths = []
        
        if os.name == 'nt':  # Windows
            common_paths = [
                r'C:\Program Files\ODA\ODAFileConverter\bin\DWGConvert.exe',
                r'C:\Program Files (x86)\ODA\ODAFileConverter\bin\DWGConvert.exe',
                r'C:\ODA\ODAFileConverter\bin\DWGConvert.exe',
            ]
        else:  # Linux/Mac
            common_paths = [
                '/usr/local/bin/DWGConvert',
                '/usr/bin/DWGConvert',
                '/opt/ODAFileConverter/bin/DWGConvert',
                '/opt/ODAFileConverter/ODAFileConverter',  # DEB包安装路径
                os.path.expanduser('~/ODAFileConverter/bin/DWGConvert'),
            ]
        
        found_in_common_path = False
        for path in common_paths:
            if os.path.exists(path):
                found_in_common_path = True
                self.stdout.write(self.style.SUCCESS(f'   ✓ 找到文件: {path}'))
                converter_path = converter_path or path
                break
        
        if not found_in_common_path:
            self.stdout.write(self.style.WARNING('   ✗ 未在常见路径中找到DWGConvert'))
        
        self.stdout.write('')

        # 检查3: 测试命令是否可用
        if converter_path:
            self.stdout.write('3. 测试命令是否可用...')
            try:
                # 尝试运行 --version 或 --help
                result = subprocess.run(
                    [converter_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 or 'version' in result.stdout.lower() or 'version' in result.stderr.lower():
                    self.stdout.write(self.style.SUCCESS('   ✓ 命令可以执行'))
                    if result.stdout:
                        self.stdout.write(f'     输出: {result.stdout.strip()[:100]}')
                else:
                    # 尝试 --help
                    result = subprocess.run(
                        [converter_path, '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self.stdout.write(self.style.SUCCESS('   ✓ 命令可以执行'))
                    else:
                        self.stdout.write(self.style.WARNING('   ⚠ 命令存在但可能无法正常执行'))
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR('   ✗ 文件不存在'))
            except subprocess.TimeoutExpired:
                self.stdout.write(self.style.WARNING('   ⚠ 命令执行超时'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ 测试时出错: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('3. 跳过测试（未找到命令）'))
        
        self.stdout.write('')

        # 检查4: 检查ezdxf是否安装
        self.stdout.write('4. 检查ezdxf库（DXF解析）...')
        try:
            import ezdxf
            self.stdout.write(self.style.SUCCESS('   ✓ ezdxf已安装'))
            self.stdout.write(f'     版本: {ezdxf.__version__ if hasattr(ezdxf, "__version__") else "未知"}')
        except ImportError:
            self.stdout.write(self.style.ERROR('   ✗ ezdxf未安装'))
            self.stdout.write('     安装命令: pip install ezdxf')
        
        self.stdout.write('')

        # 总结
        self.stdout.write('=' * 60)
        self.stdout.write('检查结果总结:')
        self.stdout.write('=' * 60)
        
        if converter_path:
            self.stdout.write(self.style.SUCCESS('✓ ODA File Converter: 已找到'))
            self.stdout.write(f'  路径: {converter_path}')
            self.stdout.write('')
            self.stdout.write('建议:')
            self.stdout.write('  1. 如果命令不在PATH中，请添加到系统PATH')
            self.stdout.write('  2. 或修改代码中的路径配置')
        else:
            self.stdout.write(self.style.ERROR('✗ ODA File Converter: 未找到'))
            self.stdout.write('')
            self.stdout.write('安装步骤:')
            self.stdout.write('  1. 访问: https://www.opendesign.com/guestfiles')
            self.stdout.write('  2. 下载 ODA File Converter')
            self.stdout.write('  3. 安装并添加到系统PATH')
            self.stdout.write('  4. 或参考: ODA_FILE_CONVERTER_SETUP.md')
        
        self.stdout.write('')
        
        # 检查ezdxf
        try:
            import ezdxf
            self.stdout.write(self.style.SUCCESS('✓ ezdxf: 已安装'))
            self.stdout.write('')
            self.stdout.write('功能状态:')
            self.stdout.write('  • DXF文件解析: ✓ 可用')
            if converter_path:
                self.stdout.write('  • DWG文件转换: ✓ 可用')
            else:
                self.stdout.write('  • DWG文件转换: ✗ 需要安装ODA File Converter')
        except ImportError:
            self.stdout.write(self.style.ERROR('✗ ezdxf: 未安装'))
            self.stdout.write('  安装命令: pip install ezdxf')
        
        self.stdout.write('')
        self.stdout.write('=' * 60)

