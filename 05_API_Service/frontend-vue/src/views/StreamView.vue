<template>
  <div class="video-detect-container">
    <el-row :gutter="20">
      <!-- 左侧：视频上传 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>视频上传与检测</span>
            </div>
          </template>
          
          <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
            accept=".mp4,.avi"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽视频文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 mp4/avi 格式，文件大小不超过 500MB
              </div>
            </template>
          </el-upload>

          <div v-if="videoFile" class="file-info">
            <el-alert :title="`已选择文件: ${videoFile.name}`" type="info" :closable="false" show-icon />
          </div>

          <div class="controls">
            <el-form :inline="true" size="default">
              <el-form-item label="模型类型">
                <el-select v-model="modelType" placeholder="选择模型" style="width: 180px">
                  <el-option
                    v-for="item in modelOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
            </el-form>
            
            <div class="action-btn">
              <el-button type="primary" size="large" @click="handleDetect" :loading="loading" :disabled="!videoFile">
                开始视频分析
              </el-button>
            </div>
          </div>
          
          <!-- 进度提示 -->
          <div v-if="loading" class="progress-info">
            <el-alert title="视频处理中，请耐心等待... (处理耗时取决于视频长度和GPU性能)" type="warning" :closable="false" show-icon />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：结果展示 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>检测结果回放</span>
            </div>
          </template>
          
          <div class="video-container">
            <video 
              v-if="resultVideoUrl" 
              :src="resultVideoUrl" 
              controls 
              autoplay 
              loop
              class="result-video"
            ></video>
            <div v-else class="empty-state">
              <el-empty description="暂无检测结果" />
            </div>
          </div>

          <div v-if="processingInfo" class="result-stats">
            <el-descriptions title="检测统计" :column="2" border>
              <el-descriptions-item label="处理帧数">{{ processingInfo.processed_frames }}</el-descriptions-item>
              <el-descriptions-item label="平均 FPS">{{ processingInfo.average_fps ? processingInfo.average_fps.toFixed(1) : '-' }}</el-descriptions-item>
              <el-descriptions-item label="处理耗时">{{ processingInfo.processing_time_seconds ? processingInfo.processing_time_seconds.toFixed(2) : '-' }} 秒</el-descriptions-item>
              <el-descriptions-item label="总检出目标">{{ processingInfo.total_detections }}</el-descriptions-item>
            </el-descriptions>
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
import request from '@/utils/request'

const videoFile = ref(null)
const resultVideoUrl = ref('')
const loading = ref(false)
const processingInfo = ref(null)

const modelType = ref('v11-nodecode-fp32')
const confThreshold = ref(0.25)

const modelOptions = [
  { value: '4060-v3-n-fp32', label: 'YOLOv11 nano FP32' },
]

const handleFileChange = (uploadFile) => {
  const isVideo = ['video/mp4', 'video/x-msvideo', 'video/avi'].includes(uploadFile.raw.type) || 
                  /\.(mp4|avi)$/i.test(uploadFile.name);
                  
  if (!isVideo) {
    ElMessage.error('请上传 MP4 或 AVI 格式的视频文件')
    return
  }
  
  if (uploadFile.size / 1024 / 1024 > 500) {
    ElMessage.error('视频大小不能超过 500MB')
    return
  }
  
  videoFile.value = uploadFile.raw
  resultVideoUrl.value = ''
  processingInfo.value = null
}

const handleDetect = async () => {
  if (!videoFile.value) return
  
  loading.value = true
  resultVideoUrl.value = ''
  processingInfo.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', videoFile.value)
    formData.append('model_type', modelType.value)
    formData.append('conf_threshold', confThreshold.value)
    
    // 增加超时时间，视频处理较慢
    const res = await request.post('/detect/video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000 // 5分钟超时
    })
    
    if (res.code === 200) {
      ElMessage.success('视频检测完成')
      resultVideoUrl.value = res.data.result_oss_url
      processingInfo.value = res.data.processing
    } else {
      ElMessage.error(res.msg || '检测失败')
    }
  } catch (error) {
    console.error(error)
    // 区分超时错误
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
       ElMessage.error('请求超时，可能视频过长，请尝试较短的视频')
    } else {
       ElMessage.error('网络请求异常')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.video-detect-container {
  padding: 20px;
}
.box-card {
  height: 100%;
  min-height: 600px;
}
.upload-demo {
  margin-bottom: 20px;
}
.file-info {
  margin-bottom: 20px;
}
.controls {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
.action-btn {
  margin-top: 20px;
  text-align: center;
}
.progress-info {
  margin-top: 20px;
}
.video-container {
  width: 100%;
  height: 400px;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
}
.result-video {
  max-width: 100%;
  max-height: 100%;
}
.empty-state {
  color: #909399;
}
.result-stats {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
