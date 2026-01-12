<template>
  <div class="home-container">
    <el-row :gutter="20">
      <!-- 左侧：图片上传与展示 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>上传巡检图像</span>
            </div>
          </template>
          
          <div class="upload-area">
            <el-upload
              class="image-uploader"
              drag
              action=""
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
            >
              <img v-if="imageUrl" :src="imageUrl" class="uploaded-image" />
              <div v-else class="el-upload__text">
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或 <em>点击上传</em>
                </div>
              </div>
            </el-upload>
          </div>

          <div class="controls">
            <el-row :gutter="10" align="middle">
              <el-col :span="12">
                <span>置信度阈值：</span>
                <el-slider v-model="confThreshold" :min="0.1" :max="0.9" :step="0.05" show-input />
              </el-col>
              <el-col :span="12" style="text-align: right;">
                <el-button type="primary" @click="handleAnalyze" :loading="loading" :disabled="!file">
                  开始分析
                </el-button>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：检测结果展示 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>检测结果可视化</span>
            </div>
          </template>
          
          <div class="result-area">
            <img v-if="resultImageUrl" :src="resultImageUrl" class="result-image" />
            <div v-else class="empty-result">
              <el-empty description="暂无检测结果" />
            </div>
          </div>

          <div class="json-result" v-if="resultData.length > 0">
            <h4>详细检测数据 (JSON)</h4>
            <pre>{{ JSON.stringify(resultData, null, 2) }}</pre>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const file = ref(null)
const imageUrl = ref('')
const resultImageUrl = ref('')
const resultData = ref([])
const loading = ref(false)
const confThreshold = ref(0.25)

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位",
  "unknown": "未知"
}

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  // 清空上次结果
  resultImageUrl.value = ''
  resultData.value = []
}

const handleAnalyze = async () => {
  if (!file.value) return
  
  loading.value = true
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('conf_threshold', confThreshold.value)
  
  try {
    const res = await axios.post('/api/v1/detect/image', formData, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.data.code === 200) {
      const data = res.data.data
      resultData.value = data.objects.map(obj => ({
        ...obj,
        label_cn: CLASSES_CN[obj.label] || obj.label
      }))
      
      // 处理结果图片 URL (如果是相对路径需要拼接，如果是 OSS 绝对路径直接用)
      // 这里假设后端返回的是 OSS 的 URL，或者我们通过 API 代理访问
      resultImageUrl.value = data.result_oss_url
      ElMessage.success('检测完成')
    } else {
      ElMessage.error(res.data.msg || '检测失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '连接服务器失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload-area, .result-area {
  height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
  background-color: #fafafa;
}

.uploaded-image, .result-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-uploader {
  width: 100%;
  height: 100%;
}

.controls {
  margin-top: 20px;
}

.json-result {
  margin-top: 20px;
  padding: 10px;
  background-color: #f4f4f5;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

pre {
  margin: 0;
  font-family: monospace;
  font-size: 12px;
}
</style>
