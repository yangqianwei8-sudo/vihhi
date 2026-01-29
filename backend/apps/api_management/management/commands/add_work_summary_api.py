# -*- coding: utf-8 -*-
"""
添加DeepSeek工作总结辅助语言API接口
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from backend.apps.api_management.models import ExternalSystem, ApiInterface

User = get_user_model()


class Command(BaseCommand):
    help = '添加DeepSeek工作总结辅助语言API接口到后台API管理'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果接口已存在，则更新信息',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='指定创建人用户ID（默认为第一个超级用户）',
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='DeepSeek API Key（如果不提供，将从环境变量或设置中读取）',
        )

    def handle(self, *args, **options):
        update = options.get('update', False)
        user_id = options.get('user_id')
        api_key_arg = options.get('api_key')
        
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
        
        # 查找DeepSeek系统
        deepseek_system = ExternalSystem.objects.filter(code='DEEPSEEK').first()
        
        if not deepseek_system:
            self.stdout.write(self.style.ERROR('未找到DeepSeek外部系统'))
            self.stdout.write('正在初始化DeepSeek系统...')
            from django.core.management import call_command
            call_command('init_deepseek_api')
            deepseek_system = ExternalSystem.objects.filter(code='DEEPSEEK').first()
        
        if not deepseek_system:
            self.stdout.write(self.style.ERROR('初始化失败，请手动运行: python manage.py init_deepseek_api'))
            return
        
        # 获取API Key（优先使用命令行参数，其次环境变量，最后使用默认值）
        if api_key_arg:
            api_key = api_key_arg
        else:
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
            # 如果环境变量中没有，使用用户提供的默认API Key
            if not api_key:
                api_key = 'sk-072ace86ec564f7eb125191413237643'
        
        model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 创建工作总结辅助语言API接口
        api_data = {
            'code': 'DEEPSEEK-00004',
            'name': '工作总结辅助语言',
            'url': '/v1/chat/completions',
            'method': 'POST',
            'auth_type': 'bearer_token',
            'auth_config': {
                'token': api_key,
                'header_name': 'Authorization',
                'header_format': 'Bearer {token}'
            },
            'request_headers': {
                'Content-Type': 'application/json'
            },
            'request_params': {},
            'request_body_schema': {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个专业的工作总结辅助助手，擅长帮助用户撰写、优化和完善工作总结。'
                    },
                    {
                        'role': 'user',
                        'content': '请帮我写一份工作总结'
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
                            'role': 'assistant',
                            'content': 'string - 生成的工作总结内容'
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
            'description': 'DeepSeek工作总结辅助语言API，用于帮助用户撰写、优化和完善工作总结。支持多种工作总结场景，包括周报、月报、年报等。',
            'timeout': 60,
            'retry_count': 2,
            'version': '1.0',
        }
        
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
                'request_params': api_data['request_params'],
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
            self.stdout.write(self.style.SUCCESS(f'✓ 已创建API接口: {api_interface.name} ({api_interface.code})'))
        elif update:
            # 更新API接口信息
            api_interface.name = api_data['name']
            api_interface.url = api_data['url']
            api_interface.method = api_data['method']
            api_interface.auth_type = api_data['auth_type']
            api_interface.auth_config = api_data['auth_config']
            api_interface.request_headers = api_data['request_headers']
            api_interface.request_params = api_data['request_params']
            api_interface.request_body_schema = api_data['request_body_schema']
            api_interface.response_schema = api_data['response_schema']
            api_interface.description = api_data['description']
            api_interface.timeout = api_data['timeout']
            api_interface.retry_count = api_data['retry_count']
            api_interface.version = api_data['version']
            api_interface.status = 'active'
            api_interface.is_active = True
            api_interface.save()
            self.stdout.write(self.style.SUCCESS(f'✓ 已更新API接口: {api_interface.name} ({api_interface.code})'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ API接口已存在: {api_interface.name} ({api_interface.code})'))
            # 即使已存在，也更新API Key
            if api_key and api_interface.auth_config.get('token') != api_key:
                api_interface.auth_config['token'] = api_key
                api_interface.save()
                self.stdout.write(self.style.SUCCESS(f'✓ 已更新API Key'))
        
        # 总结
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('添加完成！'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'API接口: {api_interface.name}')
        self.stdout.write(f'接口编码: {api_interface.code}')
        self.stdout.write(f'接口URL: {api_interface.url}')
        self.stdout.write(f'API Key: {api_key[:20]}...' if len(api_key) > 20 else f'API Key: {api_key}')
        self.stdout.write('')
        self.stdout.write('现在可以在后台管理中看到此接口了！')
        self.stdout.write('访问: /admin/api_management/apiinterface/')
