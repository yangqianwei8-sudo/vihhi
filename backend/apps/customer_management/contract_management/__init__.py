"""
合同管理模块（API 子模块 - 预留/废弃，当前未使用）

负责管理业务合同的完整生命周期，包括合同创建、审核、签署、执行、变更等全流程管理。

注意：
- 此模块为预留的 RESTful API 子模块，当前未在主 URL 配置中挂载，请勿误挂载。
- 合同管理已拆分为独立应用 backend.apps.contract_management，页面与模型以独立应用为准。
- 如需使用本 API，请在 backend/config/urls.py 中显式添加路由并注明用途。
"""

__version__ = '1.0.0'

