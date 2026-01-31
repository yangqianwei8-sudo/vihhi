# 一次性迁移与修复脚本归档

本目录存放历史一次性迁移/修复脚本，当前日常运行不再依赖。保留仅供追溯或极端恢复场景参考。

## 来源与用途

### customer_management
- `execute_migration.py` - 直接执行 SQL 迁移（原 customer_success）
- `run_migration.py` - 客户管理迁移
- `run_checklist_questions_migration.py` - 沟通清单问题迁移
- `run_add_checklist_fields_migration.py` - 清单字段迁移
- `run_visit_type_migration.py` - 拜访类型迁移
- `run_visit_four_step_migration.py` - 拜访四步迁移
- `verify_checklist_questions.py` - 清单问题校验

### delivery_customer
- `fix_migration_history.py` - 修复 delivery_customer 迁移历史

### customer_success 清理（已废弃应用）
- `fix_customer_success_references.py` - 修复引用
- `deprecate_customer_success.py` - 废弃脚本
- `cleanup_customer_success_final.py` - 最终清理
- `cleanup_customer_success_completely.py` - 彻底清理
- `check_customer_database.py` - 数据库检查

### 数据删除
- `delete_customer_data.py` / `delete_customer_data_sql.py` - 删除客户数据
- `delete_project_data_sql.py` - 删除项目数据

### 迁移工具
- `migration_optimizer.py` - 迁移优化
- `quick_fix_migrations.py` - 快速修复迁移
- `run_migration_standalone.py` - 独立运行迁移
