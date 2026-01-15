-- ============================================================
-- SQL 脚本：手动清理冗余权限
-- ============================================================
-- 此脚本用于手动检查和清理数据库中的冗余权限
-- 注意：执行前请备份数据库！
-- ============================================================

-- ============================================================
-- 步骤 1：检查 Django 自动生成的权限（auth_permission 表）
-- ============================================================

-- 检查 Plan 模型的权限
SELECT 
    p.id,
    p.codename,
    p.name,
    ct.app_label,
    ct.model,
    COUNT(DISTINCT up.user_id) as user_count,
    COUNT(DISTINCT gp.group_id) as group_count
FROM auth_permission p
JOIN django_content_type ct ON p.content_type_id = ct.id
LEFT JOIN auth_user_user_permissions up ON p.id = up.permission_id
LEFT JOIN auth_group_permissions gp ON p.id = gp.permission_id
WHERE ct.app_label = 'plan_management' 
  AND ct.model = 'plan'
  AND p.codename NOT LIKE 'custom_%'
GROUP BY p.id, p.codename, p.name, ct.app_label, ct.model;

-- 检查 StrategicGoal 模型的权限
SELECT 
    p.id,
    p.codename,
    p.name,
    ct.app_label,
    ct.model,
    COUNT(DISTINCT up.user_id) as user_count,
    COUNT(DISTINCT gp.group_id) as group_count
FROM auth_permission p
JOIN django_content_type ct ON p.content_type_id = ct.id
LEFT JOIN auth_user_user_permissions up ON p.id = up.permission_id
LEFT JOIN auth_group_permissions gp ON p.id = gp.permission_id
WHERE ct.app_label = 'plan_management' 
  AND ct.model = 'strategicgoal'
  AND p.codename NOT LIKE 'custom_%'
GROUP BY p.id, p.codename, p.name, ct.app_label, ct.model;

-- ============================================================
-- 步骤 2：检查业务权限表中的冗余权限（system_permission_item 表）
-- ============================================================

-- 检查冗余业务权限
SELECT 
    pi.id,
    pi.code,
    pi.name,
    pi.module,
    pi.action,
    COUNT(DISTINCT rp.role_id) as role_count
FROM system_permission_item pi
LEFT JOIN system_role_custom_permissions rp ON pi.id = rp.permissionitem_id
WHERE pi.code IN ('plan_management.view_plan', 'plan_management.view_strategicgoal')
GROUP BY pi.id, pi.code, pi.name, pi.module, pi.action;

-- ============================================================
-- 步骤 3：检查标准权限是否存在
-- ============================================================

-- 检查标准业务权限
SELECT 
    code,
    name,
    module,
    action,
    is_active
FROM system_permission_item
WHERE code IN (
    'plan_management.view',
    'plan_management.plan.view',
    'plan_management.plan.create',
    'plan_management.plan.manage',
    'plan_management.goal.view',
    'plan_management.goal.create',
    'plan_management.manage_goal'
)
ORDER BY code;

-- ============================================================
-- 步骤 4：清理操作（谨慎执行！）
-- ============================================================

-- 4.1 从用户中移除 Plan 模型的权限
-- DELETE FROM auth_user_user_permissions
-- WHERE permission_id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'plan'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.2 从组中移除 Plan 模型的权限
-- DELETE FROM auth_group_permissions
-- WHERE permission_id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'plan'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.3 删除 Plan 模型的权限
-- DELETE FROM auth_permission
-- WHERE id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'plan'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.4 从用户中移除 StrategicGoal 模型的权限
-- DELETE FROM auth_user_user_permissions
-- WHERE permission_id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'strategicgoal'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.5 从组中移除 StrategicGoal 模型的权限
-- DELETE FROM auth_group_permissions
-- WHERE permission_id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'strategicgoal'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.6 删除 StrategicGoal 模型的权限
-- DELETE FROM auth_permission
-- WHERE id IN (
--     SELECT p.id 
--     FROM auth_permission p
--     JOIN django_content_type ct ON p.content_type_id = ct.id
--     WHERE ct.app_label = 'plan_management' 
--       AND ct.model = 'strategicgoal'
--       AND p.codename NOT LIKE 'custom_%'
-- );

-- 4.7 从角色中移除冗余业务权限
-- DELETE FROM system_role_custom_permissions
-- WHERE permissionitem_id IN (
--     SELECT id 
--     FROM system_permission_item
--     WHERE code IN ('plan_management.view_plan', 'plan_management.view_strategicgoal')
-- );

-- 4.8 删除冗余业务权限项
-- DELETE FROM system_permission_item
-- WHERE code IN ('plan_management.view_plan', 'plan_management.view_strategicgoal');

-- ============================================================
-- 步骤 5：验证清理结果
-- ============================================================

-- 验证 Django 权限是否已清理
SELECT COUNT(*) as remaining_permissions
FROM auth_permission p
JOIN django_content_type ct ON p.content_type_id = ct.id
WHERE ct.app_label = 'plan_management' 
  AND ct.model IN ('plan', 'strategicgoal')
  AND p.codename NOT LIKE 'custom_%';
-- 期望结果：0

-- 验证业务权限是否已清理
SELECT COUNT(*) as remaining_business_permissions
FROM system_permission_item
WHERE code IN ('plan_management.view_plan', 'plan_management.view_strategicgoal');
-- 期望结果：0

-- 验证标准权限是否存在
SELECT COUNT(*) as standard_permissions_count
FROM system_permission_item
WHERE code IN (
    'plan_management.view',
    'plan_management.plan.view',
    'plan_management.plan.create',
    'plan_management.plan.manage',
    'plan_management.goal.view',
    'plan_management.goal.create',
    'plan_management.manage_goal'
);
-- 期望结果：7

