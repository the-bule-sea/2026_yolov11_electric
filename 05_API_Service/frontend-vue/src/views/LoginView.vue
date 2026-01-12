<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>⚡ 电力巡检图像智能检测系统</h2>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="auth-tabs">
        <!-- 登录 Tab -->
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="0">
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="用户名" 
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="密码" 
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="full-width" @click="handleLogin" :loading="loading">
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 注册 Tab -->
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="0">
            <el-form-item prop="username">
              <el-input 
                v-model="registerForm.username" 
                placeholder="用户名" 
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="registerForm.password" 
                type="password" 
                placeholder="密码" 
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item prop="email">
              <el-input 
                v-model="registerForm.email" 
                placeholder="邮箱" 
                :prefix-icon="Message"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="success" class="full-width" @click="handleRegister" :loading="loading">
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  email: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await axios.post('/api/v1/auth/login', loginForm)
        if (res.data.code === 200) {
          const { token, user_info } = res.data.data
          userStore.setToken(token)
          userStore.setUserInfo(user_info)
          ElMessage.success('登录成功')
          router.push('/')
        } else {
          ElMessage.error(res.data.msg || '登录失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || '连接服务器失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await axios.post('/api/v1/auth/register', registerForm)
        if (res.data.code === 200) {
          ElMessage.success('注册成功，请登录')
          activeTab.value = 'login'
          loginForm.username = registerForm.username
          loginForm.password = ''
        } else {
          ElMessage.error(res.data.msg || '注册失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || '连接服务器失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
  background-image: url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg');
  background-repeat: no-repeat;
  background-position: center 110px;
  background-size: 100%;
}

.login-card {
  width: 400px;
  border-radius: 8px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.full-width {
  width: 100%;
}

.auth-tabs {
  padding: 0 10px;
}
</style>
