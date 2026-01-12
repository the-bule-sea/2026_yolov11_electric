<template>
  <div class="status-container">
    <el-row :gutter="20" justify="center">
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>AI 推理服务 (C++/TensorRT)</span>
              <el-tag :type="cppStatus.status === 'running' ? 'success' : 'danger'">
                {{ cppStatus.status || 'Unknown' }}
              </el-tag>
            </div>
          </template>
          <div class="status-item">
            <span class="label">模型名称:</span>
            <span class="value">{{ cppStatus.model || '-' }}</span>
          </div>
          <div class="status-item">
            <span class="label">运行设备:</span>
            <span class="value">{{ cppStatus.device || '-' }}</span>
          </div>
          <div class="status-item" v-if="cppStatus.error">
             <span class="label">错误信息:</span>
             <span class="value error">{{ cppStatus.error }}</span>
          </div>
          <div class="status-actions">
             <el-button type="primary" size="small" @click="fetchCppStatus" :loading="loading">
               手动刷新
             </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
       <el-col :span="24">
          <el-card>
             <template #header>
                <span>今日数据概览</span>
             </template>
             <div ref="chartRef" style="width: 100%; height: 300px;"></div>
          </el-card>
       </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import request from '@/utils/request'
import * as echarts from 'echarts'

const backendStatus = ref({})
const cppStatus = ref({})
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let timer = null

const fetchBackendStatus = async () => {
  try {
    // 假设后端有个 /health 接口
    const res = await request.get('/health')
    // 注意：axios 响应拦截器可能已经剥离了外层，具体看 request.js 实现
    // 这里假设 res 直接就是后端返回的 JSON 数据
    // 如果后端 /health 返回 { status: 'healthy', database: 'connected', ... }
    backendStatus.value = res 
  } catch (e) {
    backendStatus.value = { database: 'Error', version: 'Error' }
  }
}

const fetchCppStatus = async () => {
  loading.value = true
  try {
    const res = await request.get('/stats/server')
    if (res.code === 200) {
      cppStatus.value = res.data
    } else {
      cppStatus.value = { status: 'error', error: res.msg }
    }
  } catch (e) {
    cppStatus.value = { status: 'offline', error: '无法连接到后端或 C++ 服务未启动' }
  } finally {
    loading.value = false
  }
}

const fetchDashboardStats = async () => {
   try {
      const res = await request.get('/stats/dashboard')
      if (res.code === 200 && res.data) {
         initChart(res.data)
      }
   } catch (e) {
      console.error(e)
   }
}

const initChart = (data) => {
   if (!chartRef.value) return
   
   if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
   }
   
   const option = {
      title: { text: '缺陷类别分布' },
      tooltip: { trigger: 'item' },
      series: [
         {
            name: '缺陷数量',
            type: 'pie',
            radius: '50%',
            data: Object.entries(data.defect_distribution || {}).map(([key, value]) => ({
               name: key,
               value: value
            })),
            emphasis: {
               itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
               }
            }
         }
      ]
   }
   chartInstance.setOption(option)
}

onMounted(() => {
  fetchBackendStatus()
  fetchCppStatus()
  fetchDashboardStats()
  
  // 每 30 秒轮询一次状态
  timer = setInterval(() => {
    fetchBackendStatus()
    fetchCppStatus()
  }, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
.status-container {
  padding: 20px;
}
.status-item {
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 5px;
}
.label {
  font-weight: bold;
  color: #606266;
}
.error {
  color: #f56c6c;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-actions {
   margin-top: 15px;
   text-align: right;
}
</style>
