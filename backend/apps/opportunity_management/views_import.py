# 商机管理 - 批量导入视图

from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .views_common import (
    _build_opportunity_management_sidebar_nav,
    get_user_permission_codes,
    BusinessOpportunity,
    Client,
    ClientType,
    DesignStage,
    ServiceType,
)
from .perm_check import opportunity_can_view

def opportunity_import(request):
    """商机批量导入功能"""
    from django.http import HttpResponse
    from django.db import transaction
    from backend.apps.system_management.models import User
    from backend.apps.base_data.models import ServiceType, DesignStage
    import csv
    import io
    
    permission_set = get_user_permission_codes(request.user)
    
    # 检查权限：需要商机管理权限
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限执行商机导入操作')
        return redirect('opportunity_pages:opportunity_management')
    
    # 下载模板
    if request.GET.get('download') == 'template':
        service_type_sample_obj = ServiceType.objects.order_by('id').first()
        design_stage_sample_obj = DesignStage.objects.filter(is_active=True).order_by('order', 'id').first()
        design_stage_sample_label = design_stage_sample_obj.name if design_stage_sample_obj else ''
        status_label_map = dict(BusinessOpportunity.STATUS_CHOICES)
        status_sample_label = status_label_map.get('potential', '潜在客户')
        urgency_label_map = dict(BusinessOpportunity.URGENCY_CHOICES)
        urgency_sample_label = urgency_label_map.get('normal', '普通')
        opportunity_type_label_map = dict(BusinessOpportunity.OPPORTUNITY_TYPE_CHOICES)
        opportunity_type_sample_label = opportunity_type_label_map.get('project_cooperation', '项目合作')
        
        columns = [
            '商机编号（可留空自动生成）',
            '商机名称',
            '客户名称（必填）',
            '负责商务手机号（必填）',
            '商机类型',
            '服务类型（可填编码或名称）',
            '项目名称',
            '项目地址',
            '项目业态',
            '建筑面积（平方米）',
            '图纸阶段（可填编码或名称）',
            '预计金额（万元）',
            '成功概率（%）',
            '商机状态',
            '紧急程度',
            '预计签约时间（YYYY-MM-DD）',
            '商机描述',
            '备注',
        ]
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="opportunity_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(columns)
        writer.writerow([
            '',
            '锦城天府综合体一期商机',
            '成都锦城房地产开发有限公司',
            '13800000005',
            opportunity_type_sample_label,
            service_type_sample_obj.name if service_type_sample_obj else '',
            '锦城天府综合体一期',
            '成都市天府新区',
            '住宅',
            '50000',
            design_stage_sample_label,
            '500',
            '30',
            status_sample_label,
            urgency_sample_label,
            '2025-12-31',
            '这是一个示例商机',
            '备注信息',
        ])
        return response
    
    # 准备上下文数据
    design_stages = DesignStage.objects.filter(is_active=True).order_by('order', 'id')
    context = {
        'service_types': ServiceType.objects.order_by('order', 'id'),
        'design_stages': design_stages,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
        'opportunity_type_choices': BusinessOpportunity.OPPORTUNITY_TYPE_CHOICES,
        'import_results': None,
    }
    
    if request.method == 'POST':
        upload = request.FILES.get('import_file')
        if not upload:
            messages.error(request, '请上传 CSV 或 Excel 文件。')
        else:
            filename = upload.name.lower()
            is_excel = filename.endswith(('.xlsx', '.xls'))
            is_csv = filename.endswith('.csv')
            
            if not (is_csv or is_excel):
                messages.error(request, '仅支持 CSV 或 Excel 文件（.csv, .xlsx, .xls）。')
            elif upload.size > 10 * 1024 * 1024:  # 10MB
                messages.error(request, '文件过大，请控制在 10MB 以内。')
            else:
                try:
                    upload.seek(0)
                except Exception:
                    pass
                
                # 处理Excel文件
                if is_excel:
                    try:
                        import pandas as pd
                        # 尝试读取Excel文件
                        df = pd.read_excel(upload, engine='openpyxl' if filename.endswith('.xlsx') else None)
                        # 转换为CSV格式的字符串
                        csv_buffer = io.StringIO()
                        df.to_csv(csv_buffer, index=False, encoding='utf-8')
                        decoded_text = csv_buffer.getvalue()
                    except ImportError:
                        messages.error(request, '系统未安装 pandas 库，无法处理 Excel 文件。请使用 CSV 格式。')
                        decoded_text = None
                    except Exception as e:
                        messages.error(request, f'Excel 文件解析失败：{str(e)}')
                        decoded_text = None
                else:
                    # 处理CSV文件
                    raw_bytes = upload.read()
                    decoded_text = None
                    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
                        try:
                            decoded_text = raw_bytes.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                
                if decoded_text is None:
                    messages.error(request, '文件解析失败，请确认编码为 UTF-8 或 GBK（CSV），或使用标准 Excel 格式。')
                else:
                    text_io = io.StringIO(decoded_text)
                    reader = csv.DictReader(text_io)
                    
                    field_aliases = {
                        'opportunity_number': {'商机编号（可留空自动生成）', '商机编号(可留空自动生成)', '商机编号', 'opportunity_number'},
                        'name': {'商机名称', 'name'},
                        'client_name': {'客户名称（必填）', '客户名称(必填)', '客户名称', 'client_name'},
                        'business_manager_phone': {'负责商务手机号（必填）', '负责商务手机号(必填)', '负责商务手机号', '商务经理手机号', 'business_manager_phone'},
                        'opportunity_type': {'商机类型', 'opportunity_type'},
                        'service_type': {'服务类型（可填编码或名称）', '服务类型(可填编码或名称)', '服务类型', 'service_type'},
                        'project_name': {'项目名称', 'project_name'},
                        'project_address': {'项目地址', 'project_address'},
                        'project_type': {'项目业态', 'project_type'},
                        'building_area': {'建筑面积（平方米）', '建筑面积(平方米)', '建筑面积', 'building_area'},
                        'drawing_stage': {'图纸阶段（可填编码或名称）', '图纸阶段(可填编码或名称)', '图纸阶段', 'drawing_stage'},
                        'estimated_amount': {'预计金额（万元）', '预计金额(万元)', '预计金额', 'estimated_amount'},
                        'success_probability': {'成功概率（%）', '成功概率(%)', '成功概率', 'success_probability'},
                        'status': {'商机状态', 'status'},
                        'urgency': {'紧急程度', 'urgency'},
                        'expected_sign_date': {'预计签约时间（YYYY-MM-DD）', '预计签约时间(YYYY-MM-DD)', '预计签约时间', 'expected_sign_date'},
                        'description': {'商机描述', 'description'},
                        'notes': {'备注', 'notes'},
                    }
                    
                    required_fields = {
                        'name',
                        'client_name',
                        'business_manager_phone',
                    }
                    
                    missing_labels = []
                    headers = set(reader.fieldnames or [])
                    headers_lower = {h.strip().lower(): h for h in headers}
                    
                    # 检查必要字段是否存在（支持模糊匹配）
                    for field in required_fields:
                        found = False
                        for alias in field_aliases[field]:
                            # 精确匹配
                            if alias in headers:
                                found = True
                                break
                            # 模糊匹配（忽略空格和大小写）
                            alias_lower = alias.strip().lower()
                            if alias_lower in headers_lower:
                                found = True
                                break
                        
                        if not found:
                            # 显示期望的字段名
                            expected_names = list(field_aliases[field])[:3]  # 显示前3个期望的格式
                            missing_labels.append(f"{next(iter(field_aliases[field]))}（期望格式：{', '.join(expected_names)}）")
                    
                    if missing_labels:
                        # 显示CSV文件中的实际列名，帮助用户对比
                        actual_headers = list(headers)[:10]  # 显示前10个实际列名
                        error_msg = f'CSV 文件格式不正确，缺少必要字段：\n\n'
                        error_msg += f'缺少的字段：\n{chr(10).join(f"  - {label}" for label in missing_labels)}\n\n'
                        error_msg += f'CSV 文件中的列名（前10个）：\n{chr(10).join(f"  - {h}" for h in actual_headers)}\n\n'
                        error_msg += f'请检查CSV文件的列名是否与模板文件一致。'
                        messages.error(request, error_msg)
                    else:
                        def get_value(row, field):
                            # 首先尝试精确匹配
                            for alias in field_aliases[field]:
                                if alias in row and row[alias] is not None:
                                    value = str(row.get(alias, '')).strip()
                                    if value:
                                        return value
                            
                            # 如果精确匹配失败，尝试忽略空格和大小写的模糊匹配
                            row_keys_lower = {k.strip().lower(): k for k in row.keys()}
                            for alias in field_aliases[field]:
                                alias_lower = alias.strip().lower()
                                if alias_lower in row_keys_lower:
                                    original_key = row_keys_lower[alias_lower]
                                    value = str(row.get(original_key, '')).strip()
                                    if value:
                                        return value
                            
                            return ''
                        
                        # 构建查找映射
                        service_type_lookup = {st.code: st for st in ServiceType.objects.all()}
                        service_type_name_lookup = {(st.name or '').strip(): st for st in ServiceType.objects.all()}
                        
                        design_stage_objects = DesignStage.objects.filter(is_active=True)
                        design_stage_id_map = {str(ds.id): ds for ds in design_stage_objects}
                        design_stage_code_map = {ds.code: ds for ds in design_stage_objects if ds.code}
                        design_stage_name_map = {ds.name: ds for ds in design_stage_objects}
                        
                        status_codes = {code for code, _ in BusinessOpportunity.STATUS_CHOICES}
                        status_label_map = {(label or '').strip(): code for code, label in BusinessOpportunity.STATUS_CHOICES}
                        
                        urgency_codes = {code for code, _ in BusinessOpportunity.URGENCY_CHOICES}
                        urgency_label_map = {(label or '').strip(): code for code, label in BusinessOpportunity.URGENCY_CHOICES}
                        
                        opportunity_type_codes = {code for code, _ in BusinessOpportunity.OPPORTUNITY_TYPE_CHOICES}
                        opportunity_type_label_map = {(label or '').strip(): code for code, label in BusinessOpportunity.OPPORTUNITY_TYPE_CHOICES}
                        
                        results = []
                        success_count = 0
                        failure_count = 0
                        
                        for row_index, row in enumerate(reader, start=2):
                            row_result = {'row': row_index, 'status': 'success', 'message': ''}
                            
                            # 跳过完全空白的行
                            if not any(str(v).strip() for v in row.values() if v):
                                continue
                            
                            try:
                                with transaction.atomic():
                                    # 必填字段验证
                                    opportunity_name = get_value(row, 'name')
                                    if not opportunity_name:
                                        # 调试信息：显示可用的列名和值
                                        available_cols = list(row.keys())
                                        available_values = {k: v for k, v in row.items() if v and str(v).strip()}
                                        debug_info = f'可用列名: {available_cols}, 有值的列: {list(available_values.keys())}'
                                        raise ValueError(f'商机名称不能为空。{debug_info}')
                                    
                                    client_name = get_value(row, 'client_name')
                                    if not client_name:
                                        raise ValueError('客户名称不能为空')
                                    
                                    # 查找或创建客户
                                    client = Client.objects.filter(name=client_name).first()
                                    if not client:
                                        # 如果客户不存在，尝试创建（需要客户类型）
                                        client_type = ClientType.objects.first()
                                        if not client_type:
                                            raise ValueError(f'客户"{client_name}"不存在，且系统未配置客户类型，无法自动创建')
                                        client = Client.objects.create(
                                            name=client_name,
                                            client_type=client_type,
                                            created_by=request.user,
                                        )
                                    
                                    business_manager_phone = get_value(row, 'business_manager_phone')
                                    if not business_manager_phone:
                                        raise ValueError('负责商务手机号不能为空')
                                    business_manager = User.objects.filter(username=business_manager_phone).first()
                                    if not business_manager:
                                        raise ValueError(f'未找到对应的商务经理手机号：{business_manager_phone}')
                                    
                                    # 可选字段处理
                                    opportunity_number = get_value(row, 'opportunity_number')
                                    if opportunity_number and BusinessOpportunity.objects.filter(opportunity_number=opportunity_number).exists():
                                        raise ValueError(f'商机编号重复：{opportunity_number}')
                                    
                                    opportunity_type_raw = get_value(row, 'opportunity_type')
                                    opportunity_type = None
                                    if opportunity_type_raw:
                                        if opportunity_type_raw in opportunity_type_codes:
                                            opportunity_type = opportunity_type_raw
                                        else:
                                            opportunity_type = opportunity_type_label_map.get(opportunity_type_raw)
                                        if not opportunity_type:
                                            raise ValueError(f'商机类型取值无效：{opportunity_type_raw}')
                                    
                                    service_type_key = get_value(row, 'service_type')
                                    service_type = None
                                    if service_type_key:
                                        service_type = service_type_lookup.get(service_type_key)
                                        if not service_type:
                                            service_type = service_type_name_lookup.get(service_type_key)
                                        if not service_type:
                                            raise ValueError(f'服务类型取值无效：{service_type_key}')
                                    
                                    project_name = get_value(row, 'project_name') or None
                                    project_address = get_value(row, 'project_address') or None
                                    project_type = get_value(row, 'project_type') or None
                                    
                                    building_area_str = get_value(row, 'building_area')
                                    building_area = None
                                    if building_area_str:
                                        try:
                                            building_area = Decimal(building_area_str)
                                        except (ValueError, InvalidOperation):
                                            raise ValueError(f'建筑面积格式无效：{building_area_str}')
                                    
                                    drawing_stage_raw = get_value(row, 'drawing_stage')
                                    drawing_stage = None
                                    if drawing_stage_raw:
                                        if drawing_stage_raw in design_stage_id_map:
                                            drawing_stage = design_stage_id_map[drawing_stage_raw]
                                        elif drawing_stage_raw in design_stage_code_map:
                                            drawing_stage = design_stage_code_map[drawing_stage_raw]
                                        elif drawing_stage_raw in design_stage_name_map:
                                            drawing_stage = design_stage_name_map[drawing_stage_raw]
                                        if not drawing_stage:
                                            raise ValueError(f'图纸阶段取值无效：{drawing_stage_raw}')
                                    
                                    estimated_amount_str = get_value(row, 'estimated_amount')
                                    estimated_amount = Decimal('0')
                                    if estimated_amount_str:
                                        try:
                                            estimated_amount = Decimal(estimated_amount_str)
                                        except (ValueError, InvalidOperation):
                                            raise ValueError(f'预计金额格式无效：{estimated_amount_str}')
                                    
                                    success_probability_str = get_value(row, 'success_probability')
                                    success_probability = 10  # 默认值
                                    if success_probability_str:
                                        try:
                                            success_probability = int(success_probability_str)
                                            if success_probability not in [10, 30, 50, 70, 90]:
                                                raise ValueError(f'成功概率必须是 10、30、50、70 或 90，当前值：{success_probability}')
                                        except ValueError as e:
                                            if '必须是' in str(e):
                                                raise
                                            raise ValueError(f'成功概率格式无效：{success_probability_str}')
                                    
                                    status_raw = get_value(row, 'status') or 'potential'
                                    status = status_raw
                                    if status not in status_codes:
                                        status = status_label_map.get(status_raw)
                                    if not status or status not in status_codes:
                                        raise ValueError(f'商机状态取值无效：{status_raw}')
                                    
                                    urgency_raw = get_value(row, 'urgency') or 'normal'
                                    urgency = urgency_raw
                                    if urgency not in urgency_codes:
                                        urgency = urgency_label_map.get(urgency_raw)
                                    if not urgency or urgency not in urgency_codes:
                                        raise ValueError(f'紧急程度取值无效：{urgency_raw}')
                                    
                                    expected_sign_date_str = get_value(row, 'expected_sign_date')
                                    expected_sign_date = None
                                    if expected_sign_date_str:
                                        try:
                                            from datetime import datetime
                                            expected_sign_date = datetime.strptime(expected_sign_date_str, '%Y-%m-%d').date()
                                        except ValueError:
                                            raise ValueError(f'预计签约时间格式无效，应为 YYYY-MM-DD：{expected_sign_date_str}')
                                    
                                    description = get_value(row, 'description') or ''
                                    notes = get_value(row, 'notes') or ''
                                    
                                    # 创建商机
                                    opportunity = BusinessOpportunity(
                                        opportunity_number=opportunity_number or None,
                                        name=opportunity_name,
                                        client=client,
                                        business_manager=business_manager,
                                        opportunity_type=opportunity_type or '',
                                        service_type=service_type,
                                        project_name=project_name or '',
                                        project_address=project_address or '',
                                        project_type=project_type or '',
                                        building_area=building_area,
                                        drawing_stage=drawing_stage,
                                        estimated_amount=estimated_amount,
                                        success_probability=success_probability,
                                        status=status,
                                        urgency=urgency,
                                        expected_sign_date=expected_sign_date,
                                        description=description,
                                        notes=notes,
                                        created_by=request.user,
                                    )
                                    
                                    # 验证模型数据
                                    opportunity.full_clean()
                                    
                                    # 保存商机
                                    opportunity.save()
                                    
                                    success_count += 1
                                    row_result['message'] = f'导入成功，商机编号：{opportunity.opportunity_number}'
                            except Exception as exc:
                                import traceback
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.error(f'导入第{row_index}行失败: {str(exc)}')
                                logger.error(traceback.format_exc())
                                failure_count += 1
                                row_result['status'] = 'failed'
                                row_result['message'] = f'{str(exc)}'
                            results.append(row_result)
                        
                        context['import_results'] = {
                            'total': success_count + failure_count,
                            'success': success_count,
                            'failed': failure_count,
                            'rows': results,
                        }
                        if success_count:
                            messages.success(request, f'成功导入 {success_count} 条商机。')
                        if failure_count:
                            messages.warning(request, f'{failure_count} 条记录导入失败，请查看结果列表。')
    
    # 添加左侧菜单
    context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, request.path, active_id='opportunity_import')
    context['sidebar_title'] = '商机管理'
    context['sidebar_subtitle'] = 'Opportunity Management'
    
    return render(
        request,
        'opportunity_management/opportunity_import.html',
        {
            **context,
            'page_title': '商机批量导入',
            'page_description': '通过上传 CSV 或 Excel 文件批量导入商机数据',
        }
    )

