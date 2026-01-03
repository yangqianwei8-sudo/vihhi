"""
测试CAD解析功能的Django管理命令
使用方法: python manage.py test_cad_parser <文件路径>
"""
from django.core.management.base import BaseCommand
import os
import json


class Command(BaseCommand):
    help = '测试CAD文件解析功能'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='要测试的CAD文件路径（支持DXF、DWG、PDF）'
        )
        parser.add_argument(
            '--extract-optimization',
            action='store_true',
            help='提取优化分析所需的关键信息'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='输出JSON文件路径（可选）'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        extract_opt = options.get('extract_optimization', False)
        output_path = options.get('output')

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'文件不存在: {file_path}')
            )
            return

        self.stdout.write(f'正在解析文件: {file_path}')
        self.stdout.write('-' * 60)

        try:
            from apps.production_management.services.cad_parser_service import CADParserService

            parser = CADParserService()

            if extract_opt:
                # 提取优化分析所需的关键信息
                self.stdout.write('提取优化分析信息...')
                result = parser.extract_for_optimization(file_path)
            else:
                # 完整解析
                self.stdout.write('完整解析CAD文件...')
                result = parser.parse_cad_file(file_path)

            if result.get('success'):
                self.stdout.write(self.style.SUCCESS('✓ 解析成功！'))
                self.stdout.write('')

                # 显示摘要信息
                if 'summary' in result:
                    self.stdout.write(f"摘要: {result['summary']}")
                    self.stdout.write('')

                # 显示统计信息
                if 'stats' in result:
                    stats = result['stats']
                    self.stdout.write('统计信息:')
                    self.stdout.write(f"  实体总数: {stats.get('total_entities', 0)}")
                    self.stdout.write(f"  图层数量: {stats.get('layers_count', 0)}")
                    self.stdout.write('')

                # 显示设计参数
                if 'design_params' in result:
                    params = result['design_params']
                    self.stdout.write('设计参数:')
                    if params.get('dimensions'):
                        self.stdout.write(f"  尺寸标注: {len(params['dimensions'])}个")
                    if params.get('texts'):
                        self.stdout.write(f"  文字标注: {len(params['texts'])}个")
                    if params.get('materials'):
                        self.stdout.write(f"  材料信息: {params['materials']}")
                    if params.get('structural_elements'):
                        self.stdout.write('  结构元素:')
                        for elem in params['structural_elements']:
                            self.stdout.write(f"    - {elem['category']}: {elem['count']}个")
                    self.stdout.write('')

                # 显示图层信息（前10个）
                if 'layers' in result:
                    layers = result['layers']
                    self.stdout.write(f'图层信息（共{len(layers)}个，显示前10个）:')
                    for i, (name, info) in enumerate(list(layers.items())[:10]):
                        self.stdout.write(f"  {i+1}. {name} (颜色: {info.get('color')}, 线型: {info.get('linetype')})")
                    if len(layers) > 10:
                        self.stdout.write(f"  ... 还有 {len(layers) - 10} 个图层")
                    self.stdout.write('')

                # 如果是优化提取，显示优化数据
                if extract_opt and 'optimization_data' in result:
                    opt_data = result['optimization_data']
                    self.stdout.write('优化分析数据:')
                    self.stdout.write(f"  摘要: {opt_data.get('summary', '')}")
                    key_params = opt_data.get('key_params', {})
                    if key_params.get('materials'):
                        self.stdout.write(f"  材料: {', '.join(key_params['materials'])}")
                    if key_params.get('structural_info'):
                        for elem in key_params['structural_info']:
                            self.stdout.write(f"  {elem['category']}: {elem['count']}个")
                    self.stdout.write('')

                # 保存到JSON文件
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                    self.stdout.write(self.style.SUCCESS(f'✓ 结果已保存到: {output_path}'))

            else:
                error = result.get('error', '未知错误')
                self.stdout.write(self.style.ERROR(f'✗ 解析失败: {error}'))

        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'导入失败: {str(e)}\n请确保已安装ezdxf: pip install ezdxf')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'发生错误: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())

