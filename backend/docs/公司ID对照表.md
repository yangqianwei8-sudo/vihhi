# 公司ID对照表

## 用途
用于数据回填和员工/部门分配子公司时的参考。

## 生成时间
2024年（基于现有 OurCompany 数据）

---

## 公司列表

| company_id | company_name | credit_code | is_active | created_time | order |
|------------|--------------|-------------|-----------|--------------|-------|
| *（运行 `python manage.py dump_companies` 获取最新数据）* | | | | | |

---

## 使用说明

### 查看最新公司列表
```bash
python manage.py dump_companies
```

### 数据回填示例
```bash
# 使用集团公司（ID=1，假设）作为默认公司回填用户
python manage.py backfill_user_company --default-company=1

# 回填部门
python manage.py backfill_department_company --default-company=1

# 回填计划
python manage.py backfill_plan_company --default-company=1
```

### Admin 操作
在 Django Admin 中：
1. 进入 `系统管理 > 我方主体信息` 查看所有公司
2. 记录每个公司的 ID（用于回填和分配）
3. 在 `系统管理 > 用户` 中为员工分配所属公司
4. 在 `系统管理 > 部门` 中为部门分配所属公司

---

## 注意事项

- **集团公司**：通常用于历史数据回填兜底，创建时间较晚（2026-01-31）
- **子公司**：创建时间较早（2025-12-08），用于实际业务隔离
- 回填时优先使用**集团公司**作为默认值，后续再逐步调整到各子公司
