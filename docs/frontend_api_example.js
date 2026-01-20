/**
 * 企业信息查询API - 前端调用示例
 * 
 * 使用说明：
 * 1. 将此文件内容添加到前端项目的 src/api/customer.js 中
 * 2. 在Vue组件中导入并使用
 * 
 * 技术栈：Vue.js + Axios
 */

import request from '@/utils/request'

/**
 * 通过企业名称获取企业信息（四要素）
 * 
 * @param {string} companyName - 企业名称（至少2个字符）
 * @returns {Promise<Object>} 返回Promise，resolve时包含企业信息
 * 
 * @example
 * // 基本使用
 * getCompanyInfoByName('威海华东数控股份有限公司')
 *   .then(response => {
 *     if (response.success) {
 *       console.log('企业信息:', response.data)
 *       // 自动填充表单...
 *     }
 *   })
 * 
 * @example
 * // 在async函数中使用
 * async function fetchCompanyInfo() {
 *   try {
 *     const res = await getCompanyInfoByName('威海华东数控股份有限公司')
 *     if (res.success) {
 *       // 处理数据...
 *     }
 *   } catch (error) {
 *     console.error('查询失败:', error)
 *   }
 * }
 * 
 * 返回数据格式：
 * {
 *   success: true,
 *   data: {
 *     name: "威海华东数控股份有限公司",
 *     credit_code: "91370000163500000X",
 *     legal_representative: "张某某",
 *     established_date: "1993-07-15",
 *     registered_capital: "6500 万人民币",
 *     registered_capital_value: 6500.0,
 *     phone: "0631-5326888",
 *     email: "info@example.com",
 *     address: "山东省威海市高新技术产业开发区..."
 *   },
 *   message: "获取成功"
 * }
 */
export function getCompanyInfoByName(companyName) {
  return request({
    url: '/api/customer/get-company-info-by-name/',
    method: 'get',
    params: {
      company_name: companyName
    }
  })
}

/**
 * Vue组件使用示例
 * 
 * 将以下代码复制到您的Vue组件中
 */

/*
<template>
  <div class="customer-create-form">
    <el-form :model="customerForm" :rules="rules" ref="customerFormRef" label-width="140px">
      
      <!-- 企业名称输入框 -->
      <el-form-item label="企业名称" prop="name" required>
        <el-input 
          v-model="customerForm.name" 
          placeholder="请输入企业名称，至少2个字符"
          clearable
        >
          <template #append>
            <el-button 
              icon="Search"
              :loading="searchLoading"
              @click="handleSearchCompanyInfo"
            >
              查询企业信息
            </el-button>
          </template>
        </el-input>
        <div class="form-item-tip">
          输入企业名称后，点击"查询企业信息"按钮自动填充企业四要素
        </div>
      </el-form-item>

      <!-- 以下字段将自动填充 -->
      
      <el-form-item label="统一社会信用代码" prop="unified_credit_code">
        <el-input 
          v-model="customerForm.unified_credit_code" 
          placeholder="自动获取"
          maxlength="18"
          :readonly="autoFilled"
        />
      </el-form-item>

      <el-form-item label="法定代表人" prop="legal_representative">
        <el-input 
          v-model="customerForm.legal_representative" 
          placeholder="自动获取"
          :readonly="autoFilled"
        />
      </el-form-item>

      <el-form-item label="成立日期" prop="established_date">
        <el-date-picker
          v-model="customerForm.established_date"
          type="date"
          placeholder="自动获取"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :readonly="autoFilled"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="注册资本" prop="registered_capital">
        <el-input-number
          v-model="customerForm.registered_capital"
          :precision="2"
          :min="0"
          placeholder="自动获取（万元）"
          :controls="false"
          :readonly="autoFilled"
          style="width: 100%"
        >
          <template #append>万元</template>
        </el-input-number>
      </el-form-item>

      <el-form-item label="联系电话" prop="company_phone">
        <el-input 
          v-model="customerForm.company_phone" 
          placeholder="自动获取"
          :readonly="autoFilled"
        />
      </el-form-item>

      <el-form-item label="邮箱" prop="company_email">
        <el-input 
          v-model="customerForm.company_email" 
          placeholder="自动获取"
          type="email"
          :readonly="autoFilled"
        />
      </el-form-item>

      <el-form-item label="地址" prop="company_address">
        <el-input 
          v-model="customerForm.company_address" 
          type="textarea"
          :rows="3"
          placeholder="自动获取"
          :readonly="autoFilled"
        />
      </el-form-item>

      <!-- 如果需要手动编辑自动填充的字段 -->
      <el-form-item v-if="autoFilled">
        <el-button @click="handleUnlockFields" type="warning" plain size="small">
          <el-icon><Unlock /></el-icon>
          允许手动编辑
        </el-button>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </el-form-item>

    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Unlock } from '@element-plus/icons-vue'
import { getCompanyInfoByName } from '@/api/customer'

// 表单数据
const customerForm = reactive({
  name: '',
  unified_credit_code: '',
  legal_representative: '',
  established_date: null,
  registered_capital: null,
  company_phone: '',
  company_email: '',
  company_address: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入企业名称', trigger: 'blur' },
    { min: 2, message: '企业名称至少2个字符', trigger: 'blur' }
  ]
}

// 状态
const searchLoading = ref(false)
const autoFilled = ref(false) // 是否自动填充
const customerFormRef = ref(null)

/**
 * 查询企业信息
 */
const handleSearchCompanyInfo = async () => {
  const companyName = customerForm.name.trim()
  
  // 验证企业名称
  if (!companyName || companyName.length < 2) {
    ElMessage.warning('请输入至少2个字符的企业名称')
    return
  }

  searchLoading.value = true

  try {
    const response = await getCompanyInfoByName(companyName)
    
    if (response.success && response.data) {
      // 自动填充表单
      const data = response.data
      
      customerForm.name = data.name || customerForm.name
      customerForm.unified_credit_code = data.credit_code || ''
      customerForm.legal_representative = data.legal_representative || ''
      customerForm.established_date = data.established_date || null
      customerForm.registered_capital = data.registered_capital_value || null
      customerForm.company_phone = data.phone || ''
      customerForm.company_email = data.email || ''
      customerForm.company_address = data.address || ''

      autoFilled.value = true

      ElMessage.success({
        message: '企业信息获取成功！已自动填充表单',
        duration: 3000
      })

      // 如果有缺失的字段，给出提示
      const missingFields = []
      if (!data.phone) missingFields.push('联系电话')
      if (!data.email) missingFields.push('邮箱')
      
      if (missingFields.length > 0) {
        ElMessage.warning({
          message: `以下字段未获取到数据，请手动填写：${missingFields.join('、')}`,
          duration: 5000
        })
      }
    } else {
      ElMessage.warning(response.message || '未找到该企业信息，请检查企业名称是否正确')
    }
  } catch (error) {
    console.error('获取企业信息失败:', error)
    ElMessage.error('获取企业信息失败，请稍后重试')
  } finally {
    searchLoading.value = false
  }
}

/**
 * 解锁字段，允许手动编辑
 */
const handleUnlockFields = () => {
  autoFilled.value = false
  ElMessage.info('已允许手动编辑自动填充的字段')
}

/**
 * 提交表单
 */
const handleSubmit = () => {
  customerFormRef.value.validate((valid) => {
    if (valid) {
      console.log('提交表单数据:', customerForm)
      // 调用创建客户的API...
      ElMessage.success('客户创建成功')
    } else {
      ElMessage.error('请完善表单信息')
    }
  })
}

/**
 * 取消
 */
const handleCancel = () => {
  // 返回列表页或关闭对话框...
}
</script>

<style scoped>
.customer-create-form {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
*/

/**
 * 如果不使用Vue 3 Composition API，可以使用以下Options API版本
 */

/*
export default {
  name: 'CustomerCreateForm',
  
  data() {
    return {
      searchLoading: false,
      autoFilled: false,
      
      customerForm: {
        name: '',
        unified_credit_code: '',
        legal_representative: '',
        established_date: null,
        registered_capital: null,
        company_phone: '',
        company_email: '',
        company_address: ''
      },
      
      rules: {
        name: [
          { required: true, message: '请输入企业名称', trigger: 'blur' },
          { min: 2, message: '企业名称至少2个字符', trigger: 'blur' }
        ]
      }
    }
  },
  
  methods: {
    async handleSearchCompanyInfo() {
      const companyName = this.customerForm.name.trim()
      
      if (!companyName || companyName.length < 2) {
        this.$message.warning('请输入至少2个字符的企业名称')
        return
      }

      this.searchLoading = true

      try {
        const response = await getCompanyInfoByName(companyName)
        
        if (response.success && response.data) {
          const data = response.data
          
          this.customerForm.name = data.name || this.customerForm.name
          this.customerForm.unified_credit_code = data.credit_code || ''
          this.customerForm.legal_representative = data.legal_representative || ''
          this.customerForm.established_date = data.established_date || null
          this.customerForm.registered_capital = data.registered_capital_value || null
          this.customerForm.company_phone = data.phone || ''
          this.customerForm.company_email = data.email || ''
          this.customerForm.company_address = data.address || ''

          this.autoFilled = true

          this.$message.success('企业信息获取成功！已自动填充表单')
        } else {
          this.$message.warning(response.message || '未找到该企业信息')
        }
      } catch (error) {
        console.error('获取企业信息失败:', error)
        this.$message.error('获取企业信息失败，请稍后重试')
      } finally {
        this.searchLoading = false
      }
    },
    
    handleUnlockFields() {
      this.autoFilled = false
      this.$message.info('已允许手动编辑自动填充的字段')
    },
    
    handleSubmit() {
      this.$refs.customerFormRef.validate((valid) => {
        if (valid) {
          console.log('提交表单数据:', this.customerForm)
          // 调用创建客户的API...
        }
      })
    }
  }
}
*/

/**
 * 纯JavaScript（无框架）使用示例
 */

/*
// HTML
<form id="customerForm">
  <div class="form-group">
    <label>企业名称</label>
    <input type="text" id="companyName" placeholder="请输入企业名称" />
    <button type="button" onclick="searchCompanyInfo()">查询企业信息</button>
  </div>
  
  <div class="form-group">
    <label>统一社会信用代码</label>
    <input type="text" id="creditCode" readonly />
  </div>
  
  <div class="form-group">
    <label>法定代表人</label>
    <input type="text" id="legalRepresentative" readonly />
  </div>
  
  <!-- 其他字段... -->
</form>

// JavaScript
async function searchCompanyInfo() {
  const companyName = document.getElementById('companyName').value.trim()
  
  if (!companyName || companyName.length < 2) {
    alert('请输入至少2个字符的企业名称')
    return
  }
  
  const token = localStorage.getItem('token') // 获取认证token
  
  try {
    const response = await fetch(
      `/api/customer/get-company-info-by-name/?company_name=${encodeURIComponent(companyName)}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    const result = await response.json()
    
    if (result.success && result.data) {
      const data = result.data
      
      document.getElementById('creditCode').value = data.credit_code || ''
      document.getElementById('legalRepresentative').value = data.legal_representative || ''
      // 填充其他字段...
      
      alert('企业信息获取成功！')
    } else {
      alert(result.message || '未找到该企业信息')
    }
  } catch (error) {
    console.error('查询失败:', error)
    alert('查询失败，请稍后重试')
  }
}
*/

