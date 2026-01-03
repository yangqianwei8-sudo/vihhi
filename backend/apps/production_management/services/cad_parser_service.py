"""
CAD图纸解析服务
专门用于提取CAD图纸中的设计参数，支持优化咨询分析
"""
import os
import logging
import tempfile
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class CADParserService:
    """CAD图纸解析服务"""
    
    def __init__(self):
        self._init_parsers()
    
    def _init_parsers(self):
        """初始化解析器"""
        # DXF解析器
        try:
            import ezdxf
            self.dxf_parser = ezdxf
            logger.info("✓ ezdxf已加载，支持DXF文件解析")
        except ImportError:
            self.dxf_parser = None
            logger.warning("⚠ ezdxf未安装，DXF解析功能不可用。安装: pip install ezdxf")
        
        # PDF转图片工具
        try:
            from pdf2image import convert_from_path
            self.pdf2image = convert_from_path
            logger.info("✓ pdf2image已加载，支持PDF转图片")
        except ImportError:
            self.pdf2image = None
            logger.warning("⚠ pdf2image未安装，PDF转图片功能不可用。安装: pip install pdf2image")
        
        # CAD转图片工具（需要系统安装ODA File Converter）
        self.cad2image_available = self._check_cad_converter()
    
    def _check_cad_converter(self) -> bool:
        """检查CAD转换工具是否可用"""
        # 检查ODA File Converter是否安装
        # ODA File Converter是免费的命令行工具，可以将DWG转换为DXF
        import shutil
        from django.conf import settings
        
        # 方法1: 从settings中读取自定义路径（优先级最高）
        custom_path = getattr(settings, 'ODA_FILE_CONVERTER_PATH', None)
        if custom_path and os.path.exists(custom_path):
            logger.info(f"使用自定义ODA File Converter路径: {custom_path}")
            return True
        
        # 方法2: 检查系统PATH中的命令
        if shutil.which('DWGConvert') or shutil.which('DWGConvert.exe'):
            return True
        
        # 方法3: 检查常见安装路径
        common_paths = []
        if os.name == 'nt':  # Windows
            # Windows常见路径（包含版本号）
            import glob
            # 检查带版本号的路径
            version_paths = glob.glob(r'C:\Program Files\ODA\ODAFileConverter*\bin\DWGConvert.exe')
            if version_paths:
                return True
            
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
                os.path.expanduser('~/bin/DWGConvert'),
            ]
        
        for path in common_paths:
            if os.path.exists(path):
                return True
        
        return False
    
    def _get_converter_command(self) -> Optional[str]:
        """获取DWG转换命令的完整路径"""
        import shutil
        from django.conf import settings
        
        # 方法1: 从settings中读取自定义路径
        custom_path = getattr(settings, 'ODA_FILE_CONVERTER_PATH', None)
        if custom_path and os.path.exists(custom_path):
            return custom_path
        
        # 方法2: 从PATH中查找
        cmd = shutil.which('DWGConvert') or shutil.which('DWGConvert.exe')
        if cmd:
            return cmd
        
        # 方法3: 检查常见路径
        if os.name == 'nt':  # Windows
            import glob
            version_paths = glob.glob(r'C:\Program Files\ODA\ODAFileConverter*\bin\DWGConvert.exe')
            if version_paths:
                return version_paths[0]  # 返回第一个找到的
            
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
                os.path.expanduser('~/bin/DWGConvert'),
            ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def parse_cad_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        解析CAD文件，提取设计参数
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（dxf/dwg/pdf），如果为None则自动检测
        
        Returns:
            包含解析结果的字典
        """
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        if file_type.lower() == 'dxf':
            return self._parse_dxf(file_path)
        elif file_type.lower() == 'dwg':
            return self._parse_dwg(file_path)
        elif file_type.lower() == 'pdf':
            return self._parse_pdf_cad(file_path)
        else:
            return {
                'success': False,
                'error': f'不支持的文件格式: {file_type}'
            }
    
    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.dxf':
            return 'dxf'
        elif ext == '.dwg':
            return 'dwg'
        elif ext == '.pdf':
            return 'pdf'
        else:
            return 'unknown'
    
    def _parse_dxf(self, file_path: str) -> Dict[str, Any]:
        """解析DXF文件"""
        if not self.dxf_parser:
            return {
                'success': False,
                'error': 'DXF解析器未初始化，请安装ezdxf: pip install ezdxf'
            }
        
        try:
            doc = self.dxf_parser.readfile(file_path)
            modelspace = doc.modelspace()
            
            # 提取图层信息
            layers = {}
            for layer in doc.layers:
                layers[layer.dxf.name] = {
                    'name': layer.dxf.name,
                    'color': layer.dxf.color,
                    'linetype': layer.dxf.linetype,
                    'lineweight': getattr(layer.dxf, 'lineweight', None),
                }
            
            # 提取实体信息（按类型分类）
            entities_by_type = {
                'LINE': [],
                'CIRCLE': [],
                'ARC': [],
                'POLYLINE': [],
                'LWPOLYLINE': [],
                'TEXT': [],
                'MTEXT': [],
                'DIMENSION': [],
                'BLOCK': [],
            }
            
            # 统计信息
            stats = {
                'total_entities': 0,
                'layers_count': len(layers),
            }
            
            # 提取设计参数
            design_params = {
                'dimensions': [],  # 尺寸标注
                'texts': [],       # 文字标注
                'materials': [],   # 材料信息（从文字中提取）
                'structural_elements': [],  # 结构元素
            }
            
            for entity in modelspace:
                stats['total_entities'] += 1
                entity_type = entity.dxftype()
                
                entity_info = {
                    'type': entity_type,
                    'layer': entity.dxf.layer,
                }
                
                # 提取线条信息
                if entity_type == 'LINE':
                    entity_info.update({
                        'start': list(entity.dxf.start),
                        'end': list(entity.dxf.end),
                        'length': self._calculate_distance(entity.dxf.start, entity.dxf.end),
                    })
                    entities_by_type['LINE'].append(entity_info)
                
                # 提取圆形信息
                elif entity_type == 'CIRCLE':
                    entity_info.update({
                        'center': list(entity.dxf.center),
                        'radius': float(entity.dxf.radius),
                        'diameter': float(entity.dxf.radius * 2),
                    })
                    entities_by_type['CIRCLE'].append(entity_info)
                
                # 提取圆弧信息
                elif entity_type == 'ARC':
                    entity_info.update({
                        'center': list(entity.dxf.center),
                        'radius': float(entity.dxf.radius),
                        'start_angle': float(entity.dxf.start_angle),
                        'end_angle': float(entity.dxf.end_angle),
                    })
                    entities_by_type['ARC'].append(entity_info)
                
                # 提取多段线信息
                elif entity_type in ['POLYLINE', 'LWPOLYLINE']:
                    points = []
                    if entity_type == 'LWPOLYLINE':
                        points = [list(point) for point in entity.get_points()]
                    else:
                        points = [list(vertex.dxf.location) for vertex in entity.vertices]
                    
                    entity_info.update({
                        'points': points,
                        'point_count': len(points),
                        'closed': getattr(entity.dxf, 'is_closed', False),
                    })
                    entities_by_type[entity_type].append(entity_info)
                
                # 提取文字信息（可能包含设计参数）
                elif entity_type == 'TEXT':
                    text_content = entity.dxf.text
                    entity_info.update({
                        'text': text_content,
                        'position': list(entity.dxf.insert),
                        'height': float(entity.dxf.height),
                        'rotation': float(getattr(entity.dxf, 'rotation', 0)),
                    })
                    entities_by_type['TEXT'].append(entity_info)
                    
                    # 尝试从文字中提取设计参数
                    params = self._extract_params_from_text(text_content)
                    if params:
                        design_params['texts'].append({
                            'text': text_content,
                            'position': list(entity.dxf.insert),
                            'extracted_params': params,
                        })
                
                # 提取多行文字
                elif entity_type == 'MTEXT':
                    text_content = entity.text
                    entity_info.update({
                        'text': text_content,
                        'position': list(entity.dxf.insert),
                        'height': float(entity.dxf.char_height),
                    })
                    entities_by_type['MTEXT'].append(entity_info)
                    
                    # 尝试从文字中提取设计参数
                    params = self._extract_params_from_text(text_content)
                    if params:
                        design_params['texts'].append({
                            'text': text_content,
                            'position': list(entity.dxf.insert),
                            'extracted_params': params,
                        })
                
                # 提取尺寸标注
                elif entity_type == 'DIMENSION':
                    entity_info.update({
                        'dim_type': getattr(entity.dxf, 'dimtype', 'unknown'),
                        'defpoint': list(entity.dxf.defpoint),
                    })
                    entities_by_type['DIMENSION'].append(entity_info)
                    design_params['dimensions'].append(entity_info)
            
            # 提取结构元素信息（基于图层和实体类型）
            structural_elements = self._identify_structural_elements(
                entities_by_type, layers
            )
            design_params['structural_elements'] = structural_elements
            
            return {
                'success': True,
                'file_type': 'DXF',
                'layers': layers,
                'entities': entities_by_type,
                'stats': stats,
                'design_params': design_params,
                'summary': self._generate_summary(stats, design_params),
            }
            
        except Exception as e:
            logger.error(f"DXF解析失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'DXF解析失败: {str(e)}'
            }
    
    def _parse_dwg(self, file_path: str) -> Dict[str, Any]:
        """解析DWG文件"""
        # DWG文件需要先转换为DXF，然后解析
        # 使用ODA File Converter工具（免费）
        if not self.cad2image_available:
            return {
                'success': False,
                'error': 'DWG文件解析需要ODA File Converter工具。\n'
                         '请访问 https://www.opendesign.com/guestfiles 下载免费的ODA File Converter，\n'
                         '安装后确保DWGConvert命令在系统PATH中。'
            }
        
        try:
            import subprocess
            import tempfile
            import os
            
            # 创建临时DXF文件
            temp_dxf = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
            temp_dxf_path = temp_dxf.name
            temp_dxf.close()
            
            try:
                # 获取转换命令路径
                converter_cmd = self._get_converter_command()
                
                if not converter_cmd:
                    return {
                        'success': False,
                        'error': 'ODA File Converter未找到。请安装并添加到系统PATH，或在settings.py中设置ODA_FILE_CONVERTER_PATH，或参考ODA_FILE_CONVERTER_SETUP.md'
                    }
                
                logger.info(f"使用DWG转换命令: {converter_cmd}")
                
                result = subprocess.run(
                    [converter_cmd, file_path, temp_dxf_path],
                    capture_output=True,
                    text=True,
                    timeout=60  # 增加超时时间到60秒
                )
                
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'DWG转换失败: {result.stderr}'
                    }
                
                # 转换成功后，使用DXF解析器解析
                if not os.path.exists(temp_dxf_path):
                    return {
                        'success': False,
                        'error': 'DXF文件未生成'
                    }
                
                # 解析DXF文件
                parse_result = self._parse_dxf(temp_dxf_path)
                
                # 添加转换信息
                if parse_result.get('success'):
                    parse_result['converted_from'] = 'DWG'
                    parse_result['original_file'] = os.path.basename(file_path)
                
                return parse_result
                
            finally:
                # 清理临时文件
                try:
                    if os.path.exists(temp_dxf_path):
                        os.remove(temp_dxf_path)
                except:
                    pass
                    
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'ODA File Converter未找到。请确保已安装并添加到系统PATH。'
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'DWG转换超时，文件可能过大或损坏'
            }
        except Exception as e:
            logger.error(f"DWG解析失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'DWG解析失败: {str(e)}'
            }
    
    def _parse_pdf_cad(self, file_path: str) -> Dict[str, Any]:
        """解析PDF格式的CAD图纸"""
        # PDF图纸通常是从CAD导出的图片格式
        # 这里返回基本信息，实际识别需要使用Vision API
        return {
            'success': True,
            'file_type': 'PDF',
            'note': 'PDF格式图纸需要使用Vision API进行识别',
            'recommendation': '建议将PDF转换为图片后使用Vision API分析'
        }
    
    def _calculate_distance(self, point1, point2) -> float:
        """计算两点之间的距离"""
        from math import sqrt
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        if len(point1) > 2:
            dz = point2[2] - point1[2]
            return sqrt(dx*dx + dy*dy + dz*dz)
        return sqrt(dx*dx + dy*dy)
    
    def _extract_params_from_text(self, text: str) -> Dict[str, Any]:
        """从文字中提取设计参数"""
        import re
        params = {}
        
        # 提取尺寸信息（如：300x400, H300, 直径200等）
        size_patterns = [
            r'(\d+)\s*[xX×]\s*(\d+)',  # 300x400
            r'[Hh](\d+)',  # H300
            r'[Bb](\d+)',  # B300
            r'直径\s*(\d+)',  # 直径200
            r'Φ\s*(\d+)',  # Φ200
        ]
        
        sizes = []
        for pattern in size_patterns:
            matches = re.findall(pattern, text)
            sizes.extend(matches)
        
        if sizes:
            params['sizes'] = sizes
        
        # 提取材料信息（如：C30, Q235, HRB400等）
        material_patterns = [
            r'[Cc](\d+)',  # C30混凝土
            r'[Qq](\d+)',  # Q235钢材
            r'HRB(\d+)',   # HRB400钢筋
            r'HPB(\d+)',   # HPB300钢筋
        ]
        
        materials = []
        for pattern in material_patterns:
            matches = re.findall(pattern, text)
            materials.extend(matches)
        
        if materials:
            params['materials'] = materials
        
        # 提取厚度信息（如：厚度200, 板厚120等）
        thickness_patterns = [
            r'厚度\s*(\d+)',
            r'板厚\s*(\d+)',
            r'壁厚\s*(\d+)',
        ]
        
        thicknesses = []
        for pattern in thickness_patterns:
            matches = re.findall(pattern, text)
            thicknesses.extend(matches)
        
        if thicknesses:
            params['thicknesses'] = thicknesses
        
        return params if params else None
    
    def _identify_structural_elements(self, entities_by_type: Dict, layers: Dict) -> List[Dict]:
        """识别结构元素"""
        elements = []
        
        # 识别梁（通常用LINE或POLYLINE表示）
        beams = []
        for line in entities_by_type.get('LINE', []):
            length = line.get('length', 0)
            if length > 1000:  # 假设长度大于1000的线条可能是梁
                beams.append({
                    'type': 'beam',
                    'length': round(length, 2),
                    'layer': line['layer'],
                })
        
        # 检查多段线（可能是梁）
        for polyline in entities_by_type.get('POLYLINE', []) + entities_by_type.get('LWPOLYLINE', []):
            points = polyline.get('points', [])
            if len(points) >= 2:
                # 计算多段线的总长度
                total_length = 0
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    if len(p1) >= 2 and len(p2) >= 2:
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        segment_length = (dx*dx + dy*dy) ** 0.5
                        total_length += segment_length
                
                if total_length > 1000:
                    beams.append({
                        'type': 'beam',
                        'length': round(total_length, 2),
                        'layer': polyline.get('layer', ''),
                    })
        
        if beams:
            elements.append({
                'category': 'beams',
                'count': len(beams),
                'details': beams[:10],  # 只返回前10个
            })
        
        # 识别柱（通常用CIRCLE或矩形POLYLINE表示）
        columns = []
        for circle in entities_by_type.get('CIRCLE', []):
            diameter = circle.get('diameter', 0)
            if 200 < diameter < 2000:  # 假设直径在这个范围的圆可能是柱
                columns.append({
                    'type': 'column',
                    'diameter': round(diameter, 2),
                    'layer': circle['layer'],
                })
        
        # 识别矩形（可能是矩形柱）
        for polyline in entities_by_type.get('POLYLINE', []) + entities_by_type.get('LWPOLYLINE', []):
            points = polyline.get('points', [])
            if len(points) == 4 or (len(points) == 5 and polyline.get('closed', False)):
                # 可能是矩形柱
                # 计算矩形的尺寸
                if len(points) >= 2:
                    p1 = points[0]
                    p2 = points[1]
                    if len(p1) >= 2 and len(p2) >= 2:
                        dx = abs(p2[0] - p1[0])
                        dy = abs(p2[1] - p1[1])
                        # 如果尺寸在合理范围内，可能是柱
                        if 200 < max(dx, dy) < 2000:
                            columns.append({
                                'type': 'column',
                                'width': round(dx, 2),
                                'height': round(dy, 2),
                                'layer': polyline.get('layer', ''),
                            })
        
        if columns:
            elements.append({
                'category': 'columns',
                'count': len(columns),
                'details': columns[:10],
            })
        
        # 识别板（通常用闭合的多段线表示，面积较大）
        slabs = []
        for polyline in entities_by_type.get('POLYLINE', []) + entities_by_type.get('LWPOLYLINE', []):
            if polyline.get('closed', False):
                points = polyline.get('points', [])
                if len(points) >= 3:
                    # 简单计算面积（使用鞋带公式）
                    area = 0
                    for i in range(len(points)):
                        j = (i + 1) % len(points)
                        if len(points[i]) >= 2 and len(points[j]) >= 2:
                            area += points[i][0] * points[j][1]
                            area -= points[j][0] * points[i][1]
                    area = abs(area) / 2
                    
                    # 如果面积较大，可能是板
                    if area > 1000000:  # 假设面积大于1000000的可能是板
                        slabs.append({
                            'type': 'slab',
                            'area': round(area, 2),
                            'layer': polyline.get('layer', ''),
                        })
        
        if slabs:
            elements.append({
                'category': 'slabs',
                'count': len(slabs),
                'details': slabs[:10],
            })
        
        return elements
    
    def _generate_summary(self, stats: Dict, design_params: Dict) -> str:
        """生成摘要信息"""
        summary_parts = []
        
        summary_parts.append(f"图纸包含 {stats['total_entities']} 个实体，分布在 {stats['layers_count']} 个图层中。")
        
        if design_params.get('dimensions'):
            summary_parts.append(f"发现 {len(design_params['dimensions'])} 个尺寸标注。")
        
        if design_params.get('texts'):
            summary_parts.append(f"提取了 {len(design_params['texts'])} 个文字标注，其中包含设计参数。")
        
        if design_params.get('structural_elements'):
            for element in design_params['structural_elements']:
                summary_parts.append(f"识别出 {element['count']} 个{element['category']}。")
        
        return " ".join(summary_parts)
    
    def convert_to_image(self, file_path: str, output_path: str = None) -> Optional[str]:
        """
        将CAD文件转换为图片（用于Vision API识别）
        
        Args:
            file_path: CAD文件路径
            output_path: 输出图片路径，如果为None则自动生成
        
        Returns:
            图片文件路径，如果失败返回None
        """
        file_type = self._detect_file_type(file_path)
        
        if file_type == 'pdf' and self.pdf2image:
            try:
                images = self.pdf2image(file_path, dpi=300)
                if images:
                    if output_path is None:
                        output_path = file_path.replace('.pdf', '.png')
                    images[0].save(output_path, 'PNG')
                    return output_path
            except Exception as e:
                logger.error(f"PDF转图片失败: {str(e)}")
        
        # DWG/DXF转图片需要外部工具（如ODA File Converter）
        # 这里返回None，表示需要手动转换
        return None
    
    def extract_for_optimization(self, file_path: str) -> Dict[str, Any]:
        """
        专门用于优化咨询的参数提取
        
        Returns:
            包含优化分析所需的关键信息
        """
        parse_result = self.parse_cad_file(file_path)
        
        if not parse_result.get('success'):
            return parse_result
        
        # 提取优化分析所需的关键信息
        optimization_data = {
            'file_type': parse_result.get('file_type'),
            'summary': parse_result.get('summary', ''),
            'key_params': {
                'dimensions': parse_result.get('design_params', {}).get('dimensions', [])[:20],  # 限制数量
                'materials': self._extract_all_materials(parse_result),
                'structural_info': parse_result.get('design_params', {}).get('structural_elements', []),
            },
            'layer_info': {
                'count': len(parse_result.get('layers', {})),
                'names': list(parse_result.get('layers', {}).keys())[:10],
            },
            'entity_stats': parse_result.get('stats', {}),
        }
        
        return {
            'success': True,
            'optimization_data': optimization_data,
            'full_parse_result': parse_result,  # 保留完整结果供后续使用
        }
    
    def _extract_all_materials(self, parse_result: Dict) -> List[str]:
        """提取所有材料信息"""
        materials = set()
        
        for text_info in parse_result.get('design_params', {}).get('texts', []):
            extracted = text_info.get('extracted_params', {})
            if extracted and 'materials' in extracted:
                materials.update(extracted['materials'])
        
        return list(materials)
    
    def extract_technical_economic_indicators(self, parse_result: Dict) -> Dict[str, Any]:
        """
        提取技术经济指标表
        
        Args:
            parse_result: CAD解析结果
            
        Returns:
            包含技术经济指标的字典
        """
        indicators = {}
        texts = []
        
        # 收集所有文字内容
        for text_info in parse_result.get('entities', {}).get('TEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        for text_info in parse_result.get('entities', {}).get('MTEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        # 查找技术经济指标表的关键词
        indicator_keywords = {
            'total_area': ['总建筑面积', '总用地面积', '总建筑面积（㎡）', '总用地面积（㎡）'],
            'building_area': ['建筑占地面积', '建筑基底面积', '建筑占地面积（㎡）'],
            'plot_ratio': ['容积率', '容积率：', '容积率='],
            'building_density': ['建筑密度', '建筑密度：', '建筑密度='],
            'green_rate': ['绿地率', '绿化率', '绿地率：', '绿化率：'],
            'parking_spaces': ['停车位', '停车位数量', '停车位：', '停车位='],
            'underground_area': ['地下建筑面积', '地下室面积', '地下建筑面积（㎡）'],
            'aboveground_area': ['地上建筑面积', '地上面积', '地上建筑面积（㎡）'],
        }
        
        # 提取数值
        import re
        for keyword_group, keywords in indicator_keywords.items():
            for text_item in texts:
                text = text_item['text']
                for keyword in keywords:
                    if keyword in text:
                        # 尝试提取数值
                        numbers = re.findall(r'\d+\.?\d*', text)
                        if numbers:
                            try:
                                value = float(numbers[0])
                                indicators[keyword_group] = value
                                break
                            except ValueError:
                                pass
        
        return indicators
    
    def extract_drawing_catalog(self, parse_result: Dict) -> Dict[str, List[Dict]]:
        """
        提取图纸目录
        
        Args:
            parse_result: CAD解析结果
            
        Returns:
            按专业分类的图纸目录字典
        """
        catalog = {
            'architecture': [],  # 建筑
            'structure': [],     # 结构
            'mep': [],           # 机电
            'electrical': [],    # 电气
            'plumbing': [],       # 给排水
            'other': [],          # 其他
        }
        
        texts = []
        
        # 收集所有文字内容
        for text_info in parse_result.get('entities', {}).get('TEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        for text_info in parse_result.get('entities', {}).get('MTEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        # 专业关键词映射
        profession_keywords = {
            'architecture': ['建施', '建筑', '建筑图', 'A-', '建-'],
            'structure': ['结施', '结构', '结构图', 'S-', '结-'],
            'mep': ['设施', '机电', 'MEP', 'M-'],
            'electrical': ['电施', '电气', '电气图', 'E-', '电-'],
            'plumbing': ['水施', '给排水', '给水', '排水', 'W-', '水-'],
        }
        
        import re
        
        # 识别图纸目录行
        for text_item in texts:
            text = text_item['text'].strip()
            
            # 跳过空文本
            if not text:
                continue
            
            # 识别专业
            profession = 'other'
            for prof, keywords in profession_keywords.items():
                if any(keyword in text for keyword in keywords):
                    profession = prof
                    break
            
            # 尝试提取图纸信息
            sheet_info = self._parse_drawing_sheet_info(text)
            if sheet_info:
                catalog[profession].append(sheet_info)
        
        # 清理空列表
        catalog = {k: v for k, v in catalog.items() if v}
        
        return catalog
    
    def _parse_drawing_sheet_info(self, text: str) -> Dict[str, Any]:
        """
        解析单行图纸信息
        
        Args:
            text: 图纸目录行文本
            
        Returns:
            图纸信息字典，如果无法解析则返回None
        """
        import re
        
        # 提取图纸编号（如：A-01, 建施-01, S-02等）
        sheet_number_match = re.search(r'([A-Z]|建施|结施|电施|水施|设施)[-－]?\s*(\d+)', text)
        sheet_number = sheet_number_match.group(0) if sheet_number_match else ''
        
        # 提取图纸名称
        sheet_name_match = re.search(r'[A-Z][-－]?\d+\s*[：:]\s*([^，,]+)', text)
        if not sheet_name_match:
            sheet_name_match = re.search(r'[-－]\d+\s*[：:]\s*([^，,]+)', text)
        sheet_name = sheet_name_match.group(1).strip() if sheet_name_match else text[:50]
        
        # 提取单体名称（如：1#楼、2#楼等）
        building_match = re.search(r'(\d+)[#号]?楼', text)
        building_name = building_match.group(0) if building_match else ''
        
        # 提取建筑面积
        area_match = re.search(r'(\d+\.?\d*)\s*[㎡平方米]', text)
        building_area = float(area_match.group(1)) if area_match else None
        
        # 提取层数
        floors_match = re.search(r'(\d+)\s*层', text)
        floors = int(floors_match.group(1)) if floors_match else None
        
        # 提取层高
        floor_height_match = re.search(r'层高[：:]?\s*(\d+\.?\d*)\s*[m米]', text)
        if not floor_height_match:
            floor_height_match = re.search(r'(\d+\.?\d*)\s*[m米]\s*层高', text)
        floor_height = float(floor_height_match.group(1)) if floor_height_match else None
        
        # 提取地下层数
        underground_match = re.search(r'地下\s*(\d+)\s*层', text)
        underground_floors = int(underground_match.group(1)) if underground_match else None
        
        # 如果至少提取到图纸编号或名称，则返回信息
        if sheet_number or sheet_name:
            return {
                'sheet_number': sheet_number,
                'sheet_name': sheet_name,
                'building_name': building_name,
                'building_area': building_area,
                'floors': floors,
                'floor_height': floor_height,
                'underground_floors': underground_floors,
                'description': text[:200],  # 保留原始文本作为描述
            }
        
        return None
    
    def extract_basic_info(self, parse_result: Dict) -> Dict[str, str]:
        """
        提取基本信息（设计单位、图纸版本、总说明等）
        
        Args:
            parse_result: CAD解析结果
            
        Returns:
            包含基本信息的字典
        """
        basic_info = {
            'design_unit': '',
            'drawing_version': '',
            'general_description': '',
        }
        
        texts = []
        
        # 收集所有文字内容
        for text_info in parse_result.get('entities', {}).get('TEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        for text_info in parse_result.get('entities', {}).get('MTEXT', []):
            texts.append({
                'text': text_info.get('text', ''),
                'position': text_info.get('position', [0, 0]),
            })
        
        import re
        
        # 提取设计单位
        design_unit_keywords = ['设计单位', '设计院', '设计公司', 'Design Unit', 'Designer']
        for text_item in texts:
            text = text_item['text']
            for keyword in design_unit_keywords:
                if keyword in text:
                    # 尝试提取设计单位名称
                    match = re.search(rf'{keyword}[：:]\s*([^\n\r]+)', text)
                    if match:
                        basic_info['design_unit'] = match.group(1).strip()
                        break
                    # 如果没有冒号，尝试提取关键词后的文本
                    idx = text.find(keyword)
                    if idx >= 0:
                        remaining = text[idx + len(keyword):].strip()
                        if remaining and len(remaining) < 100:
                            basic_info['design_unit'] = remaining
                            break
        
        # 提取图纸版本
        version_keywords = ['版本', 'Version', 'V', '版次', 'Rev']
        for text_item in texts:
            text = text_item['text']
            for keyword in version_keywords:
                if keyword in text:
                    # 尝试提取版本号
                    match = re.search(rf'{keyword}[：:]\s*([A-Z0-9.]+)', text, re.IGNORECASE)
                    if match:
                        basic_info['drawing_version'] = match.group(1).strip()
                        break
        
        # 提取总说明（通常是大段文本）
        description_keywords = ['总说明', '设计说明', '工程说明', 'General Description']
        description_texts = []
        for text_item in texts:
            text = text_item['text']
            for keyword in description_keywords:
                if keyword in text:
                    # 收集说明文本
                    if len(text) > 50:  # 说明通常比较长
                        description_texts.append(text)
        
        if description_texts:
            basic_info['general_description'] = '\n'.join(description_texts[:3])  # 最多取前3段
        
        return basic_info
    
    def parse_for_pre_optimization(self, file_path: str) -> Dict[str, Any]:
        """
        专门用于优化前资料的完整解析
        
        Args:
            file_path: CAD文件路径
            
        Returns:
            包含所有提取信息的完整字典
        """
        # 基础解析
        parse_result = self.parse_cad_file(file_path)
        
        if not parse_result.get('success'):
            return parse_result
        
        # 提取技术经济指标
        indicators = self.extract_technical_economic_indicators(parse_result)
        
        # 提取图纸目录
        catalog = self.extract_drawing_catalog(parse_result)
        
        # 提取基本信息
        basic_info = self.extract_basic_info(parse_result)
        
        # 组合结果
        result = {
            'success': True,
            'file_type': parse_result.get('file_type'),
            'basic_info': basic_info,
            'technical_economic_indicators': indicators,
            'drawing_catalog': catalog,
            'layers': parse_result.get('layers', {}),
            'entities': parse_result.get('entities', {}),
            'design_params': parse_result.get('design_params', {}),
            'stats': parse_result.get('stats', {}),
            'full_parse_result': parse_result,  # 保留完整解析结果
        }
        
        return result

