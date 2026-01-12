# 计划管理 API 使用示例

## 导入 API

```javascript
import { goalApi, planApi } from '@/api/plan'
```

## 目标管理示例

### 获取目标列表
```javascript
// 获取目标列表（自动按公司过滤）
const goals = await goalApi.list({
  status: 'in_progress',
  goal_type: 'personal',
  page: 1
})
```

### 创建目标（不传 company/org_department）
```javascript
const formData = {
  goal_type: 'personal',
  goal_period: 'annual',
  indicator_name: '2026年销售额目标',
  indicator_type: 'numeric',
  indicator_unit: '万元',
  target_value: 1000,
  current_value: 0,
  status: 'draft',
  responsible_person: 125,
  created_by: 125
}

// ⚠️ 注意：不要传 company 和 org_department，后端会自动继承
const newGoal = await goalApi.create(formData)
// 返回的数据中会自动包含 company 和 org_department
```

### 更新目标（白名单字段）
```javascript
// 只更新允许的字段，company/org_department 会被自动过滤
const updatedGoal = await goalApi.update(goalId, {
  indicator_name: '更新后的目标名称',
  target_value: 1200,
  // company 和 org_department 会被自动过滤，不会发送到后端
})
```

## 计划管理示例

### 获取计划列表
```javascript
const plans = await planApi.list({
  status: 'in_progress',
  plan_type: 'personal',
  plan_period: 'weekly'
})
```

### 创建计划（不传 company/org_department）
```javascript
const planData = {
  name: '本周工作计划',
  plan_type: 'personal',
  plan_period: 'weekly',
  related_goal: 17, // 关联的目标ID
  content: '计划内容',
  plan_objective: '计划目标',
  start_time: '2026-01-08T09:00:00+08:00',
  end_time: '2026-01-15T18:00:00+08:00',
  responsible_person: 125,
  created_by: 125,
  progress: 0,
  status: 'draft'
}

// ⚠️ 注意：不要传 company 和 org_department，后端会自动继承
const newPlan = await planApi.create(planData)
```

### 更新计划进度
```javascript
// 更新进度（如果后端有专门的接口）
await planApi.updateProgress(planId, {
  progress: 50,
  progress_description: '已完成一半工作'
})
```

## 重要提示

1. **不要在前端表单中包含 company/org_department 字段**
2. **使用白名单字段提交**：API 会自动过滤不允许的字段
3. **普通用户无法修改归属字段**：尝试修改会返回 403 错误
4. **数据自动隔离**：普通用户只能看到自己公司的数据

