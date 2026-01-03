# -*- coding: utf-8 -*-
"""
初始化快递100 API信息到后台API管理
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from backend.apps.api_management.models import ExternalSystem, ApiInterface

User = get_user_model()


class Command(BaseCommand):
    help = '初始化快递100 API信息到后台API管理'

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
        
        # 从settings获取API配置
        customer = getattr(settings, 'KUAIDI100_CUSTOMER', '4E35F2EFE1EC0764032ED487AA4DC538')
        key = getattr(settings, 'KUAIDI100_KEY', 'MaOnMTzX7201')
        secret = getattr(settings, 'KUAIDI100_SECRET', '676d530653cb4505add04d911b826c53')
        userid = getattr(settings, 'KUAIDI100_USERID', '56f5f07adbb746a28c76a25369907197')
        base_url = 'https://poll.kuaidi100.com'
        
        # 检查是否已存在快递100系统
        kuaidi100_system, created = ExternalSystem.objects.get_or_create(
            code='KUAIDI100',
            defaults={
                'name': '快递100',
                'description': '快递100物流查询平台，提供实时快递查询、物流跟踪、订阅推送等服务。企业：四川维海科技有限公司',
                'base_url': base_url,
                'contact_person': '快递100客服',
                'contact_email': 'support@kuaidi100.com',
                'status': 'active',
                'is_active': True,
                'created_by': creator,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 已创建外部系统: {kuaidi100_system.name}'))
        elif update:
            # 更新系统信息
            kuaidi100_system.name = '快递100'
            kuaidi100_system.description = '快递100物流查询平台，提供实时快递查询、物流跟踪、订阅推送等服务。企业：四川维海科技有限公司'
            kuaidi100_system.base_url = base_url
            kuaidi100_system.status = 'active'
            kuaidi100_system.is_active = True
            kuaidi100_system.save()
            self.stdout.write(self.style.SUCCESS(f'✓ 已更新外部系统: {kuaidi100_system.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 外部系统已存在: {kuaidi100_system.name} (使用 --update 参数可更新)'))
        
        # 创建或更新API接口
        api_interfaces = [
            {
                'code': 'KUAIDI100-00001',
                'name': '实时快递查询 API',
                'url': 'https://poll.kuaidi100.com/poll/query.do',
                'method': 'POST',
                'auth_type': 'custom',
                'auth_config': {
                    'customer': customer if customer else '请在后台配置KUAIDI100_CUSTOMER',
                    'key': key if key else '请在后台配置KUAIDI100_KEY',
                    'secret': secret if secret else '请在后台配置KUAIDI100_SECRET',
                    'userid': userid if userid else '请在后台配置KUAIDI100_USERID',
                    'auth_method': 'sign',
                    'sign_method': 'md5',
                    'sign_rule': 'param(JSON字符串) + key + customer，然后MD5加密转大写',
                    'param_format': 'JSON字符串，使用separators=(",", ":")确保无空格',
                },
                'request_headers': {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                'request_params': {
                    'customer': '{customer}',
                    'sign': '{sign}',
                    'param': '{param_json}',
                },
                'request_body_schema': {
                    'param': {
                        'com': '快递公司代码（必填），如：shunfeng, yuantong, zhongtong等',
                        'num': '快递单号（必填）',
                    },
                    '说明': 'param需要JSON序列化后作为form-data的param字段传递',
                },
                'response_schema': {
                    'status': '状态码（200表示成功）',
                    'message': '消息',
                    'state': '物流状态（0-在途，1-揽收，2-疑难，3-已签收，4-退签，5-派件，6-退回，7-转投，10-待清关，11-清关中，12-已清关，13-清关异常，14-收件人拒签）',
                    'data': [
                        {
                            'time': '时间',
                            'ftime': '格式化时间',
                            'context': '物流详情',
                            'location': '当前位置',
                        }
                    ],
                    'ischeck': '是否已签收（0-未签收，1-已签收）',
                    'condition': '快递单当前状态',
                    'nu': '快递单号',
                    'com': '快递公司代码',
                },
                'description': '实时快递查询API，用于查询快递物流信息。支持所有主流快递公司，包括顺丰、圆通、申通、中通、韵达、EMS、德邦、京东、极兔等。需要提供快递公司代码和快递单号。',
                'timeout': 10,
                'retry_count': 1,
                'version': '1.0',
            },
            {
                'code': 'KUAIDI100-00002',
                'name': '智能判断快递公司 API',
                'url': 'https://www.kuaidi100.com/autonumber/auto',
                'method': 'GET',
                'auth_type': 'api_key',
                'auth_config': {
                    'key': key if key else '请在后台配置KUAIDI100_KEY',
                    'key_location': 'query',
                    'key_param_name': 'key',
                },
                'request_headers': {},
                'request_params': {
                    'key': '{key}',
                    'num': '快递单号（必填）',
                },
                'response_schema': {
                    'auto': [
                        {
                            'comCode': '快递公司代码',
                            'lengthPre': '单号长度前N位',
                            'noCount': '单号匹配数',
                            'noPre': '单号前缀',
                        }
                    ],
                },
                'description': '智能判断快递公司API，根据快递单号自动识别快递公司。返回可能的快递公司列表，按匹配度排序。',
                'timeout': 10,
                'retry_count': 1,
                'version': '1.0',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for api_data in api_interfaces:
            api_interface, created = ApiInterface.objects.get_or_create(
                code=api_data['code'],
                defaults={
                    'name': api_data['name'],
                    'external_system': kuaidi100_system,
                    'url': api_data['url'],
                    'method': api_data['method'],
                    'auth_type': api_data['auth_type'],
                    'auth_config': api_data['auth_config'],
                    'request_headers': api_data['request_headers'],
                    'request_params': api_data['request_params'],
                    'request_body_schema': api_data.get('request_body_schema', {}),
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
                api_interface.request_body_schema = api_data.get('request_body_schema', {})
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
        self.stdout.write(f'外部系统: {kuaidi100_system.name} (编码: {kuaidi100_system.code})')
        self.stdout.write(f'API接口: 创建 {created_count} 个, 更新 {updated_count} 个')
        self.stdout.write('')
        self.stdout.write('下一步操作:')
        self.stdout.write('1. 访问后台管理: /admin/api_management/externalsystem/')
        self.stdout.write('2. 编辑快递100系统，确认基础URL配置')
        self.stdout.write('3. 编辑各个API接口，确认认证配置中的customer和key')
        if not customer or not key:
            self.stdout.write(self.style.WARNING('⚠ 注意: settings中未配置KUAIDI100_CUSTOMER或KUAIDI100_KEY，请在后台手动配置'))
        self.stdout.write('')
        self.stdout.write('已添加的API接口:')
        for api_data in api_interfaces:
            self.stdout.write(f'  - {api_data["name"]} ({api_data["code"]})')

