# -*- coding: utf-8 -*-
"""
初始化启信宝API信息到后台API管理
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from backend.apps.api_management.models import ExternalSystem, ApiInterface

User = get_user_model()


class Command(BaseCommand):
    help = '初始化启信宝API信息到后台API管理'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果系统已存在，则更新信息',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='指定创建人用户ID（默认为第一个超级用户）',
        )

    def handle(self, *args, **options):
        update = options.get('update', False)
        user_id = options.get('user_id')
        
        # 获取创建人
        if user_id:
            try:
                creator = User.objects.get(id=user_id, is_staff=True)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户ID {user_id} 不存在或不是员工'))
                return
        else:
            # 获取第一个超级用户
            creator = User.objects.filter(is_superuser=True, is_staff=True).first()
            if not creator:
                # 如果没有超级用户，获取第一个员工用户
                creator = User.objects.filter(is_staff=True).first()
            if not creator:
                self.stdout.write(self.style.ERROR('未找到可用的用户，请先创建管理员用户'))
                return
        
        self.stdout.write(f'使用用户: {creator.username} (ID: {creator.id})')
        
        # 从环境变量获取API配置
        app_key = getattr(settings, 'QIXINBAO_APP_KEY', '')
        app_secret = getattr(settings, 'QIXINBAO_APP_SECRET', '')
        base_url = getattr(settings, 'QIXINBAO_API_BASE_URL', 'https://api.qixin.com')
        
        # 检查是否已存在启信宝系统
        qixinbao_system, created = ExternalSystem.objects.get_or_create(
            code='QIXINBAO',
            defaults={
                'name': '启信宝',
                'description': '启信宝企业信息查询平台，提供企业工商信息、法律风险、被执行记录等查询服务',
                'base_url': base_url,
                'status': 'active',
                'is_active': True,
                'created_by': creator,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 已创建外部系统: {qixinbao_system.name}'))
        elif update:
            # 更新系统信息
            qixinbao_system.name = '启信宝'
            qixinbao_system.description = '启信宝企业信息查询平台，提供企业工商信息、法律风险、被执行记录等查询服务'
            qixinbao_system.base_url = base_url
            qixinbao_system.status = 'active'
            qixinbao_system.is_active = True
            qixinbao_system.save()
            self.stdout.write(self.style.SUCCESS(f'✓ 已更新外部系统: {qixinbao_system.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 外部系统已存在: {qixinbao_system.name} (使用 --update 参数可更新)'))
        
        # 创建或更新API接口
        api_interfaces = [
            {
                'code': 'QIXINBAO-00001',
                'name': '企业模糊搜索 API (1.31)',
                'url': '/APIService/v2/search/advSearch',
                'method': 'GET',
                'auth_type': 'custom',
                'auth_config': {
                    'app_key': app_key if app_key else '请在后台配置QIXINBAO_APP_KEY',
                    'app_secret': app_secret if app_secret else '请在后台配置QIXINBAO_APP_SECRET',
                    'auth_version': '2.0',
                    'sign_method': 'md5',
                    'sign_rule': 'appkey + timestamp + secret_key 组成的32位md5加密的小写字符串',
                    'timestamp_format': '毫秒时间戳'
                },
                'request_headers': {
                    'Auth-Version': '2.0',
                    'appkey': '{app_key}',
                    'timestamp': '{timestamp}',
                    'sign': '{sign}'
                },
                'request_params': {
                    'keyword': '企业相关关键字，输入字数大于等于2个或以上',
                    'matchType': '匹配类型（可选），多个类型使用,分隔，如：ename,credit_no',
                    'region': '地区编码（可选）',
                    'skip': '跳过条目数（可选，默认0，单页返回10条数据）'
                },
                'response_schema': {
                    'status': '状态码（200表示成功）',
                    'message': '消息',
                    'data': {
                        'total': '总数',
                        'num': '当前返回数',
                        'items': [
                            {
                                'id': '企业编号',
                                'name': '企业名称',
                                'credit_no': '统一社会信用代码',
                                'reg_no': '注册号',
                                'oper_name': '法定代表人',
                                'start_date': '成立日期'
                            }
                        ]
                    }
                },
                'description': '企业模糊搜索API，用于根据关键字搜索企业信息。支持按企业名称、统一社会信用代码等搜索。',
                'timeout': 10,
                'retry_count': 1,
                'version': '1.31',
            },
            {
                'code': 'QIXINBAO-00002',
                'name': '工商照面 API (1.41)',
                'url': '/APIService/enterprise/getBasicInfo',
                'method': 'GET',
                'auth_type': 'custom',
                'auth_config': {
                    'app_key': app_key if app_key else '请在后台配置QIXINBAO_APP_KEY',
                    'app_secret': app_secret if app_secret else '请在后台配置QIXINBAO_APP_SECRET',
                    'auth_version': '2.0',
                    'sign_method': 'md5',
                    'sign_rule': 'appkey + timestamp + secret_key 组成的32位md5加密的小写字符串',
                    'timestamp_format': '毫秒时间戳'
                },
                'request_headers': {
                    'Auth-Version': '2.0',
                    'appkey': '{app_key}',
                    'timestamp': '{timestamp}',
                    'sign': '{sign}'
                },
                'request_params': {
                    'keyword': '企业全名/注册号/统一社会信用代码'
                },
                'response_schema': {
                    'id': '企业编号',
                    'name': '企业名称',
                    'creditNo': '统一社会信用代码',
                    'regNo': '注册号',
                    'operName': '法定代表人',
                    'startDate': '成立日期',
                    'registCapi': '注册资本',
                    'address': '地址',
                    'phone': '联系电话',
                    'email': '邮箱',
                    'status': '状态',
                    'scope': '经营范围',
                    'econKind': '企业类型'
                },
                'description': '获取企业工商照面信息，包括基本信息、注册资本、联系方式等。支持通过企业全名、注册号或统一社会信用代码查询。',
                'timeout': 10,
                'retry_count': 1,
                'version': '1.41',
            },
            {
                'code': 'QIXINBAO-00003',
                'name': '企业联系方式 API (1.51)',
                'url': '/APIService/enterprise/getContactInfo',
                'method': 'GET',
                'auth_type': 'custom',
                'auth_config': {
                    'app_key': app_key if app_key else '请在后台配置QIXINBAO_APP_KEY',
                    'app_secret': app_secret if app_secret else '请在后台配置QIXINBAO_APP_SECRET',
                    'auth_version': '2.0',
                    'sign_method': 'md5',
                    'sign_rule': 'appkey + timestamp + secret_key 组成的32位md5加密的小写字符串',
                    'timestamp_format': '毫秒时间戳'
                },
                'request_headers': {
                    'Auth-Version': '2.0',
                    'appkey': '{app_key}',
                    'timestamp': '{timestamp}',
                    'sign': '{sign}'
                },
                'request_params': {
                    'keyword': '企业全名/注册号/统一社会信用代码'
                },
                'response_schema': {
                    'telephone': '联系电话',
                    'email': '邮箱',
                    'address': '地址'
                },
                'description': '获取企业联系方式信息，包括联系电话、邮箱、地址等。',
                'timeout': 10,
                'retry_count': 1,
                'version': '1.51',
            },
            {
                'code': 'QIXINBAO-00004',
                'name': '整体诉讼 API (6.6)',
                'url': '/APIService/sumLawsuit/sumLawsuit',
                'method': 'GET',
                'auth_type': 'custom',
                'auth_config': {
                    'app_key': app_key if app_key else '请在后台配置QIXINBAO_APP_KEY',
                    'app_secret': app_secret if app_secret else '请在后台配置QIXINBAO_APP_SECRET',
                    'auth_version': '2.0',
                    'sign_method': 'md5',
                    'sign_rule': 'appkey + timestamp + secret_key 组成的32位md5加密的小写字符串',
                    'timestamp_format': '毫秒时间戳'
                },
                'request_headers': {
                    'Auth-Version': '2.0',
                    'appkey': '{app_key}',
                    'timestamp': '{timestamp}',
                    'sign': '{sign}'
                },
                'request_params': {
                    'name': '企业全名/统一社会信用代码'
                },
                'response_schema': {
                    'lian': '立案信息数量（司法案件数量）',
                    'zxgg': '执行公告信息数量（被执行人数量）',
                    'terminationCaseResult': '终本案件数量',
                    'consumerResult': '限制高消费数量'
                },
                'description': '获取企业法律风险信息汇总，包括司法案件数量、被执行人数量、终本案件数量、限制高消费数量等。',
                'timeout': 10,
                'retry_count': 1,
                'version': '6.6',
            },
            {
                'code': 'QIXINBAO-00005',
                'name': '被执行企业 API (17.5)',
                'url': '/APIService/execution/getExecutedpersonListByName',
                'method': 'GET',
                'auth_type': 'custom',
                'auth_config': {
                    'app_key': app_key if app_key else '请在后台配置QIXINBAO_APP_KEY',
                    'app_secret': app_secret if app_secret else '请在后台配置QIXINBAO_APP_SECRET',
                    'auth_version': '2.0',
                    'sign_method': 'md5',
                    'sign_rule': 'appkey + timestamp + secret_key 组成的32位md5加密的小写字符串',
                    'timestamp_format': '毫秒时间戳'
                },
                'request_headers': {
                    'Auth-Version': '2.0',
                    'appkey': '{app_key}',
                    'timestamp': '{timestamp}',
                    'sign': '{sign}'
                },
                'request_params': {
                    'name': '企业全名/统一社会信用代码'
                },
                'response_schema': {
                    'list': [
                        {
                            'caseNumber': '案号',
                            'filingDate': '立案日期',
                            'executionCourt': '执行法院',
                            'amount': '执行金额',
                            'status': '执行状态'
                        }
                    ]
                },
                'description': '获取企业被执行详细记录列表，包括案号、立案日期、执行法院、执行金额、执行状态等信息。',
                'timeout': 10,
                'retry_count': 1,
                'version': '17.5',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for api_data in api_interfaces:
            api_interface, created = ApiInterface.objects.get_or_create(
                code=api_data['code'],
                defaults={
                    'name': api_data['name'],
                    'external_system': qixinbao_system,
                    'url': api_data['url'],
                    'method': api_data['method'],
                    'auth_type': api_data['auth_type'],
                    'auth_config': api_data['auth_config'],
                    'request_headers': api_data['request_headers'],
                    'request_params': api_data['request_params'],
                    'response_schema': api_data['response_schema'],
                    'description': api_data['description'],
                    'timeout': api_data['timeout'],
                    'retry_count': api_data['retry_count'],
                    'version': api_data['version'],
                    'status': 'active',
                    'is_active': True,
                    'created_by': creator,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已创建API接口: {api_interface.name}'))
            elif update:
                # 更新API接口信息
                api_interface.name = api_data['name']
                api_interface.url = api_data['url']
                api_interface.method = api_data['method']
                api_interface.auth_type = api_data['auth_type']
                api_interface.auth_config = api_data['auth_config']
                api_interface.request_headers = api_data['request_headers']
                api_interface.request_params = api_data['request_params']
                api_interface.response_schema = api_data['response_schema']
                api_interface.description = api_data['description']
                api_interface.timeout = api_data['timeout']
                api_interface.retry_count = api_data['retry_count']
                api_interface.version = api_data['version']
                api_interface.status = 'active'
                api_interface.is_active = True
                api_interface.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已更新API接口: {api_interface.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ API接口已存在: {api_interface.name}'))
        
        # 总结
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('初始化完成！'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'外部系统: {qixinbao_system.name} (编码: {qixinbao_system.code})')
        self.stdout.write(f'API接口: 创建 {created_count} 个, 更新 {updated_count} 个')
        self.stdout.write('')
        self.stdout.write('下一步操作:')
        self.stdout.write('1. 访问后台管理: /admin/api_management/externalsystem/')
        self.stdout.write('2. 编辑启信宝系统，确认基础URL配置')
        self.stdout.write('3. 编辑各个API接口，确认认证配置中的app_key和app_secret')
        if not app_key or not app_secret:
            self.stdout.write(self.style.WARNING('⚠ 注意: 环境变量中未配置QIXINBAO_APP_KEY或QIXINBAO_APP_SECRET，请在后台手动配置'))
        self.stdout.write('')
        self.stdout.write('已添加的API接口:')
        for api_data in api_interfaces:
            self.stdout.write(f'  - {api_data["name"]} ({api_data["code"]})')

