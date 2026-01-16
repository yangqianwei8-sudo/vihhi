# -*- coding: utf-8 -*-
"""
初始化DeepSeek API信息到后台API管理
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from backend.apps.api_management.models import ExternalSystem, ApiInterface

User = get_user_model()


class Command(BaseCommand):
    help = '初始化DeepSeek API信息到后台API管理'

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
        
        # 检查是否已存在DeepSeek系统
        deepseek_system, created = ExternalSystem.objects.get_or_create(
            code='DEEPSEEK',
            defaults={
                'name': 'DeepSeek',
                'description': 'DeepSeek AI平台，提供大语言模型API服务，用于合同识别、文本分析等功能',
                'base_url': getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com'),
                'status': 'active',
                'is_active': True,
                'created_by': creator,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 已创建外部系统: {deepseek_system.name}'))
        elif update:
            # 更新系统信息
            deepseek_system.name = 'DeepSeek'
            deepseek_system.description = 'DeepSeek AI平台，提供大语言模型API服务，用于合同识别、文本分析等功能'
            deepseek_system.base_url = getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com')
            deepseek_system.status = 'active'
            deepseek_system.is_active = True
            deepseek_system.save()
            self.stdout.write(self.style.SUCCESS(f'✓ 已更新外部系统: {deepseek_system.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 外部系统已存在: {deepseek_system.name} (使用 --update 参数可更新)'))
        
        # 从环境变量获取API Key（如果已配置）
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 创建或更新API接口
        api_interfaces = [
            {
                'code': 'DEEPSEEK-00001',
                'name': 'Chat Completion API',
                'url': '/v1/chat/completions',
                'method': 'POST',
                'auth_type': 'bearer_token',
                'auth_config': {
                    'token': api_key if api_key else '请在后台配置API Key',
                    'header_name': 'Authorization',
                    'header_format': 'Bearer {token}'
                },
                'request_headers': {
                    'Content-Type': 'application/json'
                },
                'request_body_schema': {
                    'model': model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a helpful assistant.'
                        },
                        {
                            'role': 'user',
                            'content': 'Hello!'
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000,
                    'stream': False
                },
                'response_schema': {
                    'id': 'string',
                    'object': 'chat.completion',
                    'created': 'integer',
                    'model': 'string',
                    'choices': [
                        {
                            'index': 'integer',
                            'message': {
                                'role': 'string',
                                'content': 'string'
                            },
                            'finish_reason': 'string'
                        }
                    ],
                    'usage': {
                        'prompt_tokens': 'integer',
                        'completion_tokens': 'integer',
                        'total_tokens': 'integer'
                    }
                },
                'description': 'DeepSeek Chat Completion API，用于文本对话和生成',
                'timeout': 60,
                'retry_count': 2,
                'version': '1.0',
            },
            {
                'code': 'DEEPSEEK-00002',
                'name': 'Vision API (合同识别)',
                'url': '/v1/chat/completions',
                'method': 'POST',
                'auth_type': 'bearer_token',
                'auth_config': {
                    'token': api_key if api_key else '请在后台配置API Key',
                    'header_name': 'Authorization',
                    'header_format': 'Bearer {token}'
                },
                'request_headers': {
                    'Content-Type': 'application/json'
                },
                'request_body_schema': {
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': '请识别这个合同文档并提取关键信息'
                                },
                                {
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': 'data:image/jpeg;base64,{base64_image}'
                                    }
                                }
                            ]
                        }
                    ],
                    'temperature': 0.1,
                    'max_tokens': 4000
                },
                'response_schema': {
                    'id': 'string',
                    'object': 'chat.completion',
                    'created': 'integer',
                    'model': 'string',
                    'choices': [
                        {
                            'index': 'integer',
                            'message': {
                                'role': 'assistant',
                                'content': 'string'
                            },
                            'finish_reason': 'string'
                        }
                    ],
                    'usage': {
                        'prompt_tokens': 'integer',
                        'completion_tokens': 'integer',
                        'total_tokens': 'integer'
                    }
                },
                'description': 'DeepSeek Vision API，用于识别合同文档、图片等，提取结构化信息',
                'timeout': 120,
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
                    'external_system': deepseek_system,
                    'url': api_data['url'],
                    'method': api_data['method'],
                    'auth_type': api_data['auth_type'],
                    'auth_config': api_data['auth_config'],
                    'request_headers': api_data['request_headers'],
                    'request_body_schema': api_data['request_body_schema'],
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
                api_interface.request_body_schema = api_data['request_body_schema']
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
        self.stdout.write(f'外部系统: {deepseek_system.name} (编码: {deepseek_system.code})')
        self.stdout.write(f'API接口: 创建 {created_count} 个, 更新 {updated_count} 个')
        self.stdout.write('')
        self.stdout.write('下一步操作:')
        self.stdout.write('1. 访问后台管理: /admin/api_management/externalsystem/')
        self.stdout.write('2. 编辑DeepSeek系统，配置API Key（在认证配置中）')
        self.stdout.write('3. 或直接编辑API接口，更新认证配置中的API Key')
        if not api_key:
            self.stdout.write(self.style.WARNING('⚠ 注意: 环境变量中未配置DEEPSEEK_API_KEY，请在后台手动配置'))
