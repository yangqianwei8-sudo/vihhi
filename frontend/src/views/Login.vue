<template>
  <div class="login-wrapper">
    <!-- 左侧装饰区域 -->
    <div class="login-left">
      <div class="left-content">
        <p class="brand-slogan">为设计创建更大价值</p>
      </div>
      <!-- 装饰性粒子效果 -->
      <div class="particles">
        <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
      </div>
    </div>
    
    <!-- 右侧登录表单区域 -->
    <div class="login-right">
      <div class="login-container">
        <!-- 顶部Logo -->
        <div class="login-header">
          <div class="header-logo">
            <div class="logo-mini">
              <svg viewBox="0 0 48 48" fill="none">
                <rect width="48" height="48" rx="10" fill="url(#miniGradient)"/>
                <path d="M24 15L32 23L24 31L16 23L24 15Z" fill="white"/>
                <defs>
                  <linearGradient id="miniGradient" x1="0" y1="0" x2="48" y2="48">
                    <stop offset="0%" stop-color="#1F2A57"/>
                    <stop offset="100%" stop-color="#0F1E3A"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
          <h2 class="welcome-title">维海星图</h2>
          <p class="welcome-subtitle">请登录您的账号以继续使用系统</p>
        </div>
        
        <!-- 登录表单 -->
        <el-form 
          :model="loginForm" 
          :rules="rules" 
          ref="loginFormRef"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <div class="input-wrapper">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入用户名或邮箱"
                @keyup.enter="handleLogin"
                size="large"
                class="login-input"
                clearable
              >
                <template #prefix>
                  <el-icon class="input-icon"><User /></el-icon>
                </template>
              </el-input>
            </div>
          </el-form-item>
          
          <el-form-item prop="password">
            <div class="input-wrapper">
              <el-input 
                type="password" 
                v-model="loginForm.password" 
                placeholder="请输入密码"
                @keyup.enter="handleLogin"
                show-password
                size="large"
                class="login-input"
                clearable
              >
                <template #prefix>
                  <el-icon class="input-icon"><Lock /></el-icon>
                </template>
              </el-input>
            </div>
          </el-form-item>
          
          <!-- 记住密码和忘记密码 -->
          <div class="login-options">
            <el-checkbox v-model="rememberMe" class="remember-me">
              <span>记住我</span>
            </el-checkbox>
            <a href="#" class="forgot-password" @click.prevent="handleForgotPassword">
              忘记密码？
            </a>
          </div>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleLogin" 
              :loading="loading"
              size="large"
              class="login-button"
              native-type="submit"
            >
              <span v-if="!loading">
                <el-icon class="button-icon"><Right /></el-icon>
                立即登录
              </span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>
        
        <!-- 错误提示 -->
        <transition name="fade">
          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            :closable="true"
            @close="errorMessage = ''"
            show-icon
            class="error-alert"
          />
        </transition>
        
        <!-- 底部信息 -->
        <div class="login-footer">
          <div class="footer-divider">
            <span>或</span>
          </div>
          <p class="footer-text">
            <el-icon><InfoFilled /></el-icon>
            需要帮助？<a href="#" @click.prevent="handleContact">联系管理员</a>
          </p>
          <p class="copyright">© 2025 维海科技 版权所有</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { login } from '../api/system'
import { ElMessage } from 'element-plus'
import { User, Lock, InfoFilled, Right } from '@element-plus/icons-vue'

export default {
  name: 'Login',
  components: {
    User,
    Lock,
    InfoFilled,
    Right
  },
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      loading: false,
      errorMessage: '',
      rememberMe: false,
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
        ]
      }
    }
  },
  mounted() {
    // 从localStorage恢复记住的密码
    const rememberedUsername = localStorage.getItem('remembered_username')
    const rememberedPassword = localStorage.getItem('remembered_password')
    if (rememberedUsername && rememberedPassword) {
      this.loginForm.username = rememberedUsername
      this.loginForm.password = rememberedPassword
      this.rememberMe = true
    }
  },
  methods: {
    async handleLogin() {
      this.$refs.loginFormRef.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.loading = true
        this.errorMessage = ''
        
        try {
          const response = await login(this.loginForm.username, this.loginForm.password)
          
          // login函数现在返回Promise，需要await
          if (response && response.success) {
            // 保存用户信息
            if (response.user) {
              localStorage.setItem('user', JSON.stringify(response.user))
              this.$store.commit('SET_USER', response.user)
            }
            
            // 处理记住密码
            if (this.rememberMe) {
              localStorage.setItem('remembered_username', this.loginForm.username)
              localStorage.setItem('remembered_password', this.loginForm.password)
            } else {
              localStorage.removeItem('remembered_username')
              localStorage.removeItem('remembered_password')
            }
            
            // 显示成功消息
            ElMessage.success({
              message: response.message || '登录成功',
              duration: 2000
            })
            
            // 检查是否有next参数（从URL查询参数获取）
            let nextUrl = this.$route.query.next || '/'
            
            // 如果nextUrl是相对路径，转换为完整URL，确保绕过Vue Router
            if (nextUrl.startsWith('/')) {
              // 使用完整URL进行跳转，强制浏览器重新加载页面
              // 这样会跳转到Django的首页（home.html模板），而不是Vue的Home组件
              nextUrl = window.location.origin + nextUrl
            }
            
            // 延迟跳转，让用户看到成功消息
            setTimeout(() => {
              // 使用 replace 方法强制完整页面刷新，绕过Vue Router
              // 添加时间戳确保浏览器不会使用缓存
              const separator = nextUrl.includes('?') ? '&' : '?'
              window.location.replace(nextUrl + separator + '_t=' + Date.now())
            }, 500)
          } else {
            this.errorMessage = response?.message || '登录失败，请检查用户名和密码'
            ElMessage.error(this.errorMessage)
          }
        } catch (error) {
          console.error('登录错误:', error)
          // 处理网络错误
          let errorMsg = '登录失败，请稍后重试'
          if (error.code === 'ECONNABORTED' || error.code === 'NETWORK_ERROR') {
            errorMsg = error.message || '无法连接到服务器，请确保后端服务已启动（端口8001）'
          } else if (error.message) {
            errorMsg = error.message
          } else if (error.errors?.non_field_errors?.[0]) {
            errorMsg = error.errors.non_field_errors[0]
          }
          this.errorMessage = errorMsg
          ElMessage.error(errorMsg)
        } finally {
          this.loading = false
        }
      })
    },
    handleForgotPassword() {
      ElMessage.info('忘记密码功能开发中，请联系系统管理员')
    },
    handleContact() {
      ElMessage.info('请联系系统管理员获取帮助')
    },
    getParticleStyle(index) {
      const size = Math.random() * 4 + 2
      const left = Math.random() * 100
      const animationDelay = Math.random() * 20
      const animationDuration = Math.random() * 10 + 15
      return {
        width: `${size}px`,
        height: `${size}px`,
        left: `${left}%`,
        animationDelay: `${animationDelay}s`,
        animationDuration: `${animationDuration}s`
      }
    }
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  position: relative;
  overflow: hidden;
  background: #F6F8FC;
}

/* 左侧装饰区域 - 使用系统主题色 */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #1F2A57 0%, #0F1E3A 50%, #1F4A85 100%);
  background-size: 200% 200%;
  animation: gradientShift 20s ease infinite;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  overflow: hidden;
}

/* 添加网格背景纹理 */
.login-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.5;
  z-index: 1;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.left-content {
  position: relative;
  z-index: 2;
  color: white;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 40px;
}

.brand-title {
  font-size: 72px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 6px;
  color: #ffffff;
  text-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(255, 255, 255, 0.2),
    0 0 60px rgba(255, 255, 255, 0.1);
  animation: titleGlow 4s ease-in-out infinite;
  position: relative;
  font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
}

.brand-title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  border-radius: 2px;
  animation: underlineGlow 4s ease-in-out infinite;
}

.brand-slogan {
  font-size: 21px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 2px;
  color: #D62828;
  text-align: center;
  line-height: 1.4;
  text-shadow: 
    0 2px 8px rgba(214, 40, 40, 0.4),
    0 0 15px rgba(214, 40, 40, 0.3),
    0 0 25px rgba(214, 40, 40, 0.2);
  animation: sloganGlow 4s ease-in-out infinite;
  position: relative;
  z-index: 2;
  font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
  padding: 12px 24px;
  background: linear-gradient(135deg, rgba(214, 40, 40, 0.08) 0%, rgba(214, 40, 40, 0.03) 100%);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(214, 40, 40, 0.2);
  box-shadow: 
    0 4px 16px rgba(214, 40, 40, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transform: translateY(0);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.brand-slogan::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(214, 40, 40, 0.3), rgba(214, 40, 40, 0.1), rgba(214, 40, 40, 0.3));
  border-radius: 22px;
  z-index: -1;
  opacity: 0;
  animation: borderGlow 4s ease-in-out infinite;
}

.brand-slogan::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #D62828, transparent);
  border-radius: 2px;
  box-shadow: 0 0 12px rgba(214, 40, 40, 0.6);
  animation: underlinePulse 3s ease-in-out infinite;
}

@keyframes sloganGlow {
  0%, 100% {
    text-shadow: 
      0 2px 8px rgba(214, 40, 40, 0.4),
      0 0 15px rgba(214, 40, 40, 0.3),
      0 0 25px rgba(214, 40, 40, 0.2);
    transform: translateY(0) scale(1);
    box-shadow: 
      0 4px 16px rgba(214, 40, 40, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }
  50% {
    text-shadow: 
      0 3px 12px rgba(214, 40, 40, 0.5),
      0 0 20px rgba(214, 40, 40, 0.4),
      0 0 35px rgba(214, 40, 40, 0.3);
    transform: translateY(-2px) scale(1.02);
    box-shadow: 
      0 6px 20px rgba(214, 40, 40, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.15);
  }
}

@keyframes borderGlow {
  0%, 100% {
    opacity: 0;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes underlinePulse {
  0%, 100% {
    width: 80px;
    opacity: 0.8;
    box-shadow: 0 0 12px rgba(214, 40, 40, 0.6);
  }
  50% {
    width: 120px;
    opacity: 1;
    box-shadow: 0 0 18px rgba(214, 40, 40, 0.8);
  }
}

@keyframes titleGlow {
  0%, 100% {
    text-shadow: 
      0 4px 20px rgba(0, 0, 0, 0.4),
      0 0 40px rgba(255, 255, 255, 0.2),
      0 0 60px rgba(255, 255, 255, 0.1);
    transform: scale(1);
  }
  50% {
    text-shadow: 
      0 4px 20px rgba(0, 0, 0, 0.4),
      0 0 60px rgba(255, 255, 255, 0.3),
      0 0 80px rgba(255, 255, 255, 0.2);
    transform: scale(1.02);
  }
}

@keyframes underlineGlow {
  0%, 100% {
    opacity: 0.6;
    width: 60px;
  }
  50% {
    opacity: 1;
    width: 100px;
  }
}

/* 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0) 70%);
  border-radius: 50%;
  animation: particleFloat infinite linear;
  bottom: -10px;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) translateX(50px) rotate(360deg);
    opacity: 0;
  }
}

/* 右侧登录表单区域 - 使用系统背景色 */
.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #F6F8FC;
  position: relative;
}

.login-container {
  width: 100%;
  max-width: 440px;
  background: #ffffff;
  padding: 56px 48px;
  border-radius: 20px;
  box-shadow: 
    0 8px 24px rgba(15, 30, 58, 0.12),
    0 2px 8px rgba(15, 30, 58, 0.08);
  animation: slideInRight 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(228, 232, 244, 0.5);
  position: relative;
  overflow: hidden;
}

/* 添加微妙的顶部高光 */
.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(31, 42, 87, 0.1), transparent);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.header-logo {
  margin-bottom: 24px;
}

.logo-mini {
  width: 72px;
  height: 72px;
  margin: 0 auto;
  filter: drop-shadow(0 4px 16px rgba(31, 42, 87, 0.2));
  animation: logoPulse 3s ease-in-out infinite;
  transition: transform 0.3s ease;
}

.logo-mini:hover {
  transform: scale(1.1) rotate(5deg);
}

@keyframes logoPulse {
  0%, 100% { 
    transform: scale(1) rotate(0deg);
    filter: drop-shadow(0 4px 16px rgba(31, 42, 87, 0.2));
  }
  50% { 
    transform: scale(1.08) rotate(2deg);
    filter: drop-shadow(0 6px 20px rgba(31, 42, 87, 0.3));
  }
}

.logo-mini svg {
  width: 100%;
  height: 100%;
}


.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #1F2A57;
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
  line-height: 1.2;
}

.welcome-subtitle {
  font-size: 15px;
  color: #6B7280;
  margin: 0;
  line-height: 1.6;
  font-weight: 400;
}


.login-form {
  margin-top: 40px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

.input-wrapper {
  position: relative;
}

.login-input {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-input :deep(.el-input__wrapper) {
  box-shadow: 
    0 1px 3px rgba(15, 30, 58, 0.05),
    0 0 0 1px #E4E8F4 inset,
    inset 0 1px 2px rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  padding: 15px 18px;
  background: #F6F7FD;
}

.login-input :deep(.el-input__wrapper:hover) {
  box-shadow: 
    0 2px 8px rgba(15, 30, 58, 0.08),
    0 0 0 1px #E4E8F4 inset,
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  background: #ffffff;
  transform: translateY(-1px);
}

.login-input :deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 
    0 0 0 4px rgba(31, 42, 87, 0.08),
    0 0 0 1px #1F2A57 inset,
    0 2px 8px rgba(31, 42, 87, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 1);
  background: #ffffff;
  transform: translateY(-2px);
}

.input-icon {
  font-size: 18px;
  color: #6C7BA8;
  margin-right: 10px;
  transition: color 0.3s;
}

.login-input :deep(.el-input.is-focus .input-icon) {
  color: #1F2A57;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  font-size: 14px;
  padding: 0 2px;
}

.remember-me {
  color: #6B7280;
}

.remember-me :deep(.el-checkbox__label) {
  color: #6B7280;
  font-size: 14px;
}

.forgot-password {
  color: #1F2A57;
  text-decoration: none;
  transition: all 0.3s;
  font-size: 14px;
  font-weight: 500;
}

.forgot-password:hover {
  color: #1F4A85;
  text-decoration: underline;
}

.login-button {
  width: 100%;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #1F2A57 0%, #0F1E3A 100%);
  border: none;
  box-shadow: 
    0 4px 14px rgba(31, 42, 87, 0.3),
    0 2px 4px rgba(15, 30, 58, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  letter-spacing: 0.5px;
  color: #ffffff;
  position: relative;
  overflow: hidden;
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-button:hover:not(.is-loading)::before {
  left: 100%;
}

.login-button:hover:not(.is-loading) {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 24px rgba(31, 42, 87, 0.4),
    0 4px 8px rgba(15, 30, 58, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  background: linear-gradient(135deg, #1F4A85 0%, #1F2A57 100%);
}

.login-button:active:not(.is-loading) {
  transform: translateY(0);
  box-shadow: 
    0 2px 8px rgba(31, 42, 87, 0.3),
    inset 0 2px 4px rgba(15, 30, 58, 0.3);
}

.login-button.is-loading {
  opacity: 0.8;
  cursor: not-allowed;
}

.button-icon {
  font-size: 18px;
}

/* 错误提示动画 */
.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.error-alert {
  margin-top: 20px;
  border-radius: 12px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-footer {
  margin-top: 48px;
  text-align: center;
}

.footer-divider {
  position: relative;
  margin: 32px 0 24px 0;
  text-align: center;
}

.footer-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #E4E8F4;
}

.footer-divider span {
  position: relative;
  background: #ffffff;
  padding: 0 16px;
  color: #9CA3AF;
  font-size: 13px;
}

.footer-text {
  color: #6B7280;
  font-size: 13px;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.footer-text .el-icon {
  font-size: 14px;
}

.footer-text a {
  color: #1F2A57;
  text-decoration: none;
  margin-left: 4px;
  transition: color 0.3s;
  font-weight: 500;
}

.footer-text a:hover {
  color: #1F4A85;
  text-decoration: underline;
}

.copyright {
  color: #9CA3AF;
  font-size: 12px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .brand-slogan {
    font-size: 36px;
    letter-spacing: 3px;
    padding: 16px 32px;
  }
  
  .login-wrapper {
    flex-direction: column;
  }
  
  .login-left {
    min-height: 35vh;
    padding: 40px 30px;
  }
  
  .brand-slogan {
    font-size: 32px;
    letter-spacing: 3px;
    padding: 16px 28px;
  }
  
  .brand-slogan::after {
    width: 100px;
  }
}

@media (max-width: 768px) {
  .login-left {
    min-height: 30vh;
    padding: 30px 20px;
  }
  
  .brand-slogan {
    font-size: 14px;
    letter-spacing: 1px;
    padding: 8px 16px;
  }
  
  .brand-slogan::after {
    width: 60px;
  }
  
  .login-right {
    padding: 30px 20px;
  }
  
  .login-container {
    padding: 40px 32px;
    border-radius: 16px;
  }
  
  .welcome-title {
    font-size: 28px;
  }
  
  .welcome-subtitle {
    font-size: 14px;
  }
  
  .logo-mini {
    width: 64px;
    height: 64px;
  }
  
  .login-button {
    height: 50px;
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .login-left {
    min-height: 25vh;
    padding: 24px 20px;
  }
  
  .brand-slogan {
    font-size: 12px;
    letter-spacing: 0.75px;
    padding: 8px 14px;
  }
  
  .brand-slogan::after {
    width: 50px;
    height: 2px;
  }
  
  .login-right {
    padding: 24px 16px;
  }
  
  .login-container {
    max-width: 100%;
    padding: 36px 24px;
    border-radius: 16px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-subtitle {
    font-size: 13px;
  }
  
  .logo-mini {
    width: 56px;
    height: 56px;
  }
  
  .login-button {
    height: 48px;
    font-size: 15px;
  }
  
  .login-form {
    margin-top: 32px;
  }
}
</style>

