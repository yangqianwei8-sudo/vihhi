-- 创建部门数据的 SQL 脚本
-- 表名：system_department
-- 字段：id, name, code, parent_id, leader_id, description, order, is_active, created_time

-- 插入部门数据
-- 使用 INSERT ... ON CONFLICT 避免重复插入（如果 code 已存在则更新）

INSERT INTO system_department (name, code, description, "order", is_active, created_time)
VALUES 
    ('总经理办公室', 'GM_OFFICE', '总经理办公室，负责公司整体战略规划和管理决策', 1, true, NOW()),
    ('造价部', 'COST', '造价部门，负责项目造价审核、成本控制等工作', 2, true, NOW()),
    ('技术部', 'TECH', '技术部门，负责技术研发和项目执行', 3, true, NOW()),
    ('商务部', 'BUSINESS', '商务部门，负责商务洽谈和客户管理', 4, true, NOW())
ON CONFLICT (code) 
DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    "order" = EXCLUDED."order",
    is_active = EXCLUDED.is_active,
    created_time = EXCLUDED.created_time;

-- 查询验证
SELECT 
    id,
    name,
    code,
    description,
    "order",
    is_active,
    created_time
FROM system_department
ORDER BY "order", id;

