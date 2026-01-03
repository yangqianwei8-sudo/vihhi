# -*- coding: utf-8 -*-
"""
快速配置DeepSeek API Key
"""
from django.core.management.base import BaseCommand
from backend.apps.api_management.models import ExternalSystem, ApiInterface


class Command(BaseCommand):
    help = '快速配置DeepSeek API Key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            required=True,
            help='DeepSeek API Key (格式: sk-xxxxxxxxxxxxx)',
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        
        if not api_key.startswith('sk-'):
            self.stdout.write(self.style.WARNING('警告: API Key格式可能不正确（应以sk-开头）'))
            confirm = input('是否继续？(y/n): ')
            if confirm.lower() != 'y':
                return
        
        # 查找DeepSeek系统
        deepseek_system = ExternalSystem.objects.filter(code='DEEPSEEK').first()
        
        if not deepseek_system:
            self.stdout.write(self.style.ERROR('未找到DeepSeek外部系统'))
            self.stdout.write('正在初始化...')
            from django.core.management import call_command
            call_command('init_deepseek_api')
            deepseek_system = ExternalSystem.objects.filter(code='DEEPSEEK').first()
        
        if not deepseek_system:
            self.stdout.write(self.style.ERROR('初始化失败，请手动运行: python manage.py init_deepseek_api'))
            return
        
        # 更新所有API接口
        updated_count = 0
        apis = ApiInterface.objects.filter(external_system=deepseek_system, is_active=True)
        
        for api in apis:
            if api.auth_type == 'bearer_token':
                auth_config = api.auth_config.copy() if api.auth_config else {}
                auth_config['token'] = api_key
                api.auth_config = auth_config
                api.save(update_fields=['auth_config', 'updated_time'])
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 已更新: {api.name} ({api.code})'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'配置完成！已更新 {updated_count} 个API接口'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('现在可以正常使用合同识别功能了！')
