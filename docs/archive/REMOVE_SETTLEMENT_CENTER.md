# 完全移除结算中心（settlement_center）步骤说明

当前状态：**结算管理（settlement_management）** 已接管所有页面与 API 路由（`/settlement/`、`api/settlement/`），但 **结算中心（settlement_center）** 仍保留在 `INSTALLED_APPS` 中，供以下功能引用。

## 仍依赖 settlement_center 的模块

| 引用方 | 引用内容 | 说明 |
|--------|----------|------|
| **settlement_management/views_api.py** | models, serializers, services | 服务费结算方案 API（ServiceFeeSettlementScheme 等） |
| **contract_management/views_pages.py** | SettlementMethod | 合同相关表单中的结算方式选项 |
| **archive_management/signals.py** | ProjectSettlement | 档案与结算关联逻辑 |
| **archive_management/services.py** | ProjectSettlement | 档案服务中的结算引用 |
| **Django Admin** | settlement_center 下的模型 | 后台“结算管理”菜单指向 `/admin/settlement_center/` |

## 完全移除前需要完成的工作

1. **统一数据表**
   - 当前存在两套表：`settlement_*`（settlement_center 迁移创建）与 `settlement_management_*`（settlement_management 迁移创建）。
   - 需决定以哪套为准，并在 settlement_management 的模型中统一使用对应 `db_table`（或做一次性数据迁移后只保留一套表）。

2. **迁移模型到 settlement_management**
   - 将 settlement_center 中以下模型迁入 settlement_management，并保持 `db_table` 指向现有表（避免重复建表）：
     - ServiceFeeRate, SettlementItem, ProjectSettlement, ContractSettlement
     - ServiceFeeSettlementScheme, ServiceFeeSegmentedRate, ServiceFeeJumpPointRate, ServiceFeeUnitCapDetail
     - SettlementMethod
   - 注意：Django 不允许两个应用共用同一张表（同一 `db_table`），因此需先从 settlement_center 中移除这些模型的注册/迁移，再在 settlement_management 中通过 `db_table` 指向原表（或做迁移合并）。

3. **迁移 serializers 与 services**
   - 将 `settlement_center/serializers.py`、`settlement_center/services.py` 中与上述模型相关的逻辑迁入 settlement_management，并改为使用 `settlement_management.models`。

4. **更新所有引用**
   - `settlement_management/views_api.py`：改为使用本应用内的 models / serializers / services。
   - `contract_management`：改为 `from backend.apps.settlement_management.models import SettlementMethod`。
   - `archive_management`：改为 `from backend.apps.settlement_management.models import ProjectSettlement`。

5. **Admin 与配置**
   - 在 settlement_management 的 `admin.py` 中注册上述模型（或保留从 settlement_center 的 admin 迁移过来的注册）。
   - `admin_menu_config.py`：将“结算管理”菜单 URL 从 `/admin/settlement_center/` 改为 `/admin/settlement_management/`，并更新 `get_menu_path_for_model` 等逻辑中对 `settlement_center` 的判断。

6. **从 INSTALLED_APPS 移除**
   - 在 `config/settings.py` 中删除 `backend.apps.settlement_center.apps.SettlementCenterConfig`。
   - 如不再需要 settlement_center 的迁移历史，可保留其 migrations 目录供 Django 识别，或通过迁移合并/重写方式处理。

---

当前 **结算管理** 已作为唯一入口提供 `/settlement/` 与 `api/settlement/`，结算中心仅作为模型与后台数据维护的依赖存在。完成上述步骤后即可彻底移除结算中心。
