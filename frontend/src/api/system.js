import api from './index'

// 用户登录
export const login = (username, password) => {
  return api.post('/system/users/login/', {
    username,
    password
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

