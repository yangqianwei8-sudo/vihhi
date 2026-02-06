# 产值管理模块 V1 —— 执行方案（冻结版）

> 本文档用于 **指导工程实现**
> 不讨论理念、不允许扩展、不接受“更合理”的修改
> 所有实现必须严格遵循本文定义

---

## 核心原则（必须遵守）

1. **产值管理模块是判断系统，不是记录系统**
2. **V1 只判断“是否还可能完成目标”**
3. **事件不直接产生产值，只用于：**
   * 里程碑完成判定
   * 全局事件修正因子（event_modifier）
4. **所有公式、权重、边界均已冻结**

---

## 零、可变口径由配置中心管理（必须遵守）

**所有可变口径由 `OutputValuePolicy`（产值口径配置）统一管理，计算内核不读代码常量。**

- **权威数据源**：`output_value_management.OutputValuePolicy` 表中 **唯一一条 `enabled=True`** 的记录。
- **包含项**：服务类型权重（JSON）、阶段权重、event_modifier 上下限、confidence 高阈值等；修改后**立即生效**。
- **运营入口**：Django Admin → 产值管理 → 产值口径配置；或执行 `python manage.py seed_output_value_policy` 创建默认 policy。
- **未配置时**：计算内核会明确抛错并提示在 Admin 配置或执行 seed 命令，禁止静默错误。

---

## 一、V1 总体计算公式（唯一合法版本）

```text
动态产值
= 商机金额
× 服务类型权重
× 阶段权重
× 里程碑权重
× 事件修正系数
```

明确禁止：

* ❌ 事件直接参与产值计算
* ❌ 多里程碑叠加
* ❌ 事件权重 × 金额
* ❌ 岗位分摊产值

---

## 二、服务类型权重（含防歧义说明）

服务类型权重（service_type_weight）为绝对折算率，不做归一化。

| 服务类型 | 权重   |
|---------|------|
| 转化阶段 | 0.02 |
| 合同阶段 | 0.02 |
| 生产阶段 | 0.10 |
| 结算阶段 | 0.05 |
| 回款阶段 | 0.06 |
| 售后阶段 | 0.02 |

注意：
- 「服务类型」不是流程阶段
- 同一个商机在任一时刻：
  - 只有一个 current_stage
  - 但 service_type 是该商机的“产值折算类别”
- service_type 在商机创建时确定，V1 中不随阶段变化

---

## 三、阶段权重（冻结）

V1 中阶段权重恒为常量：

```text
stage_weight = 1.0
```

阶段仅用于限定当前可用的里程碑集合。

---

## 四、里程碑权重计算规则（冻结）

```text
里程碑权重
= 当前阶段内
  所有【已完成里程碑】的最大权重
```

约束（必须遵守）：

* 不累计
* 不平均
* 不跨阶段
* 不允许人工修正

说明：
- milestone_weight = 0 表示「尚未产生任何可确认产值」
- 属于正常状态，不视为异常

---

## 五、事件 → 里程碑 判定规则（关键）

事件不参与产值计算。

事件的唯一职责：
- 判定某个里程碑是否完成

完成判定算法（原样）：

```pseudo
milestone_completed = (
  Σ completed_event_weights >= 100%
)
```

必须明确：
- 事件权重（completion_weight）仅用于完成度判断
- 禁止用于任何金额计算

---

## 六、事件修正系数（event_modifier）

```text
事件修正系数
= 1 + Σ(delta)
限制区间：[0.2, 1.2]
```

event_deltas 说明：
- 来源：系统级事件（如风险、冻结、加速）
- 与里程碑事件无关
- 默认值为空数组（event_modifier = 1）

---

## 七、核心计算伪代码（唯一版本）

```pseudo
function calculate_dynamic_output(opportunity):
    base = opportunity.amount

    service_weight = opportunity.service_type.weight

    stage = opportunity.current_stage
    stage_weight = 1.0

    milestones = get_milestones(stage)
    completed = filter_completed(milestones)

    if completed is empty:
        milestone_weight = 0
    else:
        milestone_weight = max(completed.weights)

    event_modifier = clamp(
        1 + sum(opportunity.event_deltas),
        0.2,
        1.2
    )

    return base
           * service_weight
           * stage_weight
           * milestone_weight
           * event_modifier
```

---

## 八、接口定义（含 confidence 规则）

### 1. 查询当前动态产值

```http
GET /api/output/v1/opportunity/{id}
```

返回示例：

```json
{
  "dynamic_output": 32000,
  "milestone": "咨询意见提交",
  "stage": "生产阶段",
  "confidence": "low | medium | high"
}
```

confidence 判定规则（V1）：
- high   ：milestone_weight ≥ 0.30
- medium ：0 < milestone_weight < 0.30
- low    ：milestone_weight = 0

### 2. 查询目标缺口

```http
GET /api/output/v1/target-gap?user_id=xxx&month=2026-02
```

### 3. 查询唯一行动结论

```http
GET /api/output/v1/action-decision?opportunity_id=xxx
```

```json
{
  "action_code": "SUBMIT_CONSULT_OPINION",
  "reason": "当前产值不足，最近的高权重里程碑未完成"
}
```

---

## 九、明确不做（必须遵守）

* ❌ 岗位产值分摊
* ❌ 事件级产值
* ❌ 计划联动
* ❌ 激励、绩效、评分
* ❌ UI 美化
* ❌ 作为绩效、提成的直接依据

---

## 十、执行要求（死命令）

> **Cursor 实现时：**
>
> * 不得新增字段语义
> * 不得修改公式
> * 不得引入“更合理”的算法
> * 所有计算逻辑必须可追溯到本文档条款

---

## 十一、V1 口径补丁：产值依据只来自计划管理

（本补丁为硬约束；与第五章「事件 → 里程碑判定」并存时，完成度来源以本补丁为准。）

1. **产值计算唯一依据**  
   产值计算只读取**计划管理模块**的完成状态，不得读取业务模块表或产值记录表作为完成度依据。  
   - 读取对象：计划管理中的「产值里程碑完成记录」（如 `PlanOutputMilestoneCompletion` 或等价表），按「商机 + 产值里程碑」维度存储是否已完成、完成时间、证据快照。  
   - 可选补充：计划管理中的 `Plan` / `PlanProgress` / `PlanDecision` 等仅当用于驱动上述「产值里程碑完成状态」时，可间接影响产值；产值模块本身不直接读这些表做公式或权重计算。

2. **业务模块仅提供证据**  
   - 业务模块只允许产生「事实/证据事件」（如写入 `FactEvent` 或等价表），用于计划管理侧判定「某产值里程碑是否可被标记为完成」。  
   - 业务模块禁止：写产值、写计划完成状态、提供直接参与产值公式或权重的字段/接口。

3. **禁止项（硬约束）**  
   - 禁止任何业务模块字段/接口直接参与产值公式或权重计算。  
   - 禁止产值模块直接读取业务模块记录来判定完成度；完成度只读计划管理的完成状态。

4. **数据流简述**  
   - 业务模块 → 写 `FactEvent`（type、ref_model/ref_id、occurred_at、payload、source_app）。  
   - 计划管理 → 根据 `MilestoneEvidenceRule` 与 `FactEvent` 评估，满足则更新「产值里程碑完成状态」（并记录 completed_at、evidence_snapshot）。  
   - 产值模块 → 仅根据「产值里程碑完成状态」计算里程碑权重与产值，不读 `OutputValueRecord`、不读业务表。
