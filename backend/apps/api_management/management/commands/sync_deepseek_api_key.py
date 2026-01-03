# -*- coding: utf-8 -*-
"""
同步DeepSeek API Key到API管理系统
从环境变量或settings中读取API Key，并更新到API管理系统的认证配置中
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from backend.apps.api_management.models import ExternalSystem, ApiInterface


class Command(BaseCommand):
    help = '同步DeepSeek API Key到API管理系统'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='直接指定API Key（可选，如果不指定则从环境变量读取）',
        )

    def handle(self, *args, **options):
        # 获取API Key
        api_key = options.get('api_key')
        if not api_key:
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        
        if not api_key:
            self.stdout.write(self.style.ERROR('未找到DeepSeek API Key'))
            self.stdout.write('请通过以下方式之一配置:')
            self.stdout.write('1. 设置环境变量 DEEPSEEK_API_KEY')
            self.stdout.write('2. 在 .env 文件中配置 DEEPSEEK_API_KEY')
            self.stdout.write('3. 使用 --api-key 参数直接指定')
            return
        
        # 查找DeepSeek系统
        deepseek_system = ExternalSystem.objects.filter(code='DEEPSEEK').first()
        
        if not deepseek_system:
            self.stdout.write(self.style.ERROR('未找到DeepSeek外部系统'))
            self.stdout.write('请先运行: python manage.py init_deepseek_api')
            return
        
        self.stdout.write(f'找到DeepSeek系统: {deepseek_system.name}')
        
        # 更新所有DeepSeek API接口的认证配置
        updated_count = 0
        apis = ApiInterface.objects.filter(external_system=deepseek_system, is_active=True)
        
        for api in apis:
            if api.auth_type == 'bearer_token' and api.auth_config:
                auth_config = api.auth_config.copy()
                if 'token' in auth_config:
                    old_token = auth_config.get('token', '')
                    auth_config['token'] = api_key
                    api.auth_config = auth_config
                    api.save(update_fields=['auth_config', 'updated_time'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已更新: {api.name} ({api.code})'))
                    if old_token and old_token != '请在后台配置API Key':
                        self.stdout.write(f'    旧Key: {old_token[:20]}...')
                    self.stdout.write(f'    新Key: {api_key[:20]}...')
        
        if updated_count == 0:
            self.stdout.write(self.style.WARNING('未找到需要更新的API接口'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 50))
            self.stdout.write(self.style.SUCCESS(f'同步完成！已更新 {updated_count} 个API接口'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
