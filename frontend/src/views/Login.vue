<template>
  <div class="login">
    <div class="login-container">
      <h1>维海科技信息化管理平台</h1>
      <el-form 
        :model="loginForm" 
        :rules="rules" 
        ref="loginFormRef"
        label-width="80px"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          ></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input 
            type="password" 
            v-model="loginForm.password" 
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
            show-password
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleLogin" 
            :loading="loading"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { login } from '../api/system'
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      loading: false,
      errorMessage: '',
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
            
            // 显示成功消息
            ElMessage.success(response.message || '登录成功')
            
            // 跳转到首页
            this.$router.push('/')
          } else {
            this.errorMessage = response?.message || '登录失败，请检查用户名和密码'
            ElMessage.error(this.errorMessage)
          }
        } catch (error) {
          console.error('登录错误:', error)
          const errorMsg = error.message || error.errors?.non_field_errors?.[0] || '登录失败，请稍后重试'
          this.errorMessage = errorMsg
          ElMessage.error(errorMsg)
        } finally {
          this.loading = false
        }
      })
    }
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-container h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

.login-form {
  margin-top: 20px;
}

.error-message {
  margin-top: 15px;
  padding: 10px;
  background-color: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  text-align: center;
  font-size: 14px;
}
</style>

