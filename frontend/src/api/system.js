import api from './index'

// 用户登录 - 使用Django REST Framework的API登录
export const login = (username, password) => {
  return api.post('/system/users/login/', {
    username,
    password
  }).then(response => {
    // API返回格式: { success: true, user: {...}, message: '登录成功' }
    if (response.success && response.user) {
      return {
        success: true,
        message: response.message || '登录成功',
        user: response.user
      }
    }
    return {
      success: false,
      message: response.message || '登录失败'
    }
  }).catch(error => {
    console.error('登录错误:', error)
    // 处理错误响应
    const errorMsg = error.message || error.errors?.non_field_errors?.[0] || '登录失败，请稍后重试'
    return {
      success: false,
      message: errorMsg
    }
  })
}

// 用户退出
export const logout = () => {
  return api.post('/system/users/logout/')
}

// 获取用户信息
export const getUserProfile = () => {
  return api.get('/system/users/profile/')
}

// 更新用户资料
export const updateUserProfile = (data) => {
  return api.put('/system/users/me/profile/', data)
}

// 修改密码
export const changePassword = (oldPassword, newPassword, confirmPassword) => {
  return api.post('/system/users/me/password/', {
    old_password: oldPassword,
    new_password: newPassword,
    confirm_password: confirmPassword
  })
}

