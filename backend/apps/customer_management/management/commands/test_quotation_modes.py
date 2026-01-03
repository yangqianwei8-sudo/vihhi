"""
测试7种报价模式的计算逻辑
"""
from django.core.management.base import BaseCommand
from backend.apps.customer_management.services.quotation_calculator import QuotationCalculator
from decimal import Decimal


class Command(BaseCommand):
    help = '测试7种报价模式的计算逻辑'

    def handle(self, *args, **options):
        calculator = QuotationCalculator()
        
        self.stdout.write(self.style.SUCCESS('\n=== 报价模式测试 ===\n'))
        
        # 测试1：纯费率模式
        self.stdout.write(self.style.WARNING('\n1. 纯费率模式测试'))
        result = calculator.calculate(
            mode='rate',
            saved_amount=1000000,  # 100万元
            mode_params={'rate': 0.20},  # 20%
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：100万元')
        self.stdout.write(f'   费率：20%')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        self.stdout.write(f'   计算步骤：')
        for step in result['calculation_steps']:
            self.stdout.write(f'     - {step}')
        
        # 测试2：基本费+费率模式
        self.stdout.write(self.style.WARNING('\n2. 基本费+费率模式测试'))
        result = calculator.calculate(
            mode='base_fee_rate',
            saved_amount=1000000,  # 100万元
            mode_params={'base_fee': 50000, 'rate': 0.15},  # 基本费5万，费率15%
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：100万元')
        self.stdout.write(f'   基本费：5万元，费率：15%')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试3：包干价模式
        self.stdout.write(self.style.WARNING('\n3. 包干价模式测试'))
        result = calculator.calculate(
            mode='fixed',
            saved_amount=1000000,  # 节省金额不影响
            mode_params={'fixed_amount': 200000},  # 固定20万
            cap_fee=None
        )
        self.stdout.write(f'   固定金额：20万元')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试4：分段累进模式
        self.stdout.write(self.style.WARNING('\n4. 分段累进模式测试'))
        result = calculator.calculate(
            mode='segmented',
            saved_amount=1500000,  # 150万元
            mode_params={
                'segments': [
                    {'min': 0, 'max': 1000000, 'rate': 0.20},  # 0-100万：20%
                    {'min': 1000000, 'max': None, 'rate': 0.15}  # 100万以上：15%
                ]
            },
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：150万元')
        self.stdout.write(f'   分段：0-100万(20%)，100万以上(15%)')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试5：最低节省+费率模式（低于门槛）
        self.stdout.write(self.style.WARNING('\n5. 最低节省+费率模式测试（低于门槛）'))
        result = calculator.calculate(
            mode='min_savings_rate',
            saved_amount=300000,  # 30万元
            mode_params={'min_threshold': 500000, 'rate': 0.20},  # 门槛50万，费率20%
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：30万元（低于门槛50万）')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试5b：最低节省+费率模式（超过门槛）
        self.stdout.write(self.style.WARNING('\n5b. 最低节省+费率模式测试（超过门槛）'))
        result = calculator.calculate(
            mode='min_savings_rate',
            saved_amount=800000,  # 80万元
            mode_params={'min_threshold': 500000, 'rate': 0.20},  # 门槛50万，费率20%
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：80万元（超过门槛50万）')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试6：绩效挂钩模式
        self.stdout.write(self.style.WARNING('\n6. 绩效挂钩模式测试'))
        result = calculator.calculate(
            mode='performance_linked',
            saved_amount=1000000,  # 节省金额不影响
            mode_params={
                'base_fee': 100000,  # 基础服务费10万
                'kpis': [
                    {'name': '质量指标', 'completion_rate': 0.8, 'weight': 0.5, 'target_bonus': 50000},
                    {'name': '进度指标', 'completion_rate': 0.9, 'weight': 0.5, 'target_bonus': 50000}
                ]
            },
            cap_fee=None
        )
        self.stdout.write(f'   基础服务费：10万元')
        self.stdout.write(f'   KPI数量：2个')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试7：混合计价模式
        self.stdout.write(self.style.WARNING('\n7. 混合计价模式测试'))
        result = calculator.calculate(
            mode='hybrid',
            saved_amount=1000000,  # 100万元
            mode_params={
                'components': [
                    {'mode': 'rate', 'params': {'rate': 0.15}, 'weight': 0.6},  # 纯费率，权重60%
                    {'mode': 'base_fee_rate', 'params': {'base_fee': 20000, 'rate': 0.10}, 'weight': 0.4}  # 基本费+费率，权重40%
                ]
            },
            cap_fee=None
        )
        self.stdout.write(f'   节省金额：100万元')
        self.stdout.write(f'   组件数量：2个')
        self.stdout.write(f'   服务费：{result["service_fee"]:.2f}万元')
        
        # 测试封顶费功能
        self.stdout.write(self.style.WARNING('\n=== 封顶费功能测试 ===\n'))
        
        # 测试封顶费：超过封顶费
        self.stdout.write(self.style.WARNING('\n封顶费测试（超过封顶费）'))
        result = calculator.calculate(
            mode='rate',
            saved_amount=2000000,  # 200万元
            mode_params={'rate': 0.20},  # 20%
            cap_fee=300000  # 封顶费30万元
        )
        self.stdout.write(f'   节省金额：200万元')
        self.stdout.write(f'   费率：20%，计算服务费：40万元')
        self.stdout.write(f'   封顶费：30万元')
        self.stdout.write(f'   最终服务费：{result["service_fee"]:.2f}万元')
        self.stdout.write(f'   是否应用封顶费：{"是" if result["is_capped"] else "否"}')
        
        # 测试封顶费：未超过封顶费
        self.stdout.write(self.style.WARNING('\n封顶费测试（未超过封顶费）'))
        result = calculator.calculate(
            mode='rate',
            saved_amount=1000000,  # 100万元
            mode_params={'rate': 0.20},  # 20%
            cap_fee=300000  # 封顶费30万元
        )
        self.stdout.write(f'   节省金额：100万元')
        self.stdout.write(f'   费率：20%，计算服务费：20万元')
        self.stdout.write(f'   封顶费：30万元')
        self.stdout.write(f'   最终服务费：{result["service_fee"]:.2f}万元')
        self.stdout.write(f'   是否应用封顶费：{"是" if result["is_capped"] else "否"}')
        
        self.stdout.write(self.style.SUCCESS('\n\n=== 所有测试完成 ===\n'))

