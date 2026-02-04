# P3 技术债 TD-05：shared 目录准入封口

## 1. 结论

`backend/apps/shared/` 与 `backend/templates/shared/` 为**公共基建**，必须保持“可复用、无业务语义、无跨域耦合”；**不得**沦为“兜底目录”或“冲突缓冲区”。

---

## 2. 准入规则（Allow）

1. **只允许** 通用 utils：日期格式化、字符串/枚举转换、简单校验函数等，无业务语义。
2. **只允许** 抽象基类与 mixin：供多个业务 app 复用的基础逻辑，不包含具体业务字段或状态机。
3. **只允许** 通用校验、通用异常、通用常量：如 HTTP 状态码、通用错误消息、通用正则。
4. **只允许** 通用装饰器：如日志、计时、权限装饰器的**抽象定义**（具体权限逻辑在业务 app）。
5. **只允许** templatetags 中与展示无关的通用输出：如 `vh_display` 类格式化标签，不依赖 customer/plan 等业务模型。
6. **只允许** `templates/shared/` 下的基模与可复用 partial：如 `list_page_base`、`detail_base`、`create_form_base`、`_partials/`，仅结构占位与 `data-*`。
7. **必须** 可复用：被 ≥2 个业务模块引用，或为全系统通用能力。
8. **必须** 无业务语义：不包含 customer、plan、production、approval 等具体领域概念。
9. **必须** 无跨域耦合：不依赖具体业务 app 的 models、services、urls。

---

## 3. 禁止规则（Forbid）

1. **禁止** 放置具体业务模型：如 `Customer`、`Plan`、`ApprovalInstance` 等，必须在对应业务 app 中。
2. **禁止** 放置某模块专用逻辑：customer/plan/production/settlement/workflow 等专属服务、视图、表单。
3. **禁止** 放置页面/模板/路由相关：shared 不定义业务路由；`templates/shared/` 仅基模与 partial，不得放业务页面。
4. **禁止** 放置审批/workflow 专属逻辑：审批节点、状态机、通知规则等属于 `workflow_engine` 或业务 app。
5. **禁止** 把“临时修复”或“待分类”代码丢进 shared：不得作为垃圾场或占位目录。
6. **禁止** shared 依赖业务 apps：依赖方向必须单向，shared 不得 `import` customer_management、plan_management 等。
7. **禁止** 在 shared 中引入不必要的数据库迁移耦合：shared 原则上无 models；若确有通用表，须经架构评审。
8. **禁止** 把 shared 当作跨团队冲突的缓冲区：不得为规避合并冲突而将本应属于业务 app 的代码放入 shared。
9. **禁止** 在 shared 中写业务级权限判断：如 `has_perm('customer.change_client')` 的分叉逻辑，属于 views/services。

---

## 4. 依赖方向（Dependencies）

- **允许**：业务 apps（customer_management、plan_management、production_management 等）依赖 `shared`。
- **禁止**：shared 反向依赖业务 apps。

**反例**：
- shared 中 `from backend.apps.customer_management.models import Client` → 违反单向依赖。
- shared 的 templatetag 中根据 `request.user` 调用 `customer_management.services.xxx()` → 违反单向依赖。

---

## 5. 违规处理（Enforcement）

- **新增违反准入**：拒绝合并；按宪法第 13 条“新增违规回退”精神执行。
- **回流**：若 shared 再度沦为兜底目录或垃圾场，按宪法第 14 条清算精神执行，必须立即清理。

---

## 6. 完成判定（用于销项）

- 仅新增该文档
- 文档含「只允许/禁止/不得/拒绝合并」等关键词
- `git diff --stat` 仅 1 个文件
