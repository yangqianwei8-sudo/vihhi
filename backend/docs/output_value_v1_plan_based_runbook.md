# 产值 V1 计划依据 — 最小运行手册

本手册用于在**任意已迁移环境**复现：FactEvent → 评估 → 完成表写入 → API 产值变化；不依赖测试库。

---

## 前置条件

- 数据库已执行迁移（含 `output_value_management`、`plan_management`、`opportunity_management` 等；**含 `OutputValuePolicy` 表**）。
- 已存在**一条生效的产值口径配置**（见下方「口径配置」）；否则计算会抛错。
- 可执行 `python manage.py` 与 Django shell。

---

## 口径配置（必须先有生效 policy）

所有可变口径（服务类型权重、event_modifier 区间、confidence 阈值等）由 **产值口径配置** 管理，修改后立即生效。

**方式一：种子命令（推荐部署时执行一次）**

```bash
python manage.py seed_output_value_policy
```

预期：`已创建默认产值口径配置（enabled=True）` 或 `已有生效口径：V1 默认口径 (id=...)`。

**方式二：Django Admin**

1. 登录 Admin → **产值管理** → **产值口径配置**。
2. 新增或编辑一条记录，勾选「是否生效」；全系统仅允许一条生效。
3. 填写「服务类型权重」JSON（如 `{"转化阶段":"0.02","conversion":"0.02","生产阶段":"0.10",...}`）、阶段权重、event_modifier 上下限、confidence 高阈值等，保存。
4. 修改后**立即生效**，无需重启；可通过步骤五调用 API 或 shell 验证 `calculate_dynamic_output` 输出是否变化。

---

## 步骤一：创建/选择一个商机（Opportunity）

最小字段要求：`name`, `client`, `business_manager`, `created_by`, `status`, `estimated_amount`, `success_probability`, `is_active`, `approval_status`。

**Django shell 示例（复制整段执行）：**

```python
from decimal import Decimal
from django.contrib.auth import get_user_model
from backend.apps.customer_management.models import Client
from backend.apps.opportunity_management.models import BusinessOpportunity

User = get_user_model()
# 若已有用户/客户，可直接用现有 id
user = User.objects.filter(is_active=True).first()
client = Client.objects.filter(is_active=True).first()
if not user or not client:
    raise SystemExit('需要至少一个活跃用户和一个活跃客户')

opp, created = BusinessOpportunity.objects.get_or_create(
    name='V1联调商机',
    client=client,
    defaults={
        'business_manager': user,
        'created_by': user,
        'status': 'potential',
        'estimated_amount': Decimal('100'),
        'success_probability': 10,
        'is_active': True,
        'approval_status': 'pending',
    }
)
print('Opportunity id:', opp.id)
# 记下 opp.id，后续步骤用 X 代替
```

若已有商机，可直接在 shell 中查 `BusinessOpportunity.objects.first().id` 作为 X。

---

## 步骤二：运行种子数据命令

先确保产值口径已配置（见「口径配置」）；再运行阶段/里程碑/规则种子：

```bash
python manage.py seed_output_value_v1_plan_rules
```

预期输出类似：`Seed done: stages created=1 updated=0 | milestones created=2 updated=0 | rules created=1 updated=0`  
（再次执行应看到 updated 或 0，幂等。）

---

## 步骤三：通过白名单入口插入一条 FactEvent

FactEvent 必须经唯一入口写入（禁止直写 `FactEvent.objects.create`）。规则要求事件类型为 `CONSULT_OPINION_SUBMITTED`（白名单内）。将下面 `X` 换为步骤一得到的商机 id。

**Django shell：**

```python
from backend.apps.plan_management.services.fact_event import record_fact_event

X = 1   # 替换为实际商机 id
record_fact_event(
    type='CONSULT_OPINION_SUBMITTED',
    ref_model='opportunity',
    ref_id=str(X),
    source_app='runbook',
)
print('FactEvent created for opportunity_id=%s' % X)
```

---

## 步骤四：运行评估命令（指定商机与里程碑）

将 `X`、`Y` 换为商机 id 与里程碑编码。里程碑编码来自种子：`consult_opinion_submitted`（咨询意见提交）。

```bash
python manage.py evaluate_output_milestone_completion --opportunity-id X --milestone-code consult_opinion_submitted
```

预期输出类似：  
`opportunity_id=X milestone_code=consult_opinion_submitted | rule_matched=True event_counts={'CONSULT_OPINION_SUBMITTED': 1} would_write=True written=yes`  
`Wrote 1 PlanOutputMilestoneCompletion(s).`

**完成记录审计字段示例**（由评估服务写入，可追溯）：

```python
from backend.apps.plan_management.models import PlanOutputMilestoneCompletion

c = PlanOutputMilestoneCompletion.objects.filter(opportunity_id=X, milestone_code='consult_opinion_submitted').first()
if c:
    print('created_via:', c.created_via)       # 'rule_engine'
    print('rule_code:', c.rule_code)           # 命中规则编码
    print('rule_snapshot:', c.rule_snapshot)   # 规则快照
```

**可选：先 dry-run 看是否会写入，不落库：**

```bash
python manage.py evaluate_output_milestone_completion --opportunity-id X --milestone-code consult_opinion_submitted --dry-run
```

---

## 步骤五：调用 API 验证产值

使用已登录会话请求（或带认证头）。将 `X` 换为商机 id。

```bash
# 若本地且已登录（示例：curl 带 cookie 或 token）
curl -s -b cookies.txt "http://localhost:8000/api/output/v1/opportunity/X/"
```

或在 **Django shell** 中直接调用计算内核验证：

```python
from backend.apps.output_value_management.services.calculator_v1 import calculate_dynamic_output

X = 1   # 替换为实际商机 id
out = calculate_dynamic_output(X)
print('milestone_weight:', out['milestone_weight'])   # 应为 0.30
print('dynamic_output:', out['dynamic_output'])      # 应 > 0
print('milestone:', out['milestone'])                 # 应为 咨询意见提交
```

预期：`milestone_weight=0.30`，`dynamic_output > 0`，`milestone='咨询意见提交'`。

---

## 步骤六：证明“只认计划完成”

删除该商机的计划完成记录后，产值应回到 0。

**Django shell：**

```python
from backend.apps.plan_management.models import PlanOutputMilestoneCompletion
from backend.apps.output_value_management.services.calculator_v1 import calculate_dynamic_output

X = 1   # 替换为实际商机 id
deleted, _ = PlanOutputMilestoneCompletion.objects.filter(opportunity_id=X).delete()
print('Deleted %s PlanOutputMilestoneCompletion(s).' % deleted)

out = calculate_dynamic_output(X)
print('milestone_weight:', out['milestone_weight'])   # 应为 0
print('dynamic_output:', out['dynamic_output'])      # 应为 0
```

结论：仅当存在 `PlanOutputMilestoneCompletion` 时产值才非 0；**FactEvent 单独不改变产值**，只有计划管理写入完成表后产值才变化。

---

## 步骤七：门禁验证（命令级）

上线前必须执行门禁验证命令，确保“完成表仅评估服务可写、FactEvent 仅白名单入口可写、幂等有效”：

```bash
python manage.py verify_output_value_v1_gates
```

**预期输出**（全部为 `[PASS]`，退出码 0）：

```
[PASS] A. PlanOutputMilestoneCompletion 直写抛 PermissionError
[PASS] B. evaluate_milestone_completion 写入且审计字段齐全
[PASS] C1. FactEvent 直写 create 抛 PermissionError
[PASS] C2. record_fact_event 可写成功
[PASS] D. record_fact_event 非白名单 type 抛 ValueError
[PASS] E. record_fact_event 幂等（同 idempotency_key 同 id）
All gate checks passed.
```

若有任一项为 `[FAIL]` 或命令退出码非 0，则门禁失效，不得上线。

---

## 命令速查

| 命令 | 说明 |
|------|------|
| `python manage.py seed_output_value_policy` | **口径配置**：创建/启用默认产值口径（幂等），未配置时计算会报错 |
| `python manage.py verify_output_value_v1_gates` | **门禁验收**：验证完成表写入门禁、FactEvent 白名单与幂等，全绿通过方可上线 |
| `python manage.py seed_output_value_v1_plan_rules` | 创建/更新阶段、里程碑、证据规则（幂等） |
| `python manage.py evaluate_output_milestone_completion --opportunity-id X --milestone-code consult_opinion_submitted` | 评估指定商机+里程碑并写入完成表 |
| `python manage.py evaluate_output_milestone_completion --opportunity-id X --milestone-code consult_opinion_submitted --dry-run` | 仅打印将要写入的内容，不落库 |
| `python manage.py evaluate_output_milestone_completion --hours 24` | 批量评估最近 24 小时内有 FactEvent 的商机 |
