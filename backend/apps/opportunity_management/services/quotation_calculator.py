"""
报价计算引擎
支持7种报价模式的计算逻辑
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple


class QuotationCalculator:
    """报价计算引擎"""
    
    def calculate(
        self, 
        mode: str, 
        saved_amount: float, 
        mode_params: Dict[str, Any] = None, 
        cap_fee: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        计算服务费
        
        Args:
            mode: 报价模式（rate/base_fee_rate/fixed/segmented/min_savings_rate/performance_linked/hybrid）
            saved_amount: 节省金额（万元）
            mode_params: 模式参数（字典格式）
            cap_fee: 封顶费（万元，可选）
        
        Returns:
            包含 service_fee, calculation_steps, is_capped 的字典
        """
        mode_params = mode_params or {}
        saved_amount_decimal = Decimal(str(saved_amount))
        
        # 根据模式调用对应的计算方法
        if mode == 'rate':
            result = self._calculate_rate(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'base_fee_rate':
            result = self._calculate_base_fee_rate(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'fixed':
            result = self._calculate_fixed(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'segmented':
            result = self._calculate_segmented(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'min_savings_rate':
            result = self._calculate_min_savings_rate(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'performance_linked':
            result = self._calculate_performance_linked(saved_amount_decimal, mode_params, cap_fee)
        elif mode == 'hybrid':
            result = self._calculate_hybrid(saved_amount_decimal, mode_params, cap_fee)
        else:
            raise ValueError(f'不支持的报价模式: {mode}')
        
        return result
    
    def _calculate_rate(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式1：纯费率模式 - 服务费 = 节省金额 × 约定费率"""
        rate = Decimal(str(mode_params.get('rate', 0)))
        steps = [
            f"节省金额：{saved_amount:,.0f} 万元",
            f"费率：{rate * 100}%",
        ]
        
        calculated_fee = saved_amount * rate
        steps.append(f"计算服务费 = {saved_amount:,.0f} × {rate * 100}% = {calculated_fee:,.2f} 万元")
        
        # 应用封顶费
        service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(calculated_fee),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _calculate_base_fee_rate(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式2：基本费+费率模式 - 服务费 = 固定基本费 + (节省金额 × 约定费率)"""
        base_fee = Decimal(str(mode_params.get('base_fee', 0)))
        rate = Decimal(str(mode_params.get('rate', 0)))
        steps = [
            f"基本费：{base_fee:,.0f} 万元",
            f"节省金额：{saved_amount:,.0f} 万元",
            f"费率：{rate * 100}%",
        ]
        
        rate_part = saved_amount * rate
        calculated_fee = base_fee + rate_part
        steps.append(f"费率部分 = {saved_amount:,.0f} × {rate * 100}% = {rate_part:,.2f} 万元")
        steps.append(f"服务费 = {base_fee:,.0f} + {rate_part:,.2f} = {calculated_fee:,.2f} 万元")
        
        # 应用封顶费
        service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(calculated_fee),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _calculate_fixed(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式3：包干价模式 - 服务费 = 预先设定的固定金额"""
        fixed_amount = Decimal(str(mode_params.get('fixed_amount', 0)))
        steps = [
            f"包干价：{fixed_amount:,.0f} 万元",
        ]
        
        # 包干价模式下，封顶费通常不适用（因为已经是固定金额）
        # 但如果设置了封顶费，且固定金额超过封顶费，则按封顶费计算
        if cap_fee and fixed_amount > Decimal(str(cap_fee)):
            service_fee = Decimal(str(cap_fee))
            is_capped = True
            steps.append(f"封顶费：{cap_fee:,.0f} 万元")
            steps.append(f"由于 {fixed_amount:,.0f} > {cap_fee:,.0f}，应用封顶费")
            steps.append(f"最终服务费 = {service_fee:,.2f} 万元")
        else:
            service_fee = fixed_amount
            is_capped = False
            steps.append(f"最终服务费 = {service_fee:,.2f} 万元")
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(fixed_amount),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _calculate_segmented(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式4：分段累进模式 - 将节省金额划分为多个区间，每个区间适用不同的费率"""
        segments = mode_params.get('segments', [])
        if not segments:
            raise ValueError('分段累进模式需要配置 segments 参数')
        
        steps = [
            f"节省金额：{saved_amount:,.0f} 万元",
        ]
        
        calculated_fee = Decimal('0')
        remaining_amount = saved_amount
        
        for i, segment in enumerate(segments, 1):
            min_val = Decimal(str(segment.get('min', 0)))
            max_val = Decimal(str(segment.get('max'))) if segment.get('max') is not None else None
            rate = Decimal(str(segment.get('rate', 0)))
            
            if remaining_amount <= 0:
                break
            
            # 计算当前区间的金额
            if max_val is not None:
                segment_amount = min(remaining_amount, max_val - min_val)
            else:
                segment_amount = remaining_amount
            
            if segment_amount > 0:
                segment_fee = segment_amount * rate
                calculated_fee += segment_fee
                
                if max_val is not None:
                    steps.append(f"{min_val:,.0f}-{max_val:,.0f} 万元部分：费率 {rate * 100}% = {segment_fee:,.2f} 万元")
                else:
                    steps.append(f"{min_val:,.0f} 万元以上部分：费率 {rate * 100}% = {segment_fee:,.2f} 万元")
                
                remaining_amount -= segment_amount
        
        steps.append(f"服务费 = {calculated_fee:,.2f} 万元")
        
        # 应用封顶费
        service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(calculated_fee),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _calculate_min_savings_rate(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式5：最低节省+费率模式 - 设定一个最低节省金额门槛"""
        min_threshold = Decimal(str(mode_params.get('min_threshold', 0)))
        rate = Decimal(str(mode_params.get('rate', 0)))
        steps = [
            f"最低节省门槛：{min_threshold:,.0f} 万元",
            f"费率：{rate * 100}%",
            f"节省金额：{saved_amount:,.0f} 万元",
        ]
        
        if saved_amount < min_threshold:
            # 低于门槛，不收费
            calculated_fee = Decimal('0')
            steps.append(f"由于 {saved_amount:,.0f} < {min_threshold:,.0f}（低于门槛），服务费 = 0 万元")
            return {
                'service_fee': 0.0,
                'calculated_fee': 0.0,
                'cap_fee': cap_fee,
                'is_capped': False,
                'calculation_steps': steps
            }
        else:
            # 超过门槛，对全部节省金额按费率计费
            calculated_fee = saved_amount * rate
            steps.append(f"由于 {saved_amount:,.0f} ≥ {min_threshold:,.0f}（超过门槛），计算服务费")
            steps.append(f"计算服务费 = {saved_amount:,.0f} × {rate * 100}% = {calculated_fee:,.2f} 万元")
            
            # 应用封顶费
            service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
            
            return {
                'service_fee': float(service_fee),
                'calculated_fee': float(calculated_fee),
                'cap_fee': cap_fee,
                'is_capped': is_capped,
                'calculation_steps': steps
            }
    
    def _calculate_performance_linked(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式6：绩效挂钩模式 - 服务费 = 基础服务费 + 绩效奖金"""
        base_fee = Decimal(str(mode_params.get('base_fee', 0)))
        kpis = mode_params.get('kpis', [])
        
        steps = [
            f"基础服务费：{base_fee:,.0f} 万元",
        ]
        
        # 计算绩效奖金
        bonus = Decimal('0')
        if kpis:
            steps.append("绩效指标完成情况：")
            for kpi in kpis:
                kpi_name = kpi.get('name', '')
                completion_rate = Decimal(str(kpi.get('completion_rate', 0)))
                weight = Decimal(str(kpi.get('weight', 0)))
                target_bonus = Decimal(str(kpi.get('target_bonus', 0)))
                
                kpi_bonus = target_bonus * completion_rate * weight
                bonus += kpi_bonus
                
                steps.append(f"  - {kpi_name}：完成率 {completion_rate * 100}%，权重 {weight * 100}%，奖金 {kpi_bonus:,.2f} 万元")
        
        calculated_fee = base_fee + bonus
        steps.append(f"绩效奖金 = {bonus:,.2f} 万元")
        steps.append(f"服务费 = {base_fee:,.0f} + {bonus:,.2f} = {calculated_fee:,.2f} 万元")
        
        # 应用封顶费
        service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(calculated_fee),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _calculate_hybrid(
        self, 
        saved_amount: Decimal, 
        mode_params: Dict[str, Any], 
        cap_fee: Optional[float]
    ) -> Dict[str, Any]:
        """模式7：混合计价模式 - 组合使用多种计价方式"""
        components = mode_params.get('components', [])
        if not components:
            raise ValueError('混合计价模式需要配置 components 参数')
        
        steps = [
            f"节省金额：{saved_amount:,.0f} 万元",
            "混合计价模式计算：",
        ]
        
        calculated_fee = Decimal('0')
        
        for i, component in enumerate(components, 1):
            component_mode = component.get('mode')
            component_params = component.get('params', {})
            component_weight = Decimal(str(component.get('weight', 1.0)))
            
            # 递归调用对应模式的计算方法
            component_result = self.calculate(
                mode=component_mode,
                saved_amount=float(saved_amount),
                mode_params=component_params,
                cap_fee=None  # 混合模式下，封顶费在最后统一应用
            )
            
            component_fee = Decimal(str(component_result['service_fee'])) * component_weight
            calculated_fee += component_fee
            
            steps.append(f"  组件{i}（{self._get_mode_name(component_mode)}，权重 {component_weight * 100}%）：{component_fee:,.2f} 万元")
        
        steps.append(f"服务费 = {calculated_fee:,.2f} 万元")
        
        # 应用封顶费
        service_fee, is_capped = self._apply_cap_fee(calculated_fee, cap_fee, steps)
        
        return {
            'service_fee': float(service_fee),
            'calculated_fee': float(calculated_fee),
            'cap_fee': cap_fee,
            'is_capped': is_capped,
            'calculation_steps': steps
        }
    
    def _apply_cap_fee(
        self, 
        calculated_fee: Decimal, 
        cap_fee: Optional[float], 
        steps: List[str]
    ) -> Tuple[Decimal, bool]:
        """应用封顶费"""
        if cap_fee is None:
            steps.append("封顶费：未设置")
            return calculated_fee, False
        
        cap_fee_decimal = Decimal(str(cap_fee))
        steps.append(f"封顶费：{cap_fee:,.0f} 万元")
        
        if calculated_fee > cap_fee_decimal:
            service_fee = cap_fee_decimal
            is_capped = True
            steps.append(f"由于 {calculated_fee:,.2f} > {cap_fee:,.0f}，应用封顶费")
            steps.append(f"最终服务费 = {service_fee:,.2f} 万元")
        else:
            service_fee = calculated_fee
            is_capped = False
            steps.append(f"最终服务费 = {service_fee:,.2f} 万元")
        
        return service_fee, is_capped
    
    def _get_mode_name(self, mode: str) -> str:
        """获取模式名称"""
        mode_names = {
            'rate': '纯费率模式',
            'base_fee_rate': '基本费+费率模式',
            'fixed': '包干价模式',
            'segmented': '分段累进模式',
            'min_savings_rate': '最低节省+费率模式',
            'performance_linked': '绩效挂钩模式',
            'hybrid': '混合计价模式',
        }
        return mode_names.get(mode, mode)

