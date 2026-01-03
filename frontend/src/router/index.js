import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

const routes = [
  // 移除根路径路由，避免Vue Router拦截
  // 根路径应该由Django处理，显示home.html模板
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 如果路径以 /admin/ 开头，直接跳转到Django Admin，不经过Vue Router
  if (to.path.startsWith('/admin/')) {
    window.location.href = to.fullPath
    return
  }
  
  // 如果是根路径，直接跳转到Django首页
  if (to.path === '/' || to.path === '') {
    window.location.href = '/'
    return
  }
  
  const user = store.state.user || JSON.parse(localStorage.getItem('user') || 'null')
  
  if (to.meta.requiresAuth && !user) {
    // 需要登录但未登录，跳转到登录页，保留next参数以便登录后重定向
    next({
      path: '/login',
      query: { next: to.fullPath }
    })
  } else if (to.path === '/login' && user) {
    // 已登录访问登录页，检查是否有next参数，否则跳转到Django首页
    const nextUrl = to.query.next || '/'
    // 直接跳转到Django首页
    window.location.href = nextUrl
    return
  } else {
    next()
  }
})

export default router

