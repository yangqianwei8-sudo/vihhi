from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import (
    Client, ClientContact, ContactEducation, ContactWorkExperience,
    ContactJobChange, ContactCooperation, ContactTracking,
    CustomerRelationship, CustomerRelationshipUpgrade, ClientProject, School
)
from .serializers import (
    ClientSerializer, ClientCreateSerializer,
    ClientContactSerializer, ClientContactCreateSerializer,
    ContactEducationSerializer, ContactWorkExperienceSerializer,
    ContactJobChangeSerializer, ContactCooperationSerializer, ContactTrackingSerializer,
    CustomerRelationshipSerializer, CustomerRelationshipCreateSerializer,
    CustomerRelationshipUpgradeSerializer, CustomerRelationshipUpgradeCreateSerializer,
)
from .services import get_service, AmapAPIService
import os


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_credit_code(request):
    """
    验证统一社会信用代码API
    
    请求参数:
    {
        "credit_code": "统一社会信用代码（18位）",
        "company_name": "公司名称（可选，用于验证匹配）"
    }
    
    返回:
    {
        "valid": bool,  # 是否有效
        "matched": bool,  # 是否与公司名称匹配
        "company_info": dict,  # 企业信息
        "message": str  # 消息
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        credit_code = request.data.get('credit_code', '').strip()
        company_name = request.data.get('company_name', '').strip()
        
        if not credit_code:
            return Response({
                'valid': False,
                'matched': False,
                'company_info': None,
                'message': '统一社会信用代码不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用启信宝API验证
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'valid': False,
                'matched': False,
                'company_info': None,
                'message': f'验证失败：服务初始化失败 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            result = qixinbao_service.verify_credit_code(credit_code, company_name)
        except Exception as e:
            logger.error(f'调用启信宝API验证失败: {str(e)}', exc_info=True)
            return Response({
                'valid': False,
                'matched': False,
                'company_info': None,
                'message': f'验证失败：API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'验证统一社会信用代码API异常: {str(e)}', exc_info=True)
        return Response({
            'valid': False,
            'matched': False,
            'company_info': None,
            'message': f'验证失败：服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_company(request):
    """
    企业模糊搜索API
    
    请求参数:
    - keyword: 企业关键字（必填，至少2个字符）
    - match_type: 匹配类型（可选）
    - region: 地区编码（可选）
    - skip: 跳过条目数（可选，默认0）
    
    返回:
    {
        "success": bool,
        "data": {
            "total": int,  # 总数
            "num": int,  # 当前返回数
            "items": [  # 企业列表
                {
                    "name": "企业名称",
                    "credit_no": "统一社会信用代码",
                    "reg_no": "注册号",
                    "oper_name": "法定代表人",
                    "start_date": "成立日期",
                    "id": "企业编号"
                }
            ]
        },
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        keyword = request.GET.get('keyword', '').strip()
        
        if not keyword or len(keyword) < 2:
            return Response({
                'success': False,
                'data': None,
                'message': '搜索关键字至少需要2个字符'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        match_type = request.GET.get('match_type', 'ename')
        region = request.GET.get('region', '')
        
        # 安全处理skip参数
        try:
            skip = int(request.GET.get('skip', 0))
            if skip < 0:
                skip = 0
        except (ValueError, TypeError):
            skip = 0
        
        # 调用启信宝API搜索
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': '搜索失败：服务初始化失败，请检查后端日志'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 检查API配置
        if not qixinbao_service.app_key or not qixinbao_service.app_secret:
            logger.warning('启信宝API未配置')
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': '搜索失败：启信宝API未配置，请在.env文件中配置QIXINBAO_APP_KEY和QIXINBAO_APP_SECRET'
            }, status=status.HTTP_200_OK)
        
        # 调用API
        try:
            result = qixinbao_service.search_company(
                keyword=keyword,
                match_type=match_type,
                region=region,
                skip=skip
            )
        except Exception as e:
            logger.error(f'调用启信宝API失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': f'搜索失败：API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f'搜索企业API调用结果: keyword={keyword}, result={result}')
        
        # 检查是否返回了错误信息
        if result and isinstance(result, dict) and 'error' in result:
            error_info = result['error']
            error_message = error_info.get('detail', error_info.get('message', '未知错误'))
            logger.warning(f'启信宝API返回错误: {error_info}')
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': f'搜索失败：{error_message}（错误码：{error_info.get("status", "未知")}）'
            }, status=status.HTTP_200_OK)
        
        if result is None:
            # 如果API调用失败，可能是网络问题或其他错误
            logger.warning('启信宝API调用失败，返回空结果')
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': '搜索失败：启信宝API调用失败，请检查网络连接或后端日志获取详细信息。'
            }, status=status.HTTP_200_OK)
        
        # 检查返回数据格式
        if not isinstance(result, dict):
            logger.error(f'API返回数据格式错误: {type(result)}')
            return Response({
                'success': False,
                'data': {
                    'total': 0,
                    'num': 0,
                    'items': []
                },
                'message': 'API返回数据格式错误'
            }, status=status.HTTP_200_OK)
        
        # 确保items是列表
        if 'items' not in result:
            result['items'] = []
        if not isinstance(result.get('items'), list):
            result['items'] = []
        
        logger.info(f'返回搜索结果: total={result.get("total", 0)}, items={len(result.get("items", []))}')
        
        return Response({
            'success': True,
            'data': result,
            'message': '搜索成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'搜索企业API异常: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'data': {
                'total': 0,
                'num': 0,
                'items': []
            },
            'message': f'搜索失败：服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_company_detail(request):
    """
    获取企业详细信息API
    
    请求参数:
    - company_id: 企业ID（启信宝返回的企业编号）
    - credit_code: 统一社会信用代码
    - company_name: 企业全名
    
    返回:
    {
        "success": bool,
        "data": {
            "reg_capital": str,  # 注册资本
            "phone": str,  # 联系电话
            "email": str,  # 邮箱
            "address": str,  # 地址
            ...
        },
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        company_id = request.GET.get('company_id', '').strip()
        credit_code = request.GET.get('credit_code', '').strip()
        company_name = request.GET.get('company_name', '').strip()
        
        if not company_id and not credit_code and not company_name:
            return Response({
                'success': False,
                'data': None,
                'message': '请提供企业ID、统一社会信用代码或企业名称'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用启信宝API获取企业详情
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': '服务初始化失败，请检查后端日志'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 检查API配置
        if not qixinbao_service.app_key or not qixinbao_service.app_secret:
            logger.warning('启信宝API未配置')
            return Response({
                'success': False,
                'data': None,
                'message': '启信宝API未配置'
            }, status=status.HTTP_200_OK)
        
        # 调用API
        try:
            result = qixinbao_service.get_company_detail(
                company_id=company_id or None,
                credit_code=credit_code or None,
                company_name=company_name or None
            )
        except Exception as e:
            logger.error(f'调用启信宝API失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': f'API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if result is None:
            return Response({
                'success': False,
                'data': None,
                'message': '获取企业详情失败，请检查企业ID或名称是否正确'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': True,
            'data': result,
            'message': '获取成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'获取企业详情API异常: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'data': None,
            'message': f'服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_legal_risk(request):
    """
    获取企业法律风险信息API
    
    请求参数:
    - company_id: 企业ID（启信宝返回的企业编号）
    - credit_code: 统一社会信用代码（如果未提供company_id，则使用此参数）
    
    返回:
    {
        "success": bool,
        "data": {
            "litigation_count": int,  # 司法案件数量
            "executed_person_count": int,  # 被执行人数量
            "final_case_count": int,  # 终本案件数量
            "consumption_limit_count": int,  # 限制高消费数量
            "risk_level": str,  # 风险等级代码
            "risk_level_label": str,  # 风险等级标签
        },
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        company_id = request.GET.get('company_id', '').strip()
        credit_code = request.GET.get('credit_code', '').strip()
        company_name = request.GET.get('company_name', '').strip()
        
        if not company_id and not credit_code and not company_name:
            return Response({
                'success': False,
                'data': None,
                'message': '请提供企业ID、统一社会信用代码或企业名称'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用启信宝API获取法律风险信息
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': f'获取失败：服务初始化失败 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            result = qixinbao_service.get_legal_risk_info(
                company_id=company_id, 
                credit_code=credit_code,
                company_name=company_name
            )
        except Exception as e:
            logger.error(f'调用启信宝API获取法律风险信息失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': {
                    'litigation_count': 0,
                    'executed_person_count': 0,
                    'final_case_count': 0,
                    'consumption_limit_count': 0,
                    'risk_level': 'unknown',
                    'risk_level_label': '未知',
                },
                'message': f'获取失败：API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f'获取法律风险信息: company_id={company_id}, credit_code={credit_code}, result={result}')
        
        # 检查是否有API错误
        api_error = result.get('api_error')
        if api_error:
            # API调用失败，但仍然返回数据（使用默认值）
            error_message = api_error.get('detail') or api_error.get('message', 'API调用失败')
            return Response({
                'success': False,
                'data': result,
                'message': f'获取失败：{error_message}',
                'api_error': api_error
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': True,
            'data': result,
            'message': '获取成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'获取法律风险信息API异常: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'data': None,
            'message': f'获取失败：服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_execution_records(request):
    """
    获取被执行记录API（不保存到数据库）
    
    请求参数:
    - credit_code: 统一社会信用代码（可选）
    - company_name: 企业名称（可选）
    
    返回:
    {
        "success": bool,
        "data": {
            "records": [
                {
                    "case_number": str,
                    "execution_status": str,
                    "execution_court": str,
                    "filing_date": str,
                    "execution_amount": str
                }
            ],
            "count": int,
            "total_amount": str
        },
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        credit_code = request.GET.get('credit_code', '').strip()
        company_name = request.GET.get('company_name', '').strip()
        
        if not credit_code and not company_name:
            return Response({
                'success': False,
                'data': None,
                'message': '请提供统一社会信用代码或企业名称'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用启信宝API获取被执行记录
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': f'获取失败：服务初始化失败 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            records = qixinbao_service.get_execution_records(
                credit_code=credit_code,
                company_name=company_name
            )
        except Exception as e:
            logger.error(f'调用启信宝API获取被执行记录失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': f'获取失败：API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 计算执行总金额
        total_amount = 0
        if records:
            for record in records:
                try:
                    amount = float(record.get('execution_amount', 0) or 0)
                    total_amount += amount
                except (ValueError, TypeError):
                    pass
        
        # 返回记录（不保存到数据库）
        return Response({
            'success': True,
            'data': {
                'records': records or [],
                'count': len(records) if records else 0,
                'total_amount': str(total_amount)
            },
            'message': '获取成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f'获取被执行记录失败: {str(e)}')
        return Response({
            'success': False,
            'data': None,
            'message': f'获取失败：服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_execution_records(request):
    """
    同步被执行记录API
    
    请求参数:
    {
        "client_id": int,  # 客户ID（必填）
        "company_id": str,  # 企业ID（启信宝返回的企业编号，可选）
        "credit_code": str,  # 统一社会信用代码（可选）
        "company_name": str,  # 企业名称（可选）
    }
    
    返回:
    {
        "success": bool,
        "synced_count": int,  # 同步的记录数量
        "total_count": int,  # 总记录数量
        "total_amount": str,  # 执行总金额
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        client_id = request.data.get('client_id')
        company_id = request.data.get('company_id', '').strip()
        credit_code = request.data.get('credit_code', '').strip()
        company_name = request.data.get('company_name', '').strip()
        
        if not client_id:
            return Response({
                'success': False,
                'synced_count': 0,
                'total_count': 0,
                'message': '请提供客户ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取客户对象
        from .models import Client, ExecutionRecord
        from decimal import Decimal
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'synced_count': 0,
                'total_count': 0,
                'total_amount': '0',
                'message': '客户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 如果没有提供查询参数，使用客户信息
        if not company_id and not credit_code and not company_name:
            company_name = client.name
            credit_code = client.unified_credit_code
        
        # 调用启信宝API获取被执行记录
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'synced_count': 0,
                'total_count': 0,
                'total_amount': '0',
                'message': f'获取失败：服务初始化失败 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            records = qixinbao_service.get_execution_records(
                company_id=company_id,
                credit_code=credit_code,
                company_name=company_name
            )
        except Exception as e:
            logger.error(f'调用启信宝API获取被执行记录失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'synced_count': 0,
                'total_count': 0,
                'total_amount': '0',
                'message': f'获取失败：API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not records:
            # 如果没有记录，返回成功但数量为0
            total_count = ExecutionRecord.objects.filter(client=client).count()
            from django.db.models import Sum
            total_amount = ExecutionRecord.objects.filter(client=client).aggregate(
                total=Sum('execution_amount')
            )['total'] or Decimal('0')
            return Response({
                'success': True,
                'synced_count': 0,
                'total_count': total_count,
                'total_amount': str(total_amount),
                'message': '未获取到被执行记录（可能该企业没有被执行记录，或API尚未实现）'
            }, status=status.HTTP_200_OK)
        
        # 保存记录到数据库
        synced_count = 0
        from datetime import datetime
        
        for record_data in records:
            # 检查是否已存在（根据案号判断）
            case_number = record_data.get('case_number', '').strip()
            if case_number:
                existing = ExecutionRecord.objects.filter(
                    client=client,
                    case_number=case_number
                ).first()
                if existing:
                    # 更新现有记录
                    if record_data.get('filing_date'):
                        try:
                            existing.filing_date = datetime.strptime(record_data['filing_date'], '%Y-%m-%d').date()
                        except:
                            pass
                    existing.execution_status = record_data.get('execution_status', 'unknown')
                    existing.execution_court = record_data.get('execution_court', '')
                    try:
                        existing.execution_amount = Decimal(str(record_data.get('execution_amount', 0) or 0))
                    except (ValueError, TypeError):
                        existing.execution_amount = Decimal('0')
                    existing.source = 'qixinbao'
                    existing.save()
                    synced_count += 1
                    continue
            
            # 创建新记录
            filing_date = None
            if record_data.get('filing_date'):
                try:
                    filing_date = datetime.strptime(record_data['filing_date'], '%Y-%m-%d').date()
                except:
                    pass
            
            try:
                execution_amount = Decimal(str(record_data.get('execution_amount', 0) or 0))
            except (ValueError, TypeError):
                execution_amount = Decimal('0')
            
            ExecutionRecord.objects.create(
                client=client,
                filing_date=filing_date,
                case_number=record_data.get('case_number', ''),
                execution_status=record_data.get('execution_status', 'unknown'),
                execution_court=record_data.get('execution_court', ''),
                execution_amount=execution_amount,
                source='qixinbao'
            )
            synced_count += 1
        
        # 计算总金额并更新客户记录
        from django.db.models import Sum
        total_amount = ExecutionRecord.objects.filter(client=client).aggregate(
            total=Sum('execution_amount')
        )['total'] or Decimal('0')
        client.total_execution_amount = total_amount
        client.save()
        
        total_count = ExecutionRecord.objects.filter(client=client).count()
        
        logger.info(f'同步被执行记录成功: client_id={client_id}, synced_count={synced_count}, total_count={total_count}, total_amount={total_amount}')
        
        return Response({
            'success': True,
            'synced_count': synced_count,
            'total_count': total_count,
            'total_amount': str(total_amount),
            'message': f'成功同步 {synced_count} 条记录'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'同步被执行记录API异常: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'synced_count': 0,
            'total_count': 0,
            'total_amount': '0',
            'message': f'同步失败：服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_company_info_by_name(request):
    """
    通过企业名称获取企业基本信息API（四要素）
    
    根据启信宝API文档（企业四要素 API 1.31）实现
    
    请求参数:
    - company_name: 企业名称（必填，至少2个字符）
    
    返回:
    {
        "success": bool,
        "data": {
            "name": str,  # 企业名称
            "credit_code": str,  # 统一社会信用代码
            "legal_representative": str,  # 法定代表人
            "established_date": str,  # 成立日期（YYYY-MM-DD格式）
            "registered_capital": str,  # 注册资本（原始字符串，如"6500 万人民币"）
            "registered_capital_value": float,  # 注册资本数值（万元）
            "phone": str,  # 联系电话
            "email": str,  # 邮箱
            "address": str,  # 地址
        },
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        company_name = request.GET.get('company_name', '').strip()
        
        if not company_name or len(company_name) < 2:
            return Response({
                'success': False,
                'data': None,
                'message': '企业名称至少需要2个字符'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用启信宝API获取企业信息
        try:
            qixinbao_service = get_service()
        except Exception as e:
            logger.error(f'获取启信宝服务失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': '服务初始化失败，请检查后端日志'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 检查API配置
        if not qixinbao_service.app_key or not qixinbao_service.app_secret:
            logger.warning('启信宝API未配置')
            return Response({
                'success': False,
                'data': None,
                'message': '启信宝API未配置，请联系管理员配置QIXINBAO_APP_KEY和QIXINBAO_APP_SECRET'
            }, status=status.HTTP_200_OK)
        
        # 调用API
        try:
            result = qixinbao_service.get_company_info_by_name(company_name)
        except Exception as e:
            logger.error(f'调用启信宝API失败: {str(e)}', exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'message': f'API调用异常 - {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if result is None:
            return Response({
                'success': False,
                'data': None,
                'message': '未找到该企业信息，请检查企业名称是否正确'
            }, status=status.HTTP_200_OK)
        
        logger.info(f'获取企业信息成功: {company_name}')
        
        return Response({
            'success': True,
            'data': result,
            'message': '获取成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'获取企业信息API异常: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'data': None,
            'message': f'服务器内部错误 - {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_duplicate_client(request):
    """
    检查客户是否重复API
    
    请求参数:
    - name: 客户名称
    - unified_credit_code: 统一社会信用代码（可选）
    - exclude_id: 排除的客户ID（用于编辑时排除自己）
    
    返回:
    {
        "success": bool,
        "is_duplicate": bool,  # 是否重复
        "duplicate_type": str,  # 重复类型: "name" 或 "credit_code"
        "existing_client": {  # 如果重复，返回已存在的客户信息
            "id": int,
            "name": str,
            "unified_credit_code": str
        },
        "message": str
    }
    """
    from .models import Client
    
    name = request.GET.get('name', '').strip()
    unified_credit_code = request.GET.get('unified_credit_code', '').strip()
    exclude_id = request.GET.get('exclude_id')
    
    if not name and not unified_credit_code:
        return Response({
            'success': False,
            'is_duplicate': False,
            'message': '请提供客户名称或统一信用代码'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 查询重复客户
    query = Client.objects.all()
    
    # 如果提供了客户名称，检查名称
    if name:
        query = query.filter(name=name)
    
    # 如果提供了统一信用代码，检查统一信用代码
    if unified_credit_code:
        query = query.filter(unified_credit_code=unified_credit_code)
    
    # 如果提供了exclude_id，排除该客户（用于编辑时）
    if exclude_id:
        try:
            query = query.exclude(pk=int(exclude_id))
        except (ValueError, TypeError):
            pass
    
    duplicate_client = query.first()
    
    if duplicate_client:
        # 如果同时提供了名称和统一信用代码，且都匹配，则认为是重复
        if name and unified_credit_code:
            if duplicate_client.name == name and duplicate_client.unified_credit_code == unified_credit_code:
                return Response({
                    'success': True,
                    'is_duplicate': True,
                    'duplicate_type': 'both',
                    'existing_client': {
                        'id': duplicate_client.id,
                        'name': duplicate_client.name,
                        'unified_credit_code': duplicate_client.unified_credit_code or ''
                    },
                    'message': f'与"{duplicate_client.name}"的客户重复，不允许创建'
                })
        # 如果只提供了名称
        elif name:
            return Response({
                'success': True,
                'is_duplicate': True,
                'duplicate_type': 'name',
                'existing_client': {
                    'id': duplicate_client.id,
                    'name': duplicate_client.name,
                    'unified_credit_code': duplicate_client.unified_credit_code or ''
                },
                'message': f'与"{duplicate_client.name}"的客户重复（客户名称相同）'
            })
        # 如果只提供了统一信用代码
        elif unified_credit_code:
            return Response({
                'success': True,
                'is_duplicate': True,
                'duplicate_type': 'credit_code',
                'existing_client': {
                    'id': duplicate_client.id,
                    'name': duplicate_client.name,
                    'unified_credit_code': duplicate_client.unified_credit_code or ''
                },
                'message': f'与"{duplicate_client.name}"的客户重复（统一信用代码相同）'
            })
    
    return Response({
        'success': True,
        'is_duplicate': False,
        'message': '客户信息未重复，可以创建'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def find_client_by_phone(request):
    """
    根据电话查询关联客户API
    
    请求参数:
    - phone: 电话号码
    
    返回:
    {
        "success": bool,
        "found": bool,  # 是否找到关联客户
        "clients": [  # 关联的客户列表
            {
                "id": int,
                "name": str,
                "code": str,
                "contact_name": str,
                "contact_position": str,
                "phone": str
            }
        ],
        "message": str
    }
    """
    # 客户管理相关API已删除，将按新设计方案重构
    return Response({
        'success': False,
        'found': False,
        'clients': [],
        'message': '客户管理API已删除，将按新设计方案重构'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


# ==================== 商机报价管理 REST API ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_quotation_modes(request):
    """
    获取报价模式列表API
    
    返回:
    {
        "success": bool,
        "modes": [
            {
                "code": str,  # 模式代码
                "name": str,  # 模式名称
                "description": str,  # 模式描述
                "formula": str,  # 计算公式说明
            }
        ]
    }
    """
    from .models import OpportunityQuotation
    
    modes = []
    for code, name in OpportunityQuotation.QUOTATION_MODE_CHOICES:
        mode_info = {
            'code': code,
            'name': name,
        }
        
        # 添加模式描述和公式说明
        descriptions = {
            'rate': {
                'description': '服务费 = 节省金额 × 约定费率。费用完全与优化成果挂钩。',
                'formula': '服务费 = 节省金额 × 费率'
            },
            'base_fee_rate': {
                'description': '服务费 = 固定基本费 + (节省金额 × 约定费率)。兼顾服务方基础成本与成果激励。',
                'formula': '服务费 = 基本费 + (节省金额 × 费率)'
            },
            'fixed': {
                'description': '服务费 = 预先设定的固定金额。价格固定，风险由服务方承担。',
                'formula': '服务费 = 固定金额'
            },
            'segmented': {
                'description': '将节省金额划分为多个区间，每个区间适用不同的费率，总服务费为各区间累计之和。',
                'formula': '服务费 = Σ(区间节省金额 × 对应费率)'
            },
            'min_savings_rate': {
                'description': '设定一个最低节省金额门槛。若实际节省金额低于此门槛，则不收取服务费；若超过，则对全部节省金额按约定费率计费。',
                'formula': '如果 节省金额 < 最低节省门槛: 服务费 = 0; 否则: 服务费 = 节省金额 × 费率'
            },
            'performance_linked': {
                'description': '服务费 = 基础服务费 + 绩效奖金。绩效奖金与预先设定的多个关键绩效指标（KPI）完成度挂钩。',
                'formula': '服务费 = 基础服务费 + Σ(KPI奖金 × KPI完成度)'
            },
            'hybrid': {
                'description': '在同一项目中，针对不同阶段、不同服务内容或不同触发条件，组合使用多种计价方式。',
                'formula': '总服务费 = Σ(各子模式服务费)'
            },
        }
        
        if code in descriptions:
            mode_info.update(descriptions[code])
        else:
            mode_info['description'] = ''
            mode_info['formula'] = ''
        
        modes.append(mode_info)
    
    return Response({
        'success': True,
        'modes': modes
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_quotation_by_mode(request):
    """
    按模式计算报价API
    
    请求参数:
    {
        "mode": str,  # 报价模式（rate/base_fee_rate/fixed/segmented/min_savings_rate/performance_linked/hybrid）
        "saved_amount": float,  # 节省金额（元，注意：不是万元）
        "mode_params": dict,  # 模式参数（根据模式不同而不同）
        "cap_fee": float  # 封顶费（元，可选）
    }
    
    返回:
    {
        "mode": str,
        "service_fee": float,  # 服务费（元）
        "calculated_fee": float,  # 计算出的服务费（未应用封顶费前，元）
        "cap_fee": float,  # 封顶费（元）
        "is_capped": bool,  # 是否应用了封顶费
        "calculation_steps": [str]  # 计算步骤说明
    }
    """
    try:
        mode = request.data.get('mode', 'rate')
        saved_amount = request.data.get('saved_amount', 0)
        mode_params = request.data.get('mode_params', {})
        cap_fee = request.data.get('cap_fee')
        
        # 验证参数
        if not mode:
            return Response({
                'success': False,
                'error': '报价模式不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if saved_amount is None or saved_amount < 0:
            return Response({
                'success': False,
                'error': '节省金额必须大于等于0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 将元转换为万元（计算引擎使用万元）
        saved_amount_wan = float(saved_amount) / 10000
        cap_fee_wan = float(cap_fee) / 10000 if cap_fee else None
        
        # 调用计算引擎
        from backend.apps.customer_management.services.quotation_calculator import QuotationCalculator
        calculator = QuotationCalculator()
        result = calculator.calculate(
            mode=mode,
            saved_amount=saved_amount_wan,
            mode_params=mode_params,
            cap_fee=cap_fee_wan
        )
        
        # 将结果从万元转换回元
        service_fee_yuan = result['service_fee'] * 10000
        calculated_fee_yuan = result.get('calculated_fee', result['service_fee']) * 10000
        cap_fee_yuan = result.get('cap_fee') * 10000 if result.get('cap_fee') else None
        
        # 转换计算步骤中的单位（从万元转为元）
        calculation_steps = []
        for step in result.get('calculation_steps', []):
            # 替换步骤中的"万元"为"元"，并调整数值
            step_yuan = step.replace('万元', '元')
            # 如果步骤中包含数字，需要乘以10000（但这里为了简化，保持原样，因为步骤中已经说明了单位）
            calculation_steps.append(step_yuan)
        
        return Response({
            'success': True,
            'mode': mode,
            'service_fee': service_fee_yuan,
            'calculated_fee': calculated_fee_yuan,
            'cap_fee': cap_fee_yuan,
            'is_capped': result.get('is_capped', False),
            'calculation_steps': calculation_steps
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('报价计算失败: %s', str(e))
        return Response({
            'success': False,
            'error': f'计算失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 商机分析 REST API ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_funnel_analysis_api(request):
    """
    销售漏斗分析API
    
    请求参数:
    - start_date: 开始日期（YYYY-MM-DD，可选）
    - end_date: 结束日期（YYYY-MM-DD，可选）
    - business_manager_id: 商务经理ID（可选）
    
    返回:
    {
        "stages": [
            {
                "stage": str,  # 阶段代码
                "stage_label": str,  # 阶段名称
                "count": int,  # 商机数量
                "amount": float,  # 预计金额（元）
                "weighted_amount": float,  # 加权金额（元）
                "conversion_rate": float  # 转化率（%，相对于上一阶段）
            }
        ],
        "total_opportunities": int,
        "total_amount": float,
        "total_weighted_amount": float,
        "overall_conversion_rate": float  # 整体转化率（从初步接触到赢单）
    }
    """
    from datetime import datetime
    from django.db.models import Count, Sum
    from .models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    
    # 获取筛选参数
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取商机查询集
    opportunities = BusinessOpportunity.objects.select_related(
        'client', 'business_manager'
    ).exclude(status__in=['won', 'lost', 'cancelled'])
    
    # 权限过滤
    from backend.core.views import _permission_granted
    if not _permission_granted('customer_management.opportunity.view_all', permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    # 时间范围筛选
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            opportunities = opportunities.filter(created_time__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            opportunities = opportunities.filter(created_time__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 商务经理筛选
    if business_manager_id:
        opportunities = opportunities.filter(business_manager_id=business_manager_id)
    
    # 按状态统计
    status_stats = opportunities.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('estimated_amount'),
        weighted_amount=Sum('weighted_amount')
    ).order_by('status')
    
    # 构建漏斗数据
    status_order = ['potential', 'initial_contact', 'requirement_confirmed', 'quotation', 'negotiation']
    status_labels = dict(BusinessOpportunity.STATUS_CHOICES)
    
    stages = []
    prev_count = None
    
    for status_code in status_order:
        status_stat = next((s for s in status_stats if s['status'] == status_code), None)
        if status_stat:
            count = status_stat['count']
            amount = float(status_stat['total_amount'] or 0)
            weighted_amount = float(status_stat['weighted_amount'] or 0)
            
            # 计算转化率
            conversion_rate = None
            if prev_count and prev_count > 0:
                conversion_rate = round((count / prev_count) * 100, 2)
            
            stages.append({
                'stage': status_code,
                'stage_label': status_labels.get(status_code, status_code),
                'count': count,
                'amount': amount,
                'weighted_amount': weighted_amount,
                'conversion_rate': conversion_rate,
            })
            prev_count = count
        else:
            stages.append({
                'stage': status_code,
                'stage_label': status_labels.get(status_code, status_code),
                'count': 0,
                'amount': 0,
                'weighted_amount': 0,
                'conversion_rate': None,
            })
            prev_count = 0
    
    # 计算整体统计
    total_opportunities = opportunities.count()
    total_amount = float(opportunities.aggregate(total=Sum('estimated_amount'))['total'] or 0)
    total_weighted_amount = float(opportunities.aggregate(total=Sum('weighted_amount'))['total'] or 0)
    
    # 计算整体转化率
    initial_contact_count = next((d['count'] for d in stages if d['stage'] == 'initial_contact'), 0)
    won_queryset = BusinessOpportunity.objects.filter(status='won')
    if not _permission_granted('customer_management.opportunity.view_all', permission_set):
        won_queryset = won_queryset.filter(business_manager=request.user)
    won_count = won_queryset.count()
    overall_conversion_rate = None
    if initial_contact_count > 0:
        overall_conversion_rate = round((won_count / initial_contact_count) * 100, 2)
    
    return Response({
        'stages': stages,
        'total_opportunities': total_opportunities,
        'total_amount': total_amount,
        'total_weighted_amount': total_weighted_amount,
        'overall_conversion_rate': overall_conversion_rate,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_sales_forecast_api(request):
    """
    销售预测API
    
    请求参数:
    - month: 预测月份（YYYY-MM，可选，默认为当前月份）
    
    返回:
    {
        "month": str,  # 预测月份
        "active_opportunities": int,  # 活跃商机数
        "weighted_amount": float,  # 加权金额（元）
        "historical_conversion_rate": float,  # 历史转化率（%）
        "forecast": {
            "optimistic": float,  # 乐观预测（元）
            "neutral": float,  # 中性预测（元）
            "conservative": float  # 保守预测（元）
        },
        "target_gap": {
            "monthly_target": float,  # 月度目标（元）
            "gap": float,  # 目标差距（元）
            "suggestions": [str]  # 建议措施
        }
    }
    """
    from datetime import datetime
    from calendar import monthrange
    from django.db.models import Sum
    from django.utils import timezone
    from .models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.core.views import _permission_granted
    
    # 获取预测月份
    forecast_month = request.GET.get('month', '')
    if not forecast_month:
        today = timezone.now().date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    try:
        year, month = map(int, forecast_month.split('-'))
        start_date = datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = datetime(year, month, days_in_month).date()
    except (ValueError, IndexError):
        today = timezone.now().date()
        start_date = datetime(today.year, today.month, 1).date()
        days_in_month = monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, days_in_month).date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取活跃商机
    active_opportunities = BusinessOpportunity.objects.exclude(
        status__in=['won', 'lost', 'cancelled']
    )
    
    # 权限过滤
    if not _permission_granted('customer_management.opportunity.view_all', permission_set):
        active_opportunities = active_opportunities.filter(business_manager=request.user)
    
    # 计算本月预计签约的商机
    month_opportunities = active_opportunities.filter(
        expected_sign_date__gte=start_date,
        expected_sign_date__lte=end_date
    )
    
    # 统计基础数据
    total_active = active_opportunities.count()
    total_weighted_amount = float(active_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    month_weighted_amount = float(month_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    
    # 计算历史转化率
    historical_queryset = BusinessOpportunity.objects.filter(
        status__in=['initial_contact', 'requirement_confirmed', 'quotation', 'negotiation', 'won']
    )
    if not _permission_granted('customer_management.opportunity.view_all', permission_set):
        historical_queryset = historical_queryset.filter(business_manager=request.user)
    
    historical_initial = historical_queryset.count()
    historical_won = historical_queryset.filter(status='won').count()
    
    historical_conversion_rate = 35.0  # 默认值
    if historical_initial > 0:
        historical_conversion_rate = (historical_won / historical_initial) * 100
    
    # 计算预测值
    optimistic_forecast = month_weighted_amount * (historical_conversion_rate / 100) * 1.2
    neutral_forecast = month_weighted_amount * (historical_conversion_rate / 100)
    conservative_forecast = month_weighted_amount * (historical_conversion_rate / 100) * 0.8
    
    # 目标差距分析
    monthly_target = total_weighted_amount * 0.6
    target_gap = monthly_target - neutral_forecast
    
    # 生成建议
    suggestions = []
    if target_gap > 0:
        suggestions.append('预测金额低于月度目标，建议加大商机开拓力度')
        suggestions.append('建议提升在途商机的转化率')
        suggestions.append('建议重点关注高价值商机，加快推进速度')
    else:
        suggestions.append('预测金额达到月度目标，继续保持')
        suggestions.append('建议持续跟进在途商机，确保按时签约')
    
    return Response({
        'month': forecast_month,
        'active_opportunities': total_active,
        'weighted_amount': total_weighted_amount,
        'historical_conversion_rate': historical_conversion_rate,
        'forecast': {
            'optimistic': optimistic_forecast,
            'neutral': neutral_forecast,
            'conservative': conservative_forecast
        },
        'target_gap': {
            'monthly_target': monthly_target,
            'gap': target_gap,
            'suggestions': suggestions
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_health_score_api(request, opportunity_id):
    """
    商机健康度评分API
    
    返回:
    {
        "health_score": int,  # 健康度评分（0-100）
        "health_level": str,  # 健康度等级（high/medium/low）
        "dimensions": {
            "followup_timeliness": {
                "score": int,
                "weight": float,
                "label": str
            },
            "information_completeness": {...},
            "client_interaction": {...},
            "stage_progress": {...}
        },
        "suggestions": [str]  # 改进建议
    }
    """
    from .models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.core.views import _permission_granted
    
    opportunity = BusinessOpportunity.objects.select_related('client').prefetch_related('followups').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = _permission_granted('customer_management.opportunity.view', permission_set) or opportunity.business_manager == request.user
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 更新健康度评分
    opportunity.save(update_health=True)
    
    # 获取详细分析
    analysis = opportunity.get_health_analysis()
    
    return Response({
        'health_score': opportunity.health_score,
        'health_level': analysis['health_level'],
        'dimensions': analysis['dimensions'],
        'suggestions': analysis['suggestions'],
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_quality_score_api(request, opportunity_id):
    """
    商机质量评分API
    
    返回:
    {
        "quality_score": int,  # 质量评分（0-100）
        "quality_level": str,  # 质量等级（A/B/C/D）
        "dimensions": {
            "client_qualification": {
                "score": int,
                "weight": float,
                "details": {...}
            },
            "project_reliability": {...},
            "competition_environment": {...}
        },
        "suggestions": [str]  # 改进建议
    }
    """
    from .models import BusinessOpportunity, ClientProject
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.core.views import _permission_granted
    
    opportunity = BusinessOpportunity.objects.select_related('client').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = _permission_granted('customer_management.opportunity.view', permission_set) or opportunity.business_manager == request.user
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 1. 客户资质评分（权重35%）
    client = opportunity.client
    client_qualification_score = 0
    client_details = {}
    
    # 客户信用
    if client.credit_level == 'excellent':
        credit_score = 30
    elif client.credit_level == 'good':
        credit_score = 20
    elif client.credit_level == 'normal':
        credit_score = 10
    else:
        credit_score = 5
    client_qualification_score += credit_score
    client_details['credit_level'] = {'score': credit_score, 'value': client.get_credit_level_display()}
    
    # 合作历史
    project_count = ClientProject.objects.filter(client=client).count()
    if project_count >= 3:
        history_score = 30
    elif project_count >= 1:
        history_score = 15
    else:
        history_score = 0
    client_qualification_score += history_score
    client_details['cooperation_history'] = {'score': history_score, 'value': f'{project_count}个项目'}
    
    # 法律风险
    if client.legal_risk_level == 'low':
        risk_score = 30
    elif client.legal_risk_level in ['medium_low', 'medium']:
        risk_score = 15
    elif client.legal_risk_level in ['medium_high', 'high']:
        risk_score = 0
    else:
        risk_score = 10
    client_qualification_score += risk_score
    client_details['legal_risk'] = {'score': risk_score, 'value': client.get_legal_risk_level_display()}
    
    # 客户资质总分（最高120分，按比例缩放到100分）
    client_qualification_score = min(client_qualification_score, 120) * (100 / 120)
    
    # 2. 项目靠谱程度评分（权重40%）
    project_reliability_score = 0
    project_details = {}
    
    # 项目阶段
    if opportunity.drawing_stage:
        drawing_stage_name = opportunity.drawing_stage.name
        if '施工图' in drawing_stage_name or '已立项' in drawing_stage_name:
            stage_score = 30
        elif '方案' in drawing_stage_name or '初步设计' in drawing_stage_name:
            stage_score = 20
        else:
            stage_score = 10
    else:
        stage_score = 5
    project_reliability_score += stage_score
    project_details['drawing_stage'] = {'score': stage_score, 'value': opportunity.drawing_stage.name if opportunity.drawing_stage else '未设置'}
    
    # 预算确认
    if opportunity.estimated_amount and opportunity.estimated_amount > 0:
        if opportunity.estimated_amount >= 100:
            budget_score = 30
        else:
            budget_score = 20
    else:
        budget_score = 10
    project_reliability_score += budget_score
    project_details['budget_confirmed'] = {'score': budget_score, 'value': f'预计金额：{opportunity.estimated_amount or 0}万元'}
    
    # 时间紧迫性
    if opportunity.urgency == 'very_urgent':
        urgency_score = 30
    elif opportunity.urgency == 'urgent':
        urgency_score = 20
    else:
        urgency_score = 10
    project_reliability_score += urgency_score
    project_details['urgency'] = {'score': urgency_score, 'value': opportunity.get_urgency_display()}
    
    # 项目信息完整度
    info_fields = ['project_name', 'project_address', 'project_type', 'building_area']
    filled_fields = sum(1 for field in info_fields if getattr(opportunity, field, None))
    completeness_score = (filled_fields / len(info_fields)) * 30
    project_reliability_score += completeness_score
    project_details['info_completeness'] = {'score': completeness_score, 'value': f'{filled_fields}/{len(info_fields)}个字段已填'}
    
    # 项目靠谱程度总分（最高120分，按比例缩放到100分）
    project_reliability_score = min(project_reliability_score, 120) * (100 / 120)
    
    # 3. 竞争环境评分（权重25%）
    competition_score = 0
    competition_details = {}
    
    # 竞争激烈度（简化版，基于商机状态判断）
    if opportunity.status in ['quotation', 'negotiation']:
        competition_score = 20  # 进入报价和谈判阶段，说明有一定竞争
    else:
        competition_score = 30  # 早期阶段，竞争较小
    competition_details['competition_intensity'] = {'score': competition_score, 'value': '基于商机阶段判断'}
    
    # 我方优势（简化版，基于健康度判断）
    if opportunity.health_score >= 80:
        advantage_score = 30
    elif opportunity.health_score >= 60:
        advantage_score = 20
    else:
        advantage_score = 10
    competition_score += advantage_score
    competition_details['our_advantage'] = {'score': advantage_score, 'value': f'健康度：{opportunity.health_score}分'}
    
    # 价格敏感度（简化版，基于客户等级判断）
    if client.client_level == 'vip':
        price_sensitivity_score = 30  # VIP客户价格敏感度低
    elif client.client_level == 'key':
        price_sensitivity_score = 20
    else:
        price_sensitivity_score = 10
    competition_score += price_sensitivity_score
    competition_details['price_sensitivity'] = {'score': price_sensitivity_score, 'value': client.get_client_level_display()}
    
    # 竞争环境总分（最高90分，按比例缩放到100分）
    competition_score = min(competition_score, 90) * (100 / 90)
    
    # 计算总质量评分
    quality_score = (
        client_qualification_score * 0.35 +
        project_reliability_score * 0.40 +
        competition_score * 0.25
    )
    
    # 确定质量等级
    if quality_score >= 80:
        quality_level = 'A'
    elif quality_score >= 60:
        quality_level = 'B'
    elif quality_score >= 40:
        quality_level = 'C'
    else:
        quality_level = 'D'
    
    # 生成建议
    suggestions = []
    if quality_score >= 80:
        suggestions.append('商机质量优秀，建议重点投入，优先跟进')
    elif quality_score >= 60:
        suggestions.append('商机质量良好，建议正常跟进，保持节奏')
    elif quality_score >= 40:
        suggestions.append('商机质量一般，建议观察维护，适度投入')
    else:
        suggestions.append('商机质量较低，建议低优先级，资源有限时暂停')
    
    if client_qualification_score < 60:
        suggestions.append('客户资质有待提升，建议加强客户关系维护')
    if project_reliability_score < 60:
        suggestions.append('项目信息不完整，建议完善项目信息')
    
    return Response({
        'quality_score': round(quality_score, 2),
        'quality_level': quality_level,
        'dimensions': {
            'client_qualification': {
                'score': round(client_qualification_score, 2),
                'weight': 0.35,
                'details': client_details
            },
            'project_reliability': {
                'score': round(project_reliability_score, 2),
                'weight': 0.40,
                'details': project_details
            },
            'competition_environment': {
                'score': round(competition_score, 2),
                'weight': 0.25,
                'details': competition_details
            }
        },
        'suggestions': suggestions
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def opportunity_action_suggestions_api(request, opportunity_id):
    """
    智能行动建议API（基于结构化数据）
    
    返回:
    {
        "suggestions": [
            {
                "type": str,  # 建议类型（stage_overdue/info_incomplete/followup_overdue）
                "priority": str,  # 优先级（high/medium/low）
                "action": str,  # 建议行动
                "reason": str  # 原因说明
            }
        ]
    }
    """
    from django.utils import timezone
    from .models import BusinessOpportunity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.core.views import _permission_granted
    
    opportunity = BusinessOpportunity.objects.prefetch_related('followups').get(id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_view = _permission_granted('customer_management.opportunity.view', permission_set) or opportunity.business_manager == request.user
    if not can_view:
        return Response({
            'error': '您没有权限查看此商机'
        }, status=status.HTTP_403_FORBIDDEN)
    
    suggestions = []
    
    # 1. 检查阶段超期
    days_since_created = (timezone.now().date() - opportunity.created_time.date()).days
    
    # 各阶段的平均周期（天）
    average_durations = {
        'potential': 7,
        'initial_contact': 10,
        'requirement_confirmed': 15,
        'quotation': 20,
        'negotiation': 30,
    }
    
    average_duration = average_durations.get(opportunity.status, 15)
    if days_since_created > average_duration * 1.5:
        suggestions.append({
            'type': 'stage_overdue',
            'priority': 'high',
            'action': '立即提交方案' if opportunity.status == 'requirement_confirmed' else '加快跟进频率',
            'reason': f'当前阶段已停留{days_since_created}天，超过平均周期{average_duration}天'
        })
    
    # 2. 检查必填字段完整性
    required_fields = ['project_name', 'estimated_amount', 'expected_sign_date']
    missing_fields = [f for f in required_fields if not getattr(opportunity, f, None)]
    
    if missing_fields:
        suggestions.append({
            'type': 'info_incomplete',
            'priority': 'medium',
            'action': '完善必填信息',
            'reason': f'缺少必填字段：{", ".join(missing_fields)}'
        })
    
    # 3. 检查跟进及时性
    last_followup = opportunity.followups.order_by('-follow_date').first()
    if last_followup and last_followup.next_follow_date:
        days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
        if days_overdue > 0:
            suggestions.append({
                'type': 'followup_overdue',
                'priority': 'high',
                'action': '立即安排跟进',
                'reason': f'已超过预计跟进时间{days_overdue}天'
            })
    elif not last_followup:
        days_since_created = (timezone.now().date() - opportunity.created_time.date()).days
        if days_since_created > 3:
            suggestions.append({
                'type': 'followup_missing',
                'priority': 'high',
                'action': '尽快建立首次联系',
                'reason': f'商机创建已{days_since_created}天，尚未有跟进记录'
            })
    
    return Response({
        'suggestions': suggestions
    }, status=status.HTTP_200_OK)


# ==================== 销售活动 REST API ====================

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def sales_activity_rest_api(request, activity_id=None):
    """
    销售活动REST API接口
    
    GET /api/customer/activities/ - 获取活动列表
    GET /api/customer/activities/<id>/ - 获取活动详情
    POST /api/customer/activities/ - 创建活动
    PUT /api/customer/activities/<id>/ - 更新活动
    DELETE /api/customer/activities/<id>/ - 删除活动
    """
    from datetime import datetime
    from .models import SalesActivity
    from backend.apps.system_management.services import get_user_permission_codes
    from backend.core.views import _permission_granted
    
    if request.method == 'GET':
        if activity_id:
            # 获取单个活动详情
            try:
                activity = SalesActivity.objects.select_related(
                    'sales_person', 'related_opportunity', 'related_client'
                ).get(id=activity_id)
                
                # 权限检查
                permission_set = get_user_permission_codes(request.user)
                can_view = _permission_granted('customer_management.opportunity.view_all', permission_set) or activity.sales_person == request.user
                if not can_view:
                    return Response({'error': '您没有权限查看此活动'}, status=status.HTTP_403_FORBIDDEN)
                
                return Response({
                    'id': activity.id,
                    'activity_type': activity.activity_type,
                    'activity_type_label': activity.get_activity_type_display(),
                    'title': activity.title,
                    'start_time': activity.start_time.isoformat(),
                    'end_time': activity.end_time.isoformat(),
                    'location': activity.location,
                    'description': activity.description,
                    'is_completed': activity.is_completed,
                    'completed_time': activity.completed_time.isoformat() if activity.completed_time else None,
                    'related_opportunity': {
                        'id': activity.related_opportunity.id,
                        'name': activity.related_opportunity.name,
                        'opportunity_number': activity.related_opportunity.opportunity_number,
                    } if activity.related_opportunity else None,
                    'related_client': {
                        'id': activity.related_client.id,
                        'name': activity.related_client.name,
                    } if activity.related_client else None,
                    'sales_person': {
                        'id': activity.sales_person.id,
                        'username': activity.sales_person.username,
                    },
                }, status=status.HTTP_200_OK)
            except SalesActivity.DoesNotExist:
                return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 获取活动列表
            start_date_str = request.GET.get('start', '')
            end_date_str = request.GET.get('end', '')
            
            permission_set = get_user_permission_codes(request.user)
            
            if _permission_granted('customer_management.opportunity.view_all', permission_set):
                activities = SalesActivity.objects.select_related(
                    'sales_person', 'related_opportunity', 'related_client'
                )
            else:
                activities = SalesActivity.objects.filter(
                    sales_person=request.user
                ).select_related('sales_person', 'related_opportunity', 'related_client')
            
            # 日期范围筛选
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    activities = activities.filter(start_time__date__gte=start_date)
                except ValueError:
                    pass
            
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    activities = activities.filter(start_time__date__lte=end_date)
                except ValueError:
                    pass
            
            # 转换为列表
            activities_list = []
            for activity in activities:
                activities_list.append({
                    'id': activity.id,
                    'title': activity.title,
                    'start': activity.start_time.isoformat(),
                    'end': activity.end_time.isoformat(),
                    'type': activity.activity_type,
                    'type_label': activity.get_activity_type_display(),
                    'location': activity.location,
                    'is_completed': activity.is_completed,
                    'related_opportunity': {
                        'id': activity.related_opportunity.id,
                        'name': activity.related_opportunity.name,
                    } if activity.related_opportunity else None,
                    'related_client': {
                        'id': activity.related_client.id,
                        'name': activity.related_client.name,
                    } if activity.related_client else None,
                })
            
            return Response({'activities': activities_list}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # 创建活动
        try:
            activity_type = request.data.get('activity_type')
            title = request.data.get('title')
            start_time_str = request.data.get('start_time')
            end_time_str = request.data.get('end_time')
            location = request.data.get('location', '')
            related_opportunity_id = request.data.get('related_opportunity_id')
            related_client_id = request.data.get('related_client_id')
            description = request.data.get('description', '')
            
            # 验证必填字段
            if not activity_type or not title or not start_time_str or not end_time_str:
                return Response({
                    'error': '活动类型、标题、开始时间和结束时间为必填项'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 解析时间
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({'error': '时间格式错误'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证时间
            if end_time <= start_time:
                return Response({'error': '结束时间必须晚于开始时间'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建活动
            activity = SalesActivity.objects.create(
                sales_person=request.user,
                activity_type=activity_type,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                related_opportunity_id=related_opportunity_id if related_opportunity_id else None,
                related_client_id=related_client_id if related_client_id else None,
                description=description,
            )
            
            return Response({
                'success': True,
                'id': activity.id,
                'message': '活动创建成功'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建销售活动失败: %s', str(e))
            return Response({
                'error': f'创建失败：{str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        # 更新活动
        if not activity_id:
            return Response({'error': '请提供活动ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = SalesActivity.objects.get(id=activity_id)
            
            # 权限检查：只能修改自己的活动
            if activity.sales_person != request.user:
                return Response({'error': '您没有权限修改此活动'}, status=status.HTTP_403_FORBIDDEN)
            
            # 更新字段
            if 'is_completed' in request.data:
                activity.is_completed = request.data['is_completed']
                if activity.is_completed and not activity.completed_time:
                    from django.utils import timezone
                    activity.completed_time = timezone.now()
            
            if 'title' in request.data:
                activity.title = request.data['title']
            if 'description' in request.data:
                activity.description = request.data['description']
            if 'location' in request.data:
                activity.location = request.data['location']
            
            activity.save()
            
            return Response({
                'success': True,
                'message': '活动更新成功'
            }, status=status.HTTP_200_OK)
        except SalesActivity.DoesNotExist:
            return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新销售活动失败: %s', str(e))
            return Response({
                'error': f'更新失败：{str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        # 删除活动
        if not activity_id:
            return Response({'error': '请提供活动ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = SalesActivity.objects.get(id=activity_id)
            
            # 权限检查：只能删除自己的活动
            if activity.sales_person != request.user:
                return Response({'error': '您没有权限删除此活动'}, status=status.HTTP_403_FORBIDDEN)
            
            activity.delete()
            
            return Response({
                'success': True,
                'message': '活动删除成功'
            }, status=status.HTTP_200_OK)
        except SalesActivity.DoesNotExist:
            return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除销售活动失败: %s', str(e))
            return Response({
                'error': f'删除失败：{str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'error': '不支持的请求方法'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# ==================== 客户管理模块ViewSet（按《客户管理详细设计方案 v1.12》实现）====================

class ClientViewSet(viewsets.ModelViewSet):
    """客户ViewSet"""
    queryset = Client.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client_level', 'grade', 'credit_level', 'client_type', 'industry', 'region', 'source', 'is_active']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
    def get_queryset(self):
        queryset = Client.objects.select_related('created_by', 'responsible_user').all()
        
        # 搜索
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(unified_credit_code__icontains=search)
            )
        
        # 公海过滤
        public_sea = self.request.query_params.get('public_sea', '').strip()
        if public_sea == 'true':
            queryset = queryset.filter(responsible_user__isnull=True)
        elif public_sea == 'false':
            queryset = queryset.filter(responsible_user__isnull=False)
        
        # 负责人过滤
        responsible_user = self.request.query_params.get('responsible_user', '').strip()
        if responsible_user:
            queryset = queryset.filter(responsible_user_id=responsible_user)
        
        return queryset.order_by('-created_time')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """客户统计信息"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        vip_count = queryset.filter(client_level='vip').count()
        important_count = queryset.filter(client_level='important').count()
        general_count = queryset.filter(client_level='general').count()
        potential_count = queryset.filter(client_level='potential').count()
        
        public_sea_count = queryset.filter(responsible_user__isnull=True).count()
        active_count = queryset.filter(is_active=True).count()
        
        return Response({
            'total': total,
            'vip_count': vip_count,
            'important_count': important_count,
            'general_count': general_count,
            'potential_count': potential_count,
            'public_sea_count': public_sea_count,
            'active_count': active_count,
        })


class ClientContactViewSet(viewsets.ModelViewSet):
    """客户联系人ViewSet"""
    queryset = ClientContact.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'role', 'relationship_level', 'decision_influence']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientContactCreateSerializer
        return ClientContactSerializer
    
    def get_queryset(self):
        queryset = ClientContact.objects.select_related('client', 'created_by').all()
        
        # 搜索
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        return queryset.order_by('-created_time')
    
    @action(detail=True, methods=['put'])
    def update_role(self, request, pk=None):
        """更新人员角色"""
        contact = self.get_object()
        role = request.data.get('role')
        if role not in dict(ClientContact.ROLE_CHOICES):
            return Response({'error': '无效的角色'}, status=status.HTTP_400_BAD_REQUEST)
        contact.role = role
        contact.save()
        return Response(ClientContactSerializer(contact).data)
    
    @action(detail=True, methods=['put'])
    def update_relationship_level(self, request, pk=None):
        """更新关系等级"""
        contact = self.get_object()
        level = request.data.get('relationship_level')
        if level not in dict(ClientContact.RELATIONSHIP_LEVEL_CHOICES):
            return Response({'error': '无效的关系等级'}, status=status.HTTP_400_BAD_REQUEST)
        contact.relationship_level = level
        contact.save()
        return Response(ClientContactSerializer(contact).data)
    
    @action(detail=True, methods=['put'])
    def update_last_contact_time(self, request, pk=None):
        """更新最后联系时间"""
        contact = self.get_object()
        contact.update_last_contact_time()
        contact.save()
        return Response(ClientContactSerializer(contact).data)
    
    @action(detail=True, methods=['get'])
    def calculate_relationship_score(self, request, pk=None):
        """计算关系评分"""
        contact = self.get_object()
        score = contact.calculate_relationship_score()
        contact.relationship_score = score
        contact.save(update_fields=['relationship_score'])
        return Response({'relationship_score': score})
    
    @action(detail=True, methods=['get'])
    def related_contacts(self, request, pk=None):
        """查找关联的客户人员（根据教育背景和工作经历）"""
        from .services import find_all_related_contacts
        
        contact = self.get_object()
        related_contacts, relation_reasons = find_all_related_contacts(contact)
        
        # 序列化关联联系人
        serializer = ClientContactSerializer(related_contacts, many=True)
        
        # 添加关联原因
        result = []
        for contact_data in serializer.data:
            contact_id = contact_data['id']
            contact_data['relation_reasons'] = relation_reasons.get(contact_id, [])
            result.append(contact_data)
        
        return Response({
            'related_contacts': result,
            'total': len(result)
        })
    
    @action(detail=True, methods=['get', 'post'])
    def work_experiences(self, request, pk=None):
        """工作经历管理"""
        contact = self.get_object()
        if request.method == 'GET':
            experiences = ContactWorkExperience.objects.filter(contact=contact).order_by('-start_date')
            serializer = ContactWorkExperienceSerializer(experiences, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = ContactWorkExperienceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def educations(self, request, pk=None):
        """教育背景管理"""
        contact = self.get_object()
        if request.method == 'GET':
            educations = ContactEducation.objects.filter(contact=contact).order_by('-start_date')
            serializer = ContactEducationSerializer(educations, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = ContactEducationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def upload_resume(self, request, pk=None):
        """上传简历文件"""
        contact = self.get_object()
        resume_file = request.FILES.get('resume_file')
        resume_source = request.data.get('resume_source', 'other')
        
        if not resume_file:
            return Response({'error': '请上传简历文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        contact.resume_file = resume_file
        contact.resume_source = resume_source
        contact.resume_upload_time = timezone.now()
        contact.save()
        
        return Response(ClientContactSerializer(contact).data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """联系人统计信息"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        role_stats = queryset.values('role').annotate(count=Count('id'))
        level_stats = queryset.values('relationship_level').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'role_statistics': list(role_stats),
            'level_statistics': list(level_stats),
        })


class CustomerRelationshipViewSet(viewsets.ModelViewSet):
    """客户关系（跟进与拜访）ViewSet"""
    queryset = CustomerRelationship.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'followup_method', 'relationship_level']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerRelationshipCreateSerializer
        return CustomerRelationshipSerializer
    
    def get_queryset(self):
        queryset = CustomerRelationship.objects.select_related(
            'client', 'followup_person'
        ).prefetch_related('related_contacts').all()
        
        # 搜索
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(client__name__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset.order_by('-followup_time')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """关系记录统计"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        method_stats = queryset.values('followup_method').annotate(count=Count('id'))
        level_stats = queryset.values('relationship_level').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'method_statistics': list(method_stats),
            'level_statistics': list(level_stats),
        })


class CustomerRelationshipUpgradeViewSet(viewsets.ModelViewSet):
    """关系升级ViewSet"""
    queryset = CustomerRelationshipUpgrade.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'from_level', 'to_level', 'approval_status']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerRelationshipUpgradeCreateSerializer
        return CustomerRelationshipUpgradeSerializer
    
    def get_queryset(self):
        queryset = CustomerRelationshipUpgrade.objects.select_related(
            'client', 'created_by'
        ).prefetch_related('related_contacts').all()
        
        # 搜索
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(client__name__icontains=search) |
                Q(upgrade_reason__icontains=search)
            )
        
        return queryset.order_by('-created_time')
    
    @action(detail=True, methods=['put'])
    def approve(self, request, pk=None):
        """审批关系升级（通过审批流程引擎）"""
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance
        from backend.apps.workflow_engine.services import ApprovalEngine
        
        upgrade = self.get_object()
        
        # 检查是否已有审批实例
        if upgrade.approval_instance:
            approval_instance = upgrade.approval_instance
            # 可以通过审批流程引擎进行审批
            # 这里返回当前状态，实际审批通过审批流程引擎的API进行
            return Response({
                'message': '关系升级已关联审批流程',
                'approval_instance': approval_instance.instance_number,
                'approval_status': approval_instance.status,
                'upgrade': CustomerRelationshipUpgradeSerializer(upgrade).data
            })
        else:
            return Response({
                'error': '该关系升级申请未关联审批流程'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """关系等级统计"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        from_level_stats = queryset.values('from_level').annotate(count=Count('id'))
        to_level_stats = queryset.values('to_level').annotate(count=Count('id'))
        status_stats = queryset.values('approval_status').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'from_level_statistics': list(from_level_stats),
            'to_level_statistics': list(to_level_stats),
            'status_statistics': list(status_stats),
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def regeocode_location(request):
    """
    逆地理编码API：根据经纬度获取地址信息
    
    请求参数:
    - longitude: 经度（必需）
    - latitude: 纬度（必需）
    
    返回:
    {
        "success": bool,
        "formatted_address": str,  # 格式化地址
        "province": str,  # 省份
        "city": str,  # 城市
        "district": str,  # 区县
        "township": str,  # 街道
        "adcode": str,  # 区域编码
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        longitude = request.GET.get('longitude', '').strip()
        latitude = request.GET.get('latitude', '').strip()
        
        if not longitude or not latitude:
            return Response({
                'success': False,
                'message': '请提供经度和纬度参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            longitude = float(longitude)
            latitude = float(latitude)
        except ValueError:
            return Response({
                'success': False,
                'message': '经纬度格式不正确'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 调用高德地图逆地理编码服务
        amap_service = AmapAPIService()
        result = amap_service.regeocode(longitude, latitude)
        
        if result:
            return Response({
                'success': True,
                'formatted_address': result.get('formatted_address', ''),
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'district': result.get('district', ''),
                'township': result.get('township', ''),
                'adcode': result.get('adcode', ''),
                'neighborhood': result.get('neighborhood', {}).get('name', '') if result.get('neighborhood') else '',
                'building': result.get('building', {}).get('name', '') if result.get('building') else '',
                'message': '获取地址成功'
            })
        else:
            return Response({
                'success': False,
                'message': '无法获取地址信息，请检查坐标是否正确'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.exception('逆地理编码失败: %s', str(e))
        return Response({
            'success': False,
            'message': f'获取地址失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ip_location_api(request):
    """
    IP定位API：根据IP地址获取位置信息（备选方案）
    
    请求参数:
    - ip: IP地址（可选，不传则使用请求IP）
    
    返回:
    {
        "success": bool,
        "province": str,  # 省份
        "city": str,  # 城市
        "adcode": str,  # 区域编码
        "center_longitude": float,  # 中心点经度
        "center_latitude": float,  # 中心点纬度
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        ip = request.GET.get('ip', '').strip()
        
        # 如果没有提供IP，尝试从请求头获取
        if not ip:
            # 尝试从X-Forwarded-For获取真实IP（如果使用代理）
            forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if forwarded_for:
                ip = forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', '')
        
        # 调用高德地图IP定位服务
        amap_service = AmapAPIService()
        result = amap_service.ip_location(ip if ip else None)
        
        if result:
            # IP定位返回的是城市级别，没有详细地址
            # 可以返回城市中心点坐标
            rectangle = result.get('rectangle', '')
            center_lon = None
            center_lat = None
            
            if rectangle:
                # rectangle格式: "min_lon,min_lat;max_lon,max_lat"
                try:
                    coords = rectangle.split(';')
                    if len(coords) == 2:
                        min_coords = coords[0].split(',')
                        max_coords = coords[1].split(',')
                        center_lon = (float(min_coords[0]) + float(max_coords[0])) / 2
                        center_lat = (float(min_coords[1]) + float(max_coords[1])) / 2
                except (ValueError, IndexError):
                    pass
            
            return Response({
                'success': True,
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'adcode': result.get('adcode', ''),
                'rectangle': rectangle,
                'center_longitude': center_lon,
                'center_latitude': center_lat,
                'message': 'IP定位成功（城市级别）'
            })
        else:
            return Response({
                'success': False,
                'message': '无法获取IP位置信息'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.exception('IP定位失败: %s', str(e))
        return Response({
            'success': False,
            'message': f'IP定位失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_districts(request):
    """
    获取行政区划数据API：根据关键词和级别获取省市区数据
    
    请求参数:
    - keywords: 查询关键字，支持：行政区名称、citycode、adcode（可选）
    - level: 查询行政级别，可选值：country、province、city、district、street（可选）
    - subdistrict: 子级行政区，0：不返回下级行政区；1：返回下一级行政区；2：返回下两级行政区；3：返回下三级行政区（默认1）
    
    返回:
    {
        "success": bool,
        "districts": [
            {
                "name": "北京市",
                "adcode": "110000",
                "citycode": "010",
                "level": "province",
                "center": "116.407526,39.904030",
                "districts": [...]  # 下级行政区
            }
        ],
        "message": str
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        keywords = request.GET.get('keywords', '').strip()
        level = request.GET.get('level', '').strip()
        try:
            subdistrict = int(request.GET.get('subdistrict', 1))
        except ValueError:
            subdistrict = 1
        
        # 记录查询参数（用于调试）
        logger.info(f'查询行政区划: keywords={keywords}, level={level}, subdistrict={subdistrict}')
        
        # 检查高德地图API配置
        amap_service = AmapAPIService()
        if not amap_service.api_key:
            logger.error('高德地图API Key未配置')
            return Response({
                'success': False,
                'districts': [],
                'message': '高德地图API Key未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 调用高德地图行政区划查询服务
        try:
            result = amap_service.district_search(keywords, subdistrict, level)
        except Exception as e:
            logger.exception(f'高德地图API调用异常: {str(e)}')
            return Response({
                'success': False,
                'districts': [],
                'message': f'高德地图API调用异常：{str(e)}'
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        if not result:
            logger.warning('高德地图API调用失败：返回结果为空')
            return Response({
                'success': False,
                'districts': [],
                'message': '高德地图API调用失败，请检查配置或稍后重试'
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        status_code = result.get('status', '0')
        if status_code != '1':
            error_info = result.get('info', '未知错误')
            logger.warning(f'高德地图API返回错误: status={status_code}, info={error_info}')
            return Response({
                'success': False,
                'districts': [],
                'message': f'获取行政区划数据失败：{error_info}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        districts = result.get('districts', [])
        if not districts or len(districts) == 0:
            return Response({
                'success': False,
                'districts': [],
                'message': '未找到行政区划数据'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 处理返回数据
        # 根据高德地图API文档：
        # 1. 查询省份列表（level=province且keywords为空）：返回districts数组，每个元素是一个省份对象
        #   注意：高德地图API可能返回嵌套结构，需要检查是否有嵌套的districts
        # 2. 查询特定省份下的城市（keywords=省份adcode，subdistrict=1）：返回districts数组，第一个元素是该省份对象，其districts字段包含城市列表
        # 3. 查询特定城市下的区县（keywords=城市adcode，subdistrict=1）：返回districts数组，第一个元素是该城市对象，其districts字段包含区县列表
        
        if level == 'province' and not keywords:
            # 查询所有省份
            # 根据高德地图API文档，查询所有省份有两种方式：
            # 1. level=province, keywords="", subdistrict=0 - 可能只返回部分省份（约20个）
            # 2. level=country, keywords="中国", subdistrict=1 - 返回中国对象，其districts包含所有省份（34个）
            
            # 优先使用国家级别查询，确保获取所有省份
            logger.info('查询省份列表，优先使用国家级别查询')
            try:
                country_result = amap_service.district_search('中国', subdistrict=1, level='country')
                if country_result and country_result.get('status') == '1':
                    country_districts = country_result.get('districts', [])
                    if len(country_districts) > 0:
                        country_obj = country_districts[0]
                        if country_obj.get('level') == 'country' and country_obj.get('districts'):
                            provinces = country_obj.get('districts', [])
                            logger.info(f'使用国家级别查询成功，获取{len(provinces)}个省份')
                            return Response({
                                'success': True,
                                'districts': provinces,
                                'message': f'获取省份列表成功，共{len(provinces)}个省份'
                            })
            except Exception as e:
                logger.warning(f'使用国家级别查询失败: {str(e)}，回退到省份级别查询')
            
            # 如果国家级别查询失败，使用原始返回的数据
            # 如果返回的数据少于30个省份，记录警告
            if len(districts) < 30:
                logger.warning(f'使用level=province查询只返回{len(districts)}个省份，可能不完整')
            
            # 使用原始返回的数据
            result_districts = []
            
            # 检查是否是嵌套结构（返回"中国"对象）
            if len(districts) == 1 and isinstance(districts[0], dict):
                first_item = districts[0]
                # 如果第一个元素的level是country（国家），说明是嵌套结构
                if first_item.get('level') == 'country' and first_item.get('districts'):
                    result_districts = first_item.get('districts', [])
                    logger.info(f'检测到嵌套结构，从国家对象中提取省份列表')
                # 如果第一个元素有districts字段且level不是province，也可能是嵌套结构
                elif first_item.get('districts') and first_item.get('level') != 'province':
                    result_districts = first_item.get('districts', [])
                    logger.info(f'检测到嵌套结构，从父级对象中提取省份列表')
            
            # 如果不是嵌套结构，直接使用districts数组
            if not result_districts:
                # 过滤出level为province的对象
                result_districts = [d for d in districts if isinstance(d, dict) and d.get('level') == 'province']
                # 如果过滤后为空，使用原始districts（可能所有元素都是省份）
                if not result_districts:
                    result_districts = districts
            
            logger.info(f'查询省份列表，原始返回{len(districts)}个元素，处理后{len(result_districts)}个省份')
            logger.debug(f'省份列表: {[d.get("name") for d in result_districts[:5]]}...')  # 只记录前5个
            
            return Response({
                'success': True,
                'districts': result_districts,
                'message': f'获取省份列表成功，共{len(result_districts)}个省份'
            })
        
        # 查询特定区域的下级行政区
        # 根据高德地图API文档：
        # - 当查询城市时（keywords=省份adcode，level=city），返回districts数组
        #   第一个元素是该省份对象，其districts字段包含城市列表
        # - 当查询区县时（keywords=城市adcode，level=district），返回districts数组
        #   第一个元素是该城市对象，其districts字段包含区县列表
        
        if len(districts) > 0:
            first_district = districts[0]
            
            # 检查第一个区域是否有districts字段（下级行政区）
            if isinstance(first_district, dict) and first_district.get('districts'):
                sub_districts = first_district.get('districts', [])
                if len(sub_districts) > 0:
                    # 返回下级行政区列表（城市或区县）
                    return Response({
                        'success': True,
                        'districts': sub_districts,
                        'message': '获取行政区划数据成功'
                    })
            
            # 如果第一个区域没有districts字段，但有level字段
            # 检查是否是查询结果本身就是目标级别的列表
            if isinstance(first_district, dict):
                first_level = first_district.get('level', '')
                # 如果查询的是城市级别，且第一个元素的level是city，说明返回的就是城市列表
                if level == 'city' and first_level == 'city':
                    return Response({
                        'success': True,
                        'districts': districts,
                        'message': '获取城市列表成功'
                    })
                # 如果查询的是区县级别，且第一个元素的level是district，说明返回的就是区县列表
                if level == 'district' and first_level == 'district':
                    return Response({
                        'success': True,
                        'districts': districts,
                        'message': '获取区县列表成功'
                    })
            
            # 其他情况：返回districts数组本身
            return Response({
                'success': True,
                'districts': districts,
                'message': '获取行政区划数据成功'
            })
        
        return Response({
            'success': False,
            'districts': [],
            'message': '未找到行政区划数据'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.exception('获取行政区划数据失败: %s', str(e))
        return Response({
            'success': False,
            'districts': [],
            'message': f'获取行政区划数据失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_our_company_info(request):
    """
    根据公司名称获取我方主体信息API
    
    请求参数:
    - company_name: 公司名称
    
    返回:
    {
        "success": bool,
        "data": {
            "company_name": str,
            "credit_code": str,
            "legal_representative": str,
            "registered_address": str
        },
        "message": str
    }
    """
    from backend.apps.system_management.models import OurCompany
    
    try:
        company_name = request.GET.get('company_name', '').strip()
        
        if not company_name:
            return Response({
                'success': False,
                'data': None,
                'message': '公司名称不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 查询我方主体信息
        company = OurCompany.objects.filter(
            company_name=company_name,
            is_active=True
        ).first()
        
        if not company:
            return Response({
                'success': False,
                'data': None,
                'message': '未找到对应的我方主体信息'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'company_name': company.company_name,
                'credit_code': company.credit_code or '',
                'legal_representative': company.legal_representative or '',
                'registered_address': company.registered_address or ''
            },
            'message': '获取我方主体信息成功'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取我方主体信息失败: %s', str(e))
        return Response({
            'success': False,
            'data': None,
            'message': f'获取我方主体信息失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_opportunities_by_client_name(request):
    """
    根据客户ID或客户名称获取商机列表API
    从商机管理中获取该客户的所有商机
    """
    """
    根据客户ID或客户名称获取商机列表API
    
    请求参数:
    - client_id: 客户ID（优先使用）
    - client_name: 客户名称（可选，如果client_id未提供则使用）
    
    返回:
    {
        "success": bool,
        "opportunities": [
            {
                "id": int,
                "name": str,
                "opportunity_number": str,
                "client": {
                    "id": int,
                    "name": str
                }
            }
        ],
        "message": str
    }
    """
    from .models import BusinessOpportunity
    
    try:
        opportunity_id = request.GET.get('opportunity_id', '').strip()
        client_id = request.GET.get('client_id', '').strip()
        client_name = request.GET.get('client_name', '').strip()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'[商机API] 请求参数 - opportunity_id: {opportunity_id}, client_id: {client_id}, client_name: {client_name}')
        
        # 如果提供了opportunity_id，返回单个商机详情
        if opportunity_id:
            try:
                opportunity_id_int = int(opportunity_id)
                opportunity = BusinessOpportunity.objects.select_related('client').get(id=opportunity_id_int)
                opportunity_data = {
                    'id': opportunity.id,
                    'name': opportunity.name,
                    'opportunity_number': opportunity.opportunity_number or '',
                    'status': opportunity.status,
                    'status_display': opportunity.get_status_display() if hasattr(opportunity, 'get_status_display') else opportunity.status,
                    'is_active': opportunity.is_active,
                    'project_type': opportunity.project_type or '',
                    'client': {
                        'id': opportunity.client.id if opportunity.client else None,
                        'name': opportunity.client.name if opportunity.client else '未指定客户'
                    }
                }
                return Response({
                    'success': True,
                    'opportunity': opportunity_data,
                    'message': '获取商机详情成功'
                })
            except (ValueError, TypeError) as e:
                logger.warning(f'[商机API] opportunity_id转换失败: {opportunity_id}, 错误: {e}')
                return Response({
                    'success': False,
                    'opportunity': None,
                    'message': f'商机ID无效：{opportunity_id}'
                }, status=status.HTTP_400_BAD_REQUEST)
            except BusinessOpportunity.DoesNotExist:
                logger.warning(f'[商机API] 商机不存在: ID={opportunity_id}')
                return Response({
                    'success': False,
                    'opportunity': None,
                    'message': f'商机不存在：ID={opportunity_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # 获取商机列表（从商机管理中获取该客户的所有商机，包含所有状态）
        # 优先使用client_id过滤，如果没有则使用client_name
        opportunities = BusinessOpportunity.objects.all().select_related('client').order_by('-created_time')
        
        if client_id:
            try:
                client_id_int = int(client_id)
                # 先检查客户是否存在
                from .models import Client
                try:
                    client_obj = Client.objects.get(id=client_id_int)
                    logger.info(f'[商机API] 客户存在: {client_obj.name} (ID: {client_id_int})')
                except Client.DoesNotExist:
                    logger.warning(f'[商机API] 客户不存在: ID={client_id_int}')
                    opportunities = BusinessOpportunity.objects.none()
                else:
                    opportunities = opportunities.filter(client_id=client_id_int)
                    count_before_limit = opportunities.count()
                    logger.info(f'[商机API] 使用client_id过滤: {client_id_int}, 找到 {count_before_limit} 个商机')
                    # 记录前5个商机的详细信息用于调试
                    for i, opp in enumerate(opportunities[:5]):
                        logger.info(f'[商机API] 商机 {i+1}: ID={opp.id}, name={opp.name}, client_id={opp.client_id}, is_active={opp.is_active}')
            except (ValueError, TypeError) as e:
                logger.warning(f'[商机API] client_id转换失败: {client_id}, 错误: {e}')
                opportunities = BusinessOpportunity.objects.none()
        elif client_name:
            opportunities = opportunities.filter(client__name=client_name)
            count_before_limit = opportunities.count()
            logger.info(f'[商机API] 使用client_name过滤: {client_name}, 找到 {count_before_limit} 个商机')
            # 记录前5个商机的详细信息用于调试
            for i, opp in enumerate(opportunities[:5]):
                logger.info(f'[商机API] 商机 {i+1}: ID={opp.id}, name={opp.name}, client_id={opp.client_id}, is_active={opp.is_active}')
        else:
            # 如果没有提供client_id或client_name，返回空列表
            logger.warning('[商机API] 未提供client_id或client_name参数')
            opportunities = BusinessOpportunity.objects.none()
        
        # 限制返回数量（最多100条）
        opportunities = opportunities[:100]
        logger.info(f'[商机API] 最终返回 {len(opportunities)} 个商机')
        
        # 构建返回数据（从商机管理中获取，包含状态信息）
        opportunities_data = []
        for opp in opportunities:
            opportunities_data.append({
                'id': opp.id,
                'name': opp.name,
                'opportunity_number': opp.opportunity_number or '',
                'status': opp.status,  # 商机状态
                'status_display': opp.get_status_display() if hasattr(opp, 'get_status_display') else opp.status,  # 状态显示名称
                'is_active': opp.is_active,  # 是否激活
                'project_type': opp.project_type or '',  # 项目业态
                'client': {
                    'id': opp.client.id if opp.client else None,
                    'name': opp.client.name if opp.client else '未指定客户'
                }
            })
        
        return Response({
            'success': True,
            'opportunities': opportunities_data,
            'message': '获取商机列表成功'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取商机列表失败: %s', str(e))
        return Response({
            'success': False,
            'opportunities': [],
            'message': f'获取商机列表失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_client_address(request):
    """
    根据客户ID获取客户办公地址API
    
    请求参数:
    - client_id: 客户ID（必填）
    
    返回:
    {
        "success": bool,
        "address": str,
        "message": str
    }
    """
    try:
        client_id = request.GET.get('client_id', '').strip()
        if not client_id:
            return Response({
                'success': False,
                'address': '',
                'message': '客户ID不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            client = Client.objects.get(id=int(client_id))
            # 返回region字段（办公地址），这是客户表单中使用的地址格式
            address = client.region or ''
            return Response({
                'success': True,
                'address': address,
                'message': '获取成功'
            }, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'address': '',
                'message': '客户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({
                'success': False,
                'address': '',
                'message': '无效的客户ID'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取客户办公地址失败: %s', str(e))
        return Response({
            'success': False,
            'address': '',
            'message': f'获取失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_client_info(request):
    """
    根据客户ID获取客户完整信息API（用于自动填充联系人表单和合同签约主体）
    
    请求参数:
    - client_id: 客户ID（必填）
    
    返回:
    {
        "success": bool,
        "data": {
            "name": str,              # 客户名称
            "unified_credit_code": str, # 统一信用代码
            "legal_representative": str, # 法定代表人
            "address": str             # 办公地址
        },
        "message": str
    }
    """
    try:
        client_id = request.GET.get('client_id', '').strip()
        if not client_id:
            return Response({
                'success': False,
                'data': {},
                'message': '客户ID不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import Client
            client = Client.objects.get(id=int(client_id))
            return Response({
                'success': True,
                'data': {
                    'name': client.name or '',
                    'unified_credit_code': client.unified_credit_code or '',
                    'legal_representative': client.legal_representative or '',
                    'address': client.company_address or client.region or ''  # 优先返回company_address，如果没有则返回region字段（办公地址）
                },
                'message': '获取成功'
            }, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({
                'success': False,
                'data': {},
                'message': '客户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({
                'success': False,
                'data': {},
                'message': '客户ID格式错误'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取客户信息失败: %s', str(e))
        return Response({
            'success': False,
            'data': {},
            'message': f'获取客户信息失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_contact_info(request, contact_id):
    """获取联系人信息API"""
    try:
        contact = ClientContact.objects.get(id=contact_id)
        return Response({
            'id': contact.id,
            'name': contact.name,
            'gender': contact.gender,
            'birthplace': contact.birthplace or '',
            'phone': contact.phone or '',
            'email': contact.email or '',
            'wechat': contact.wechat or '',
            'office_address': contact.office_address or '',
            'role': contact.role,
            'relationship_level': contact.relationship_level,
            'decision_influence': contact.decision_influence,
            'contact_frequency': contact.contact_frequency or '',
            'tracking_cycle_days': contact.tracking_cycle_days,
            'is_primary': contact.is_primary,
            'notes': contact.notes or '',
        })
    except ClientContact.DoesNotExist:
        return Response({'error': '联系人不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取联系人信息失败: %s', str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_contacts_by_client_id(request):
    """
    根据客户ID获取联系人列表API
    
    请求参数:
    - client_id: 客户ID（必填）
    
    返回:
    {
        "success": bool,
        "contacts": [
            {
                "id": int,
                "name": str,
                "phone": str,
                "email": str,
                "office_address": str
            }
        ],
        "message": str
    }
    """
    try:
        client_id = request.GET.get('client_id', '').strip()
        
        if not client_id:
            return Response({
                'success': False,
                'contacts': [],
                'message': '请提供客户ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取联系人列表
        contacts = ClientContact.objects.filter(client_id=client_id).order_by('name')
        
        # 构建返回数据
        contacts_data = []
        for contact in contacts:
            contacts_data.append({
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone or '',
                'email': contact.email or '',
                'office_address': contact.office_address or ''
            })
        
        return Response({
            'success': True,
            'contacts': contacts_data,
            'message': '获取联系人列表成功'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取联系人列表失败: %s', str(e))
        return Response({
            'success': False,
            'contacts': [],
            'message': f'获取联系人列表失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_schools(request):
    """
    学校模糊搜索API
    
    注意：此API返回所有激活的学校，不限制985、211标签。
    
    请求参数:
    - keyword: 搜索关键词（可选，支持学校名称、地区搜索）
    - limit: 返回结果数量限制（可选，默认50）
    
    返回:
    {
        "success": bool,
        "schools": [
            {
                "id": int,
                "name": str,
                "region": str,
                "region_display": str,
                "is_211": bool,
                "is_985": bool,
                "is_double_first_class": bool,
                "tags": str,
                "display_name": str
            }
        ],
        "total": int,
        "message": str
    }
    """
    try:
        keyword = request.GET.get('keyword', '').strip()
        limit = int(request.GET.get('limit', 50))
        
        # 构建查询
        queryset = School.objects.filter(is_active=True)
        
        if keyword:
            # 模糊搜索：学校名称、地区代码
            # 注意：地区显示名称需要在Python层面过滤，因为get_region_display是方法
            queryset = queryset.filter(
                Q(name__icontains=keyword) |
                Q(region__icontains=keyword)
            )
        
        # 按显示顺序、地区、名称排序
        schools = queryset.order_by('display_order', 'region', 'name')[:limit]
        
        # 构建返回数据
        school_list = []
        for school in schools:
            tags = []
            if school.is_985:
                tags.append('985')
            if school.is_211:
                tags.append('211')
            if school.is_double_first_class:
                tags.append('双一流')
            
            school_list.append({
                'id': school.id,
                'name': school.name,
                'region': school.region,
                'region_display': school.get_region_display(),
                'is_211': school.is_211,
                'is_985': school.is_985,
                'is_double_first_class': school.is_double_first_class,
                'tags': ', '.join(tags) if tags else '',
                'display_name': f"{school.name} ({', '.join(tags)})" if tags else school.name
            })
        
        return Response({
            'success': True,
            'schools': school_list,
            'total': len(school_list),
            'message': '搜索成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('学校搜索失败: %s', str(e))
        return Response({
            'success': False,
            'schools': [],
            'total': 0,
            'message': f'搜索失败：{str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def recognize_contract(request):
    """
    合同识别API
    上传合同文件，使用DeepSeek API识别并提取合同信息
    
    请求参数:
    - file: 合同文件（PDF、图片等）
    
    返回:
    {
        "success": bool,
        "data": {
            "contract_name": "合同名称",
            "contract_number": "合同编号",
            "contract_type": "合同类型",
            "contract_amount": "合同金额",
            "contract_date": "签订日期",
            "effective_date": "生效日期",
            "start_date": "开始日期",
            "end_date": "结束日期",
            "party_a": {...},
            "party_b": {...},
            "description": "描述",
            "notes": "备注"
        },
        "error": "错误信息（如果失败）"
    }
    """
    import logging
    import tempfile
    from django.core.files.uploadedfile import UploadedFile
    from .services.contract_recognition import ContractRecognitionService
    
    logger = logging.getLogger(__name__)
    
    try:
        # 检查文件是否存在
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': '请上传合同文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file: UploadedFile = request.FILES['file']
        
        # 检查文件类型
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            return Response({
                'success': False,
                'error': f'不支持的文件类型: {file_ext}，支持的类型: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查文件大小（限制为10MB）
        if uploaded_file.size > 10 * 1024 * 1024:
            return Response({
                'success': False,
                'error': '文件大小不能超过10MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # 确定文件类型
            file_type = 'pdf' if file_ext == '.pdf' else 'image' if file_ext in ['.jpg', '.jpeg', '.png'] else 'docx'
            
            # 调用识别服务
            recognition_service = ContractRecognitionService()
            result = recognition_service.recognize_contract(tmp_file_path, file_type)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            if result.get('success'):
                return Response({
                    'success': True,
                    'data': result.get('data', {}),
                    'raw_text': result.get('raw_text', '')
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', '识别失败')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            # 确保临时文件被删除
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e
            
    except Exception as e:
        logger.exception(f"合同识别API错误: {str(e)}")
        return Response({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
