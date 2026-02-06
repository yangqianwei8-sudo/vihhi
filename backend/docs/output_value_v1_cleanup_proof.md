# 产值 V1 二次清除 — 残留入口零结果证明

## 1. 无路由/页面引用旧产值服务（output_value_management 原 services.py）

旧服务已封存为 `legacy_services.py`，不得被任何路由或页面引用。

**Grep 命令与结果：**

```bash
# 从 output_value_management 应用内引用“旧 services 模块”（非 calculator_v1）的导入
grep -r "from backend.apps.output_value_management.services import\|from \.services import" backend/apps/output_value_management --include="*.py"
# 预期：无匹配（仅 services/ 包存在，且无人从 .services 导入非 calculator_v1 的符号）
```

**实际结果：** 在 `output_value_management` 应用内，无 `from backend.apps.output_value_management.services import` 或 `from .services import`（指向旧单文件）的引用。  
唯一对 `output_value_management.services` 的引用为 **包** `services.calculator_v1`（`views_api_v1.py`、`test_calculator_v1.py`），属白名单权威实现。

---

```bash
# 全仓引用 legacy_services（封存文件不应被引用）
grep -rn "legacy_services\|from.*legacy_services import" backend/apps --include="*.py"
```

**实际结果：** 仅 `output_value_management/legacy_services.py` 自身存在；无其他文件 import `legacy_services`。

---

## 2. 无页面/接口通过读写“产值记录”展示产值

V1 只算不记；禁止页面或接口通过读写产值记录表来展示产值。

**说明：**  
- `output_value_management/views_pages.py` 中首页仅展示说明与 V1 API 指引，不查询 `OutputValueRecord`。  
- 旧模板/记录/统计/项目维度入口已删除实现，统一 410，不再读写产值记录。  
- 唯一计算与数据来源：`services/calculator_v1.py` + `GET /api/output/v1/opportunity/<id>/`。

**Grep 结果（仅作结构说明）：**  
- `OutputValueRecord.objects.(create|filter|get)` 仅出现在：  
  - `legacy_services.py`（已废弃，不对外暴露）；  
  - `services/calculator_v1.py`（仅用于完成度判定：是否已有记录视为已完成，不用于“展示产值”）；  
  - 测试 `test_calculator_v1.py`（构造测试数据）。  
- 无任何页面视图或 API 视图通过产值记录做列表/统计/详情展示。

---

## 3. 仍引用“旧逻辑”的其他应用（非 output_value_management）

- **financial_management**：使用本应用内 `services_settlement.py` 的 `get_project_output_value_*`，未引用 `output_value_management` 的旧服务。  
- **settlement_management**：已改为使用本地占位 `_output_value_placeholder_for_settlement`，不再调用 `output_value_management.services`。  
- **production_management**：已移除对 `calculate_output_value` 的调用及对 `output_value_management.services` 的依赖。

---

## 4. 自测结果（仅列结果）

| 检查项 | 结果 |
|--------|------|
| 旧路径 `/output-value/template/` | 410 |
| 旧路径 `/output-value/records/` | 410 |
| 旧路径 `/output-value/statistics/` | 410 |
| 旧路径 `/output-value/project/<id>/` | 410 |
| V1 API `GET /api/output/v1/opportunity/<id>/`（有效 id、已登录） | 200 |
| V1 API（不存在 id） | 404 |
| V1 API（未登录/无权限） | 401 |

---

## 5. 结论

- 除白名单（产值首页 + V1 API）外，旧产值入口均返回 410 或已无实现。  
- 无任何路由或页面引用 `output_value_management` 的旧服务（原 `services.py`，现 `legacy_services.py`）。  
- 文档 `output_value_v1_cleanup_diff.md` 与本文档齐全。
