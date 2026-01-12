# 列表页操作列统一实现迁移状态

## 已迁移的文件（✅）

1. ✅ **customer_list.html** - 客户列表
   - 视图函数：`customer_list` (views_pages.py:1151)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

2. ✅ **opportunity_list.html** - 商机列表
   - 视图函数：`opportunity_list` (views_pages.py:8773)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

3. ✅ **contact_list.html** - 联系人列表
   - 视图函数：`contact_list` (views_pages.py:2815)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

4. ✅ **incoming_document_list.html** - 收文列表
   - 视图函数：`incoming_document_list` (incoming_document_views.py:143)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

5. ✅ **express_company_list.html** - 快递公司列表
   - 视图函数：`express_company_list` (express_views.py:18)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

6. ✅ **opportunity_win_loss.html** - 赢单与输单列表
   - 视图函数：`opportunity_win_loss` (views_pages.py:10412)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（使用统一实现）

7. ✅ **business_expense_application_list.html** - 业务费申请列表
   - 视图函数：`business_expense_application_list` (views_pages.py:4181)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

8. ✅ **customer_relationship_upgrade.html** - 客户关系升级列表
   - 视图函数：`customer_relationship_upgrade` (views_pages.py:4017)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

9. ✅ **customer_relationship_collaboration.html** - 客户关系协作列表
   - 视图函数：`customer_relationship_collaboration` (views_pages.py:4386)
   - URL配置已添加（查看、编辑、删除）
   - 模板已更新（保留删除确认消息）

10. ✅ **customer_visit.html** - 客户拜访列表
    - 视图函数：`customer_visit` (views_pages.py:3923)
    - URL配置已添加（查看、编辑、删除）
    - 模板已更新（保留删除确认消息）

11. ✅ **opportunity_warehouse_list.html** - 入库列表
    - 视图函数：`opportunity_warehouse_list` (views_pages.py:9505)
    - URL配置已添加（查看、编辑、删除）
    - 模板已更新（保留删除确认消息）

12. ✅ **workflow_list.html** - 审批流程列表
    - 视图函数：`workflow_list` (views_pages.py:288)
    - URL配置已添加（查看、编辑、删除）
    - 模板已更新（保留删除确认消息）

## 需要保留覆盖的文件（⚠️ 特殊逻辑）

以下文件有特殊逻辑，需要保留 `list_page_table_actions_cell` 块的覆盖：

1. ⚠️ **outgoing_document_list.html** - 发文列表
   - 原因：有条件判断 `item.approval_instance_id`，根据是否有审批实例显示不同的查看链接
   - 建议：保留覆盖，但可以考虑在统一实现中支持条件URL

2. ⚠️ **customer_public_sea.html** - 客户公海列表
   - 原因：只有"认领"操作，不是标准的查看/编辑/删除
   - 建议：保留覆盖

## 待迁移的文件（📋）

以下文件需要迁移，但尚未处理：

1. 📋 **customer_relationship_list.html** - 客户关系列表（使用了 list_page_table_row_actions，需要检查）
2. 📋 **supplier_list.html** - 供应商列表
3. 📋 **inventory_check_list.html** - 库存盘点列表
4. 📋 **purchase_contract_list.html** - 采购合同列表
5. 📋 **inventory_adjust_list.html** - 库存调整列表
6. 📋 **supply_category_list.html** - 物资分类列表
7. 📋 **supply_purchase_list.html** - 物资采购列表
8. 📋 **supplies_list.html** - 物资列表
9. 📋 **affair_list.html** - 事务列表
10. 📋 **supply_request_list.html** - 物资申请列表
11. 📋 **outgoing_document_tracking_list.html** - 发文跟踪列表
12. 📋 **approval_list.html** - 审批列表（有特殊逻辑，可能需要保留覆盖）
13. 📋 **all_workflows.html** - 所有工作流列表（操作列在 row_content 中，需要检查）

## 特殊说明

- **opportunity_followup_list.html** - 已迁移，但操作列指向关联商机，不是跟进记录本身（这是预期的行为）

## 迁移步骤

对于每个待迁移的文件，需要执行以下步骤：

### 1. 在视图函数中添加URL配置

在视图函数的 `context.update()` 中添加：

```python
context.update({
    # ... 其他配置 ...
    'can_create': ...,
    'can_delete': ...,  # 如果还没有的话
    # 操作列URL配置（统一实现）
    'detail_url_name': 'app_name:detail_view_name',
    'edit_url_name': 'app_name:edit_view_name',
    'delete_url_name': 'app_name:delete_view_name',
})
```

### 2. 在模板中移除操作列代码

将模板中的 `{% block list_page_table_actions_cell %}` 块替换为：

```django
{% block delete_confirm_message %}确定要删除此记录吗？此操作不可恢复。{% endblock %}
```

如果需要自定义删除确认消息，可以覆盖 `delete_confirm_message` 块。

### 3. 特殊情况处理

- **只有查看和编辑，没有删除**：只传递 `detail_url_name` 和 `edit_url_name`，不传递 `delete_url_name`，并设置 `can_delete=False` 或不传递
- **只有查看**：只传递 `detail_url_name`，设置 `can_edit=False` 和 `can_delete=False`
- **特殊权限控制**：可以在模板中覆盖 `list_page_table_actions_cell` 块，使用统一实现但添加额外的权限检查

## 注意事项

1. **URL名称必须存在**：确保传递的URL名称在 `urls.py` 中已定义
2. **权限检查**：建议在视图函数中进行权限检查，而不是仅依赖模板变量
3. **向后兼容**：现有的子模板覆盖不会受到影响，可以逐步迁移
4. **特殊需求**：对于有特殊逻辑的页面（如条件判断），仍可在子模板中覆盖

## 迁移检查清单

- [ ] 视图函数中添加了URL配置
- [ ] 模板中移除了操作列代码
- [ ] 保留了删除确认消息（如果需要）
- [ ] 测试了查看、编辑、删除功能
- [ ] 测试了权限控制
- [ ] 检查了URL名称是否正确

