import api from './index'

// 工具函数：从对象中提取指定字段（白名单）
function pick(obj, keys) {
  const out = {}
  keys.forEach((k) => {
    if (obj[k] !== undefined) out[k] = obj[k]
  })
  return out
}

// 目标字段白名单
const GOAL_FIELDS = [
  'goal_type',
  'goal_period',
  'indicator_name',
  'indicator_type',
  'indicator_unit',
  'target_value',
  'current_value',
  'status',
  'responsible_person',
  'responsible_department',
  'participants',
  'created_by',
]

// 计划字段白名单
const PLAN_FIELDS = [
  'name',
  'plan_type',
  'plan_period',
  'related_goal',
  'content',
  'plan_objective',
  'start_time',
  'end_time',
  'responsible_person',
  'responsible_department',
  'participants',
  'parent_plan',
  'progress',
  'status',
  'created_by',
]

const BASE = '/plan'

export const goalApi = {
  list(params = {}) {
    return api.get(`${BASE}/strategic-goals/`, { params })
  },
  detail(id) {
    return api.get(`${BASE}/strategic-goals/${id}/`)
  },
  create(data) {
    // ⚠️ 不允许前端传 company/org_department（让后端自动继承）
    const payload = pick(data || {}, GOAL_FIELDS)
    return api.post(`${BASE}/strategic-goals/`, payload)
  },
  update(id, data) {
    // 普通用户禁止改归属；前端也不要发
    const payload = pick(data || {}, GOAL_FIELDS)
    return api.patch(`${BASE}/strategic-goals/${id}/`, payload)
  },
  delete(id) {
    return api.delete(`${BASE}/strategic-goals/${id}/`)
  },
}

export const planApi = {
  list(params = {}) {
    return api.get(`${BASE}/plans/`, { params })
  },
  detail(id) {
    return api.get(`${BASE}/plans/${id}/`)
  },
  create(data) {
    // ⚠️ 不允许前端传 company/org_department（让后端自动继承）
    const payload = pick(data || {}, PLAN_FIELDS)
    return api.post(`${BASE}/plans/`, payload)
  },
  update(id, data) {
    // 普通用户禁止改归属；前端也不要发
    const payload = pick(data || {}, PLAN_FIELDS)
    return api.patch(`${BASE}/plans/${id}/`, payload)
  },
  delete(id) {
    return api.delete(`${BASE}/plans/${id}/`)
  },
  
  // A3-3-8-3 进度更新（带白名单）
  updateProgress(id, data) {
    const PROGRESS_UPDATE_FIELDS = [
      'progress',
      'progress_description',
      'execution_result',
      'execution_issues',
      'notes',
    ]
    const payload = pick(data || {}, PROGRESS_UPDATE_FIELDS)
    return api.post(`${BASE}/plans/${id}/progress/`, payload)
  },
  
  // A3-3-8-3 状态变更（带白名单）
  changeStatus(id, data) {
    const STATUS_CHANGE_FIELDS = [
      'status',
      'reason',
    ]
    const payload = pick(data || {}, STATUS_CHANGE_FIELDS)
    return api.post(`${BASE}/plans/${id}/status/`, payload)
  },
}

// A3-3-6 统计 API
export const planStatsApi = {
  plans(params = {}) {
    const payload = pick(params || {}, ['mine', 'participating', 'range', 'no_cache'])
    return api.get(`${BASE}/stats/plans/`, { params: payload })
  },
  goals(params = {}) {
    const payload = pick(params || {}, ['mine', 'participating', 'range', 'no_cache'])
    return api.get(`${BASE}/stats/goals/`, { params: payload })
  },
}

// C3-3-2: 通知 API
export const notificationApi = {
  list(params = {}) {
    return api.get(`${BASE}/notifications/`, { params })
  },
  unreadCount() {
    return api.get(`${BASE}/notifications/unread-count/`)
  },
  markRead(id) {
    return api.post(`${BASE}/notifications/${id}/mark-read/`)
  },
  markAllRead() {
    return api.post(`${BASE}/notifications/mark-all-read/`)
  }
}

