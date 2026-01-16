"""
清除Django缓存的管理命令
支持清除所有缓存或指定缓存
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache, caches
from django.conf import settings


class Command(BaseCommand):
    help = '清除Django缓存（支持清除所有缓存或指定缓存）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache',
            type=str,
            help='指定要清除的缓存名称（如：default），如果不指定则清除所有缓存',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='清除所有配置的缓存',
        )

    def handle(self, *args, **options):
        cache_name = options.get('cache')
        clear_all = options.get('all', False)

        # 显示当前缓存配置信息
        self.stdout.write(self.style.SUCCESS('当前缓存配置：'))
        cache_backend = settings.CACHES.get('default', {}).get('BACKEND', '')
        cache_location = settings.CACHES.get('default', {}).get('LOCATION', '')
        
        # 解析缓存类型
        if 'redis' in cache_backend.lower():
            cache_type = 'Redis'
            self.stdout.write(f'  类型：{cache_type}')
            self.stdout.write(f'  位置：{cache_location}')
        elif 'locmem' in cache_backend.lower():
            cache_type = '内存缓存（LocMem）'
            self.stdout.write(f'  类型：{cache_type}')
        else:
            cache_type = cache_backend
            self.stdout.write(f'  类型：{cache_type}')
        
        self.stdout.write('')

        try:
            if cache_name:
                # 清除指定的缓存
                self.stdout.write(self.style.WARNING(f'正在清除缓存：{cache_name}...'))
                try:
                    specific_cache = caches[cache_name]
                    specific_cache.clear()
                    self.stdout.write(self.style.SUCCESS(f'✓ 缓存 "{cache_name}" 已成功清除'))
                except KeyError:
                    self.stdout.write(self.style.ERROR(f'✗ 错误：未找到名为 "{cache_name}" 的缓存配置'))
                    return
            elif clear_all or len(settings.CACHES) > 1:
                # 清除所有缓存
                self.stdout.write(self.style.WARNING('正在清除所有缓存...'))
                cleared_count = 0
                for name in settings.CACHES:
                    try:
                        caches[name].clear()
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 已清除缓存：{name}'))
                        cleared_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠ 清除缓存 {name} 时出错：{e}'))
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'成功清除 {cleared_count} 个缓存配置'))
            else:
                # 默认清除 default 缓存
                self.stdout.write(self.style.WARNING('正在清除默认缓存...'))
                cache.clear()
                self.stdout.write(self.style.SUCCESS('✓ 默认缓存已成功清除'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ 清除缓存时发生错误：{e}'))
            return





