# 产值 V1 二次清除 — 路由差异清单

## 1. 清除前后路由对照

### 1.1 页面路由（前缀 `/output-value/`）

| 路径 | 清除前 | 清除后 | 说明 |
|------|--------|--------|------|
| `home/` | 产值管理首页（展示说明） | **保留** | 仅展示“已收敛/已废弃说明 + V1 API 指引”，不查旧记录 |
| `template/` | 模板管理页 | **410 Gone** | 视图改为 `output_value_410_gone` |
| `records/` | 记录列表 | **410 Gone** | 同上 |
| `records/export/` | 记录导出 | **410 Gone** | 同上 |
| `records/batch-confirm/` | 批量确认 | **410 Gone** | 同上 |
| `records/<id>/confirm/` | 单条确认 | **410 Gone** | 同上 |
| `project/<id>/` | 项目维度产值详情 | **410 Gone** | 同上 |
| `statistics/` | 统计报表 | **410 Gone** | 同上 |

### 1.2 API 路由（前缀 `/api/output/`）

| 路径 | 清除前 | 清除后 | 说明 |
|------|--------|--------|------|
| `v1/opportunity/<id>/` | GET 动态产值 | **保留** | 唯一权威 API，见冻结文档 |

### 1.3 其他应用中的产值相关路由

- **financial_management**：`urls_settlement.py` 中已无产值路径挂载（注释说明产值已收敛至 output_value_management 及 V1 API）。
- **settlement_management**：仅注释说明产值管理独立至 `/output-value/`，无产值路由定义。

## 2. 删除项（无路由删除，实现删除）

- 以下**视图实现**已从 `output_value_management/views_pages.py` 中删除，对应 URL 改为返回 410：
  - `output_value_template_manage`（原模板管理逻辑）
  - `output_value_record_list`（原记录列表逻辑）
  - `output_value_record_export` / `output_value_record_batch_confirm`
  - `output_value_record_confirm`（原单条确认逻辑）
  - `project_output_value_detail`（原项目产值详情逻辑）
  - `output_value_statistics`（原统计报表逻辑）

## 3. 保留项（白名单）

- **页面**：`GET /output-value/home/` → 产值管理首页（仅说明 + V1 指引）。
- **API**：`GET /api/output/v1/opportunity/<id>/` → 动态产值查询（唯一权威）。

## 4. 新增项

- 无新增路由。新增视图仅 `output_value_410_gone`（用于上述旧路径统一返回 410）。

## 5. 左侧菜单

- 产值模块左侧菜单仅保留一个入口：**产值管理首页**（`output_value_management_home`），其余（模板、记录、项目维度、统计）已从 `OUTPUT_VALUE_MENU_STRUCTURE` 移除。
