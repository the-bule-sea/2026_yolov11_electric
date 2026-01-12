<template>
  <div class="system-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>今日缺陷统计</span>
        </div>
      </template>
      
      <div id="chart" style="width: 100%; height: 400px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const chartInstance = ref(null)

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位",
  "unknown": "未知"
}

const initChart = (data) => {
  const chartDom = document.getElementById('chart')
  chartInstance.value = echarts.init(chartDom)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: data.map(item => item.name),
        axisTick: { alignWithLabel: true }
      }
    ],
    yAxis: [
      {
        type: 'value'
      }
    ],
    series: [
      {
        name: '缺陷数量',
        type: 'bar',
        barWidth: '60%',
        data: data.map(item => item.value),
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  }
  
  chartInstance.value.setOption(option)
}

const fetchData = async () => {
  try {
    const res = await axios.get('/api/v1/stats/dashboard', {
      headers: { 'Authorization': `Bearer ${userStore.token}` }
    })
    
    if (res.data.code === 200) {
      const dist = res.data.data.defect_distribution || {}
      const chartData = Object.entries(dist).map(([key, value]) => ({
        name: CLASSES_CN[key] || key,
        value
      }))
      initChart(chartData)
    } else {
      ElMessage.error(res.data.msg || '获取数据失败')
    }
  } catch (error) {
    ElMessage.error('连接服务器失败')
  }
}

onMounted(() => {
  fetchData()
  
  window.addEventListener('resize', () => {
    chartInstance.value?.resize()
  })
})
</script>

<style scoped>
.system-container {
  padding: 20px;
}
</style>
