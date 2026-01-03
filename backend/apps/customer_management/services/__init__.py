"""
客户管理服务模块
"""
from .quotation_calculator import QuotationCalculator

# 导入原有的服务（从父目录的services.py）
# 注意：services.py在父目录（backend/apps/customer_management/services.py）
# 而当前文件在backend/apps/customer_management/services/__init__.py
# 所以需要使用..services来导入父目录的services模块
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
services_file = os.path.join(parent_dir, 'services.py')

if os.path.exists(services_file):
    # 动态导入父目录的services模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("customer_management_services", services_file)
    customer_management_services = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(customer_management_services)
    
    # 导出服务
    QixinbaoAPIService = customer_management_services.QixinbaoAPIService
    get_service = customer_management_services.get_service
    AmapAPIService = getattr(customer_management_services, 'AmapAPIService', None)
else:
    # 如果文件不存在，提供默认实现
    QixinbaoAPIService = None
    AmapAPIService = None
    def get_service():
        raise ImportError("Cannot import get_service: services.py not found")

__all__ = ['QuotationCalculator', 'QixinbaoAPIService', 'get_service', 'AmapAPIService']

