import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 检查当前路径是否为Admin页面
const isAdminPath = window.location.pathname.startsWith('/admin/')

// 检查当前路径是否为根路径（需要跳转到Django首页）
const isRootPath = window.location.pathname === '/' || window.location.pathname === ''

// 检查是否存在#app元素（Vue应用的挂载点）
const appElement = document.getElementById('app')

// 如果是根路径（不是/login），且存在#app元素（说明是Vue应用页面），才跳转到Django首页
// 如果不存在#app元素，说明已经是Django页面，不需要跳转，避免循环
if (isRootPath && !window.location.pathname.startsWith('/login') && appElement) {
  // 强制完整页面刷新，跳转到Django首页
  window.location.replace('/')
} else {
  // 只在非Admin页面且存在#app元素时才挂载Vue应用
  if (!isAdminPath && appElement) {
  const app = createApp(App)

  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(store)
  app.use(router)
  app.use(ElementPlus)

    app.mount('#app')
  } else if (isAdminPath) {
    // 如果是Admin页面，确保不执行任何Vue相关操作
    console.log('[Vue] Admin页面检测到，跳过Vue应用挂载')
  }
}
