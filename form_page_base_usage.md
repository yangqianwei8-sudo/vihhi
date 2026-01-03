# form_page_base.html 使用情况统计

## 概述
`form_page_base.html` 是系统中用于表单创建/编辑页面的共享基础模板，当前继承自 `module_base.html`。

## 使用该模板的页面列表

### 1. 客户管理模块 (customer_management)

#### 1.1 合同表单 (contract_form.html)
- **模板路径**: `backend/templates/customer_management/contract_form.html`
- **视图函数**: 
  - `contract_create` - 创建合同
  - `contract_edit` - 编辑合同
  - `contract_finalize_create` - 创建合同定稿
- **URL路由**:
  - `/business/contracts/create/` - 创建合同
  - `/business/contracts/<id>/edit/` - 编辑合同
  - `/business/contracts/finalize/create/` - 创建合同定稿

#### 1.2 联系人表单 (contact_form.html)
- **模板路径**: `backend/templates/customer_management/contact_form.html`
- **视图函数**:
  - `contact_create` - 创建联系人
  - `contact_edit` - 编辑联系人
- **URL路由**:
  - `/business/contacts/create/` - 创建联系人
  - `/business/contacts/<id>/edit/` - 编辑联系人

### 2. 工作流引擎模块 (workflow_engine)

#### 2.1 流程表单 (workflow_form.html)
- **模板路径**: `backend/templates/workflow_engine/workflow_form.html`
- **视图函数**:
  - `workflow_create` - 创建流程
  - `workflow_edit` - 编辑流程
- **URL路由**:
  - `/workflow/workflows/create/` - 创建流程
  - `/workflow/workflows/<id>/edit/` - 编辑流程

#### 2.2 节点表单 (node_form.html)
- **模板路径**: `backend/templates/workflow_engine/node_form.html`
- **视图函数**:
  - `node_create` - 创建节点
  - `node_edit` - 编辑节点
- **URL路由**:
  - `/workflow/workflows/<id>/nodes/create/` - 创建节点
  - `/workflow/nodes/<id>/edit/` - 编辑节点

### 3. 交付客户模块 (delivery_customer)

#### 3.1 发文创建 (outgoing_document_create.html)
- **模板路径**: `backend/templates/delivery_customer/outgoing_document_create.html`
- **视图函数**: `outgoing_document_create`
- **URL路由**: 待确认（需查看 delivery_customer 的 urls 配置）

#### 3.2 收文创建 (incoming_document_create.html)
- **模板路径**: `backend/templates/delivery_customer/incoming_document_create.html`
- **视图函数**: `incoming_document_create`
- **URL路由**: 待确认（需查看 delivery_customer 的 urls 配置）

### 4. 结算中心模块 (settlement_center)

#### 4.1 项目结算表单 (project_settlement_form.html)
- **模板路径**: `backend/templates/settlement_center/project_settlement_form.html`
- **视图函数**:
  - `project_settlement_create` - 创建项目结算
  - `project_settlement_update` - 更新项目结算
- **URL路由**:
  - `/settlement/project-settlement/create/` - 创建项目结算
  - `/settlement/project-settlement/<id>/edit/` - 编辑项目结算

## 统计汇总

- **总计**: 7个模板文件
- **涉及模块**: 4个应用模块
  - customer_management (2个模板)
  - workflow_engine (2个模板)
  - delivery_customer (2个模板)
  - settlement_center (1个模板)
- **页面类型**: 全部为表单创建/编辑页面

## 模板继承链

```
base.html (L1)
  └─ module_base.html (L2)
      └─ form_page_base.html (L3)
          └─ 具体表单页面 (L4)
```

## 注意事项

1. 所有使用 `form_page_base.html` 的模板都需要：
   - 覆盖 `form_content` 块来定义表单字段
   - 可选覆盖 `form_page_title_text` 来设置页面标题
   - 可选覆盖 `cancel_url` 来设置取消按钮的URL
   - 可选覆盖 `form_page_extra_css` 和 `form_page_extra_js` 添加额外资源

2. 模板已经自动提供了：
   - 表单布局结构
   - CSRF token
   - 表单错误提示
   - 表单操作按钮（保存、取消、提交审批）

