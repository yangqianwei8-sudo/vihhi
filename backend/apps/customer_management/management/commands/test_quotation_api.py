"""
测试报价计算API接口（直接测试计算引擎，不依赖数据库）
"""
from django.core.management.base import BaseCommand
from backend.apps.customer_management.services.quotation_calculator import QuotationCalculator
import json


class Command(BaseCommand):
    help = '测试报价计算API接口（直接测试计算引擎）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== 报价计算引擎测试（模拟API调用）===\n'))
        
        calculator = QuotationCalculator()
        
        # 测试1：纯费率模式
        self.stdout.write(self.style.WARNING('\n1. 测试纯费率模式'))
        try:
            result = calculator.calculate(
                mode='rate',
                saved_amount=1000000,
                mode_params={'rate': 0.20},
                cap_fee=None
            )
            self.stdout.write(f'   ✓ 计算成功')
            self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
            self.stdout.write(f'   是否应用封顶费：{"是" if result.get("is_capped") else "否"}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ 计算失败：{str(e)}'))
        
        # 测试2：基本费+费率模式
        self.stdout.write(self.style.WARNING('\n2. 测试基本费+费率模式'))
        try:
            result = calculator.calculate(
                mode='base_fee_rate',
                saved_amount=1000000,
                mode_params={'base_fee': 50000, 'rate': 0.15},
                cap_fee=None
            )
            self.stdout.write(f'   ✓ 计算成功')
            self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ 计算失败：{str(e)}'))
        
        # 测试3：封顶费功能
        self.stdout.write(self.style.WARNING('\n3. 测试封顶费功能'))
        try:
            result = calculator.calculate(
                mode='rate',
                saved_amount=2000000,
                mode_params={'rate': 0.20},
                cap_fee=300000
            )
            self.stdout.write(f'   ✓ 计算成功')
            self.stdout.write(f'   计算服务费：{result.get("calculated_fee", result["service_fee"]):.2f}万元')
            self.stdout.write(f'   封顶费：{result.get("cap_fee", 0):.2f}万元')
            self.stdout.write(f'   最终服务费：{result["service_fee"]:.2f}万元')
            self.stdout.write(f'   是否应用封顶费：{"是" if result.get("is_capped") else "否"}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ 计算失败：{str(e)}'))
        
        # 测试4：错误处理
        self.stdout.write(self.style.WARNING('\n4. 测试错误处理（无效模式）'))
        try:
            result = calculator.calculate(
                mode='invalid_mode',  # 无效模式
                saved_amount=1000000,
                mode_params={},
                cap_fee=None
            )
            self.stdout.write(self.style.WARNING(f'   ⚠ 预期抛出异常，但计算成功'))
        except ValueError as e:
            self.stdout.write(f'   ✓ 错误处理正常')
            self.stdout.write(f'   错误信息：{str(e)}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠ 预期ValueError，实际：{type(e).__name__}'))
            self.stdout.write(f'   错误信息：{str(e)}')
        
        self.stdout.write(self.style.SUCCESS('\n\n=== API测试完成 ===\n'))

