# 产值管理模块清除与重构执行方案

**重要说明**：本方案与 `docs/output_value_v1_execution.md`（冻结版）一致。  
**原则**：产值管理 V1 为「判断系统」不是「记录系统」；动态产值由接口**实时计算**，V1 不新增「产值表」存储动态产值。

---

## 一、范围界定（必读）

### 1. 什么是「现有模块」

| 类型 | 说明 | 处理 |
|------|------|------|
| **V1 已实现（按冻结文档）** | 计算内核 `calculator_v1.py`、接口 `GET /api/output/v1/opportunity/{id}/`、单元测试与文档 | **保留**，不删除 |
| **共用表（非产值独有）** | `opportunity`（商机）、`project`（项目）等为全系统共用 | **不删除**，仅产值逻辑可调整 |
| **产值相关旧逻辑** | 旧版产值记录列表、模板管理、按事件/岗位分摊的旧计算、与 V1 公式冲突的代码 | **可清除或标记废弃** |
| **前端产值页面** | `output-value/` 下首页、模板、记录、统计等页面 | 按产品决定：保留只读展示或下线，由产品/业务定 |

### 2. 不可删除

- **商机表（Opportunity）**：`opportunity_management` 的 `BusinessOpportunity`，全系统共用，不能因产值模块删除。
- **项目表（Project）**：`production_management` 的 `Project`，全系统共用，不能因产值模块删除。
- **V1 接口**：`GET /api/output/v1/opportunity/{id}/` 为冻结文档规定接口，必须保留。
- **V1 计算内核**：`output_value_management.services.calculator_v1`，必须保留。
- **阶段/里程碑/事件表**：`OutputValueStage`、`OutputValueMilestone`、`OutputValueEvent`、`OutputValueRecord` 为 V1 判定「里程碑是否完成」所需（Record 表示事件已完成），删除会导致 V1 无法计算；若确需删表，需先做数据迁移与方案评审。

---

## 二、现有模块清除（分步执行）

### 步骤 1：梳理与产值相关的入口

- [ ] 列出所有产值相关路由（API + 页面）：
  - `config/urls.py`：`api/output/`、`output-value/`
  - `financial_management` 下是否有重复的 `output-value/` 路径
- [ ] 列出所有引用「产值计算」「产值记录」的视图、服务、表单。

### 步骤 2：只清除与 V1 冲突或已废弃的逻辑

- [ ] **后端**：删除或注释仅用于「旧版事件产值、岗位分摊」的代码路径（若有）；保留 `calculator_v1` 与 `GET /api/output/v1/opportunity/{id}/`。
- [ ] **重复路由**：若 `financial_management` 与 `output_value_management` 存在相同 path（如 `output-value/records/`），统一到一个入口，避免重复。
- [ ] **表单/字段**：若某表单中有「旧版产值计算字段」且已不再使用，可移除或标记只读；**不删除**商机金额、服务类型、阶段等 V1 依赖字段。

### 步骤 3：不删表、不删商机/项目

- [ ] **不执行**：删除 `opportunity` 表、`project` 表、`output_value_management` 下阶段/里程碑/事件/记录表。
- [ ] 若未来确需删表，单独做「数据迁移与下线方案」，并评审。

### 步骤 4：前端（按产品要求执行）

- [ ] 若产品决定下线旧产值页面：移除或重定向 `output-value/` 下不再使用的页面。
- [ ] 若保留：确保展示动态产值时调用 `GET /api/output/v1/opportunity/{id}/`，不依赖已清除的旧接口。

---

## 三、新模块结构（与冻结文档一致）

V1 **不新增**「产值表」；动态产值 = 接口按公式实时计算。

### 1. 数据与模型（沿用现有）

| 用途 | 来源 | 说明 |
|------|------|------|
| 商机金额、服务类型 | `BusinessOpportunity` + `ServiceType` | 已有 |
| 当前阶段、里程碑 | `OutputValueStage`、`OutputValueMilestone` | 已有 |
| 里程碑是否完成 | `OutputValueEvent` + `OutputValueRecord`（已存在记录即视为事件完成） | 已有 |
| 项目（用于关联 Record） | `Project` | 已有 |

### 2. 计算逻辑（已实现）

- 公式：`动态产值 = 商机金额 × 服务类型权重 × 1 × 里程碑权重 × 事件修正系数`
- 实现：`backend.apps.output_value_management.services.calculator_v1.calculate_dynamic_output(opportunity_id)`
- 文档：`docs/output_value_v1_execution.md` 第一至八章

### 3. API 接口（已实现）

| 接口 | 说明 | 状态 |
|------|------|------|
| `GET /api/output/v1/opportunity/{id}/` | 返回 dynamic_output、stage、milestone、milestone_weight、confidence | 已实现 |

### 4. 前端

- 需要展示动态产值、目标缺口、行动结论时：调用上述 API，不新增与冻结文档冲突的存储或计算。

---

## 四、开发与实现（当前状态）

| 项 | 状态 |
|----|------|
| 数据模型（沿用现有表） | 已满足 V1 |
| 核心计算逻辑（calculator_v1） | 已实现 |
| API 接口（v1/opportunity/{id}/） | 已实现 |
| 单元测试（计算 + API） | 已编写 |
| 接口文档与上线前检查 | 已编写 |

**结论**：在「只做 V1、按冻结文档」前提下，**无需从零重建**；只需按第二章做**清除与收敛**（去旧逻辑、去重复、前端对齐 V1 接口）。

---

## 五、部署与验证

1. **清除/收敛完成后**：在测试环境执行单元测试与接口联调。
2. **上线前**：按 `docs/output_value_v1_api.md` 第 4 节「上线前检查清单」逐项验证（200/404/401、网关放行）。
3. **上线**：部署到生产后再次执行检查清单，确认动态产值结果符合预期。

---

## 六、执行顺序与时间建议

| 阶段 | 内容 | 说明 |
|------|------|------|
| 1. 梳理 | 列出所有产值相关路由、视图、引用 | 避免误删共用表与 V1 代码 |
| 2. 清除 | 仅移除与 V1 冲突或已废弃的旧逻辑与重复路由 | 不删商机/项目/阶段里程碑事件记录表 |
| 3. 收敛 | 前端与产品对齐：展示产值处统一走 V1 API | 可选：下线不再使用的旧页面 |
| 4. 验证 | 跑单元测试 + 上线前检查清单 | 确认 200/404/401 与数值正确 |
| 5. 上线 | 部署到生产并复验 | 按上线确认文档执行 |

---

**若确需「从零重建」**（例如废弃现有 V1 实现、连 V1 API 一并删除后重写）：需先与产品/架构确认，并书面说明与冻结文档的对应关系，再单独制定「从零重建」方案，避免与当前冻结文档冲突。本方案**不建议**删除已按冻结文档实现的 V1 计算与 API。
