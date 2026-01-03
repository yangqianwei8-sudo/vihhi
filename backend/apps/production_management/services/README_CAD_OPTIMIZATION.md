# CAD图纸优化咨询功能说明

## 功能概述

本功能实现了CAD图纸的自动解析和设计参数提取，结合AI顾问系统提供优化咨询建议。

## 技术方案

**方案B：ODA File Converter + ezdxf**

- **DWG文件**：使用ODA File Converter（免费）转换为DXF
- **DXF文件**：使用ezdxf直接解析
- **PDF文件**：转换为图片后使用Vision API识别
- **图片文件**：直接使用Vision API识别

## 文件结构

```
backend/apps/production_management/services/
├── cad_parser_service.py          # CAD文件解析服务
├── ai_advisor_service.py          # AI顾问服务（已集成CAD解析）
├── ODA_FILE_CONVERTER_SETUP.md    # ODA File Converter安装指南
└── README_CAD_OPTIMIZATION.md     # 本文件
```

## 核心功能

### 1. CAD文件解析 (`CADParserService`)

**支持格式：**
- DXF（直接解析）
- DWG（转换为DXF后解析）
- PDF（转换为图片）

**提取信息：**
- 图层信息（名称、颜色、线型）
- 实体信息（线条、圆形、圆弧、多段线、文字等）
- 尺寸标注
- 文字标注
- 设计参数（材料、尺寸、厚度等）

### 2. AI优化分析 (`AIAdvisorService`)

**集成方式：**
- CAD解析结果自动作为上下文提供给AI
- 结合用户描述和CAD参数生成优化建议

**输出内容：**
- 优化方案（多个方案，包含节省金额、风险等级）
- 相似案例
- 分析报告
- 风险评估

## 使用流程

### 后端使用

```python
from apps.production_management.services.cad_parser_service import CADParserService

# 初始化
parser = CADParserService()

# 解析CAD文件
result = parser.parse_cad_file('drawing.dwg')
if result['success']:
    # 提取优化分析所需的关键信息
    opt_data = parser.extract_for_optimization('drawing.dwg')
    print(opt_data['optimization_data']['summary'])
```

### 前端使用

1. 访问AI顾问页面：`/production/ai-advisor/`
2. 填写问题描述和约束条件
3. 上传CAD文件（DWG/DXF）或图片
4. 点击"提交问题并获取优化建议"
5. 查看AI生成的优化方案

## API接口

### 分析接口

**URL:** `POST /production/api/ai-advisor/analyze/`

**请求格式：**
- FormData（支持文件上传）
- JSON（仅文本）

**参数：**
- `problem`: 优化前做法（必填）
- `constraints`: 约束条件（可选）
- `service_type_id`: 服务类型ID（可选）
- `profession_code`: 专业代码（可选）
- `budget_impact`: 预算影响（可选）
- `images`: 图片数组（base64，可选）
- `cad_file`: CAD文件（文件上传，可选）

**响应：**
```json
{
    "summary": "分析总结",
    "solutions": [
        {
            "title": "方案名称",
            "description": "方案描述",
            "savings": 12.5,
            "risk": "low",
            "advantages": ["优势1", "优势2"],
            "disadvantages": ["注意事项1"]
        }
    ],
    "similar_cases": [],
    "analysis_report": {
        "content": "分析报告HTML内容"
    },
    "risk_assessment": [
        {
            "title": "风险名称",
            "level": "low",
            "description": "风险描述"
        }
    ]
}
```

## 安装要求

### 必需依赖

```bash
pip install ezdxf
```

### 可选依赖（用于DWG支持）

1. **ODA File Converter**（免费）
   - 下载：https://www.opendesign.com/guestfiles
   - 安装后添加到系统PATH
   - 详见：`ODA_FILE_CONVERTER_SETUP.md`

2. **pdf2image**（用于PDF转图片）
   ```bash
   pip install pdf2image
   # 需要系统安装poppler
   ```

## 配置说明

### 自动检测ODA File Converter

代码会自动检测系统PATH中的`DWGConvert`命令。如果未找到，会提示用户安装。

### 手动指定路径

如需手动指定ODA File Converter路径，修改 `cad_parser_service.py` 中的 `_check_cad_converter()` 方法。

## 性能考虑

1. **文件大小限制**
   - 建议限制上传文件大小（如50MB）
   - 大文件转换需要较长时间

2. **异步处理**
   - 对于大文件，建议使用Celery异步任务
   - 避免阻塞HTTP请求

3. **缓存机制**
   - 相同文件的解析结果可以缓存
   - 减少重复转换和解析

## 错误处理

### 常见错误

1. **DWG转换失败**
   - 检查ODA File Converter是否安装
   - 检查文件是否损坏
   - 查看日志获取详细错误

2. **DXF解析失败**
   - 检查ezdxf是否安装
   - 检查文件格式是否正确

3. **AI分析失败**
   - 检查DeepSeek API配置
   - 查看日志获取错误详情
   - 系统会自动返回模拟数据作为后备

## 测试

```bash
# 测试DXF解析
python manage.py shell
>>> from apps.production_management.services.cad_parser_service import CADParserService
>>> parser = CADParserService()
>>> result = parser.parse_cad_file('test.dxf')
>>> print(result['success'])

# 测试DWG转换（需要ODA File Converter）
>>> result = parser.parse_cad_file('test.dwg')
>>> print(result['success'])
```

## 后续优化方向

1. **支持更多CAD格式**
   - DGN（MicroStation）
   - IFC（BIM格式）

2. **增强参数提取**
   - 更智能的材料识别
   - 更精确的尺寸提取
   - 结构元素自动识别

3. **性能优化**
   - 异步处理大文件
   - 结果缓存
   - 批量处理

4. **用户体验**
   - 上传进度显示
   - 解析状态反馈
   - 错误提示优化

## 技术支持

- CAD解析问题：查看 `cad_parser_service.py`
- AI分析问题：查看 `ai_advisor_service.py`
- ODA安装问题：查看 `ODA_FILE_CONVERTER_SETUP.md`
- 项目问题反馈：联系开发团队

