<template>
  <div class="home-container">
    <el-tabs v-model="activeTab" class="demo-tabs">
      <el-tab-pane label="单帧检测" name="single">
        <!-- 单帧检测内容 -->
        <el-row :gutter="20">
          <el-col :span="10">
            <el-card class="upload-card">
              <template #header>
                <div class="card-header">
                  <span>图片上传</span>
                </div>
              </template>
              
              <el-upload
                class="upload-demo"
                drag
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :show-file-list="false"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    只能上传 jpg/png 文件，且不超过 5MB
                  </div>
                </template>
              </el-upload>
              
              <div class="controls" style="margin-top: 20px;">
                <el-form label-position="top" size="small">
                  <el-row :gutter="10">
                    <el-col :span="14">
                      <el-form-item label="模型类型">
                        <el-select v-model="modelType" placeholder="选择模型" style="width: 100%">
                           <el-option
                             v-for="item in modelOptions"
                             :key="item.value"
                             :label="item.label"
                             :value="item.value"
                           />
                        </el-select>
                      </el-form-item>
                    </el-col>
                    
                  </el-row>
                </el-form>
              </div>

              <div v-if="imageUrl" class="preview-container">
                <el-image 
                  :src="imageUrl" 
                  fit="contain" 
                  class="preview-image"
                />
              </div>
              
              <div class="upload-actions">
                <el-button type="primary" @click="handleDetect" :loading="loading" :disabled="!file">
                  开始检测
                </el-button>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="14">
            <el-card class="result-card">
              <template #header>
                <div class="card-header">
                  <span>检测结果</span>
                </div>
              </template>
              
              <div v-if="resultImage" class="result-image-container">
                <el-image 
                  :src="resultImage" 
                  fit="contain"
                  class="result-image" 
                  :preview-src-list="[resultImage]"
                />
              </div>
              
              <div v-if="detectResult" class="result-info">
                <el-descriptions title="检测详情" :column="2" border>
                  <el-descriptions-item label="检测耗时">{{ detectResult.inference_time_ms }} ms</el-descriptions-item>
                  <el-descriptions-item label="缺陷数量">{{ detectResult.defect_count }}</el-descriptions-item>
                </el-descriptions>
                
                <el-table :data="detectResult.objects" style="width: 100%; margin-top: 20px" height="250">
                  <el-table-column prop="label" label="类别" />
                  <el-table-column prop="confidence" label="置信度" />
                  <el-table-column prop="bbox" label="坐标 (x1, y1, x2, y2)">
                     <template #default="scope">
                        {{ scope.row.bbox.map(n => Math.round(n)).join(', ') }}
                     </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-else class="empty-state">
                <el-empty description="暂无检测结果" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="批量检测" name="batch">
        <!-- 批量检测内容 -->
        <el-card class="batch-card">
          <template #header>
            <div class="card-header">
              <span>批量上传与检测 (最多20张)</span>
              <el-button type="primary" @click="handleBatchDetect" :loading="batchLoading" :disabled="batchFileList.length === 0">
                开始批量检测
              </el-button>
            </div>
          </template>
          
          <el-upload
            class="upload-demo"
            drag
            multiple
            action="#"
            :auto-upload="false"
            :on-change="handleBatchFileChange"
            :on-remove="handleBatchRemove"
            :file-list="batchFileList"
            list-type="picture"
            accept=".jpg,.jpeg,.png,.bmp"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽多个文件到此处或 <em>点击上传</em>
            </div>
          </el-upload>

          <el-divider content-position="left">检测结果列表</el-divider>

          <div v-if="batchResults.length > 0" class="batch-results">
            <el-table :data="batchResults" style="width: 100%" v-loading="batchLoading">
              <el-table-column prop="filename" label="文件名" width="180" />
              <el-table-column label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                    {{ scope.row.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="预览" width="120">
                 <template #default="scope">
                    <el-image 
                       v-if="scope.row.result_oss_url"
                       style="width: 50px; height: 50px"
                       :src="scope.row.result_oss_url"
                       :preview-src-list="[scope.row.result_oss_url]"
                       fit="cover"
                    />
                 </template>
              </el-table-column>
              <el-table-column prop="defect_count" label="缺陷数" width="100" />
              <el-table-column label="详情" min-width="200">
                <template #default="scope">
                   <div v-if="scope.row.objects && scope.row.objects.length">
                      <el-tag v-for="(obj, idx) in scope.row.objects" :key="idx" size="small" style="margin-right: 5px">
                         {{ obj.label }} ({{ obj.confidence }})
                      </el-tag>
                   </div>
                   <span v-else-if="scope.row.status === 'success'">无缺陷</span>
                   <span v-else>{{ scope.row.error }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

// 通用状态
const activeTab = ref('single')

// --- 单帧检测逻辑 ---
const file = ref(null)
const imageUrl = ref('')
const resultImage = ref('')
const loading = ref(false)
const detectResult = ref(null)

const modelType = ref('v11-nodecode-fp32')
const confThreshold = ref(0.25)

const modelOptions = [
  { value: 'v11-nodecode-fp32', label: 'YOLOv11 NoEncode FP32 (推荐)' },
  { value: 'v11-nodecode-int8', label: 'YOLOv11 NoEncode INT8 (快速)' },
  { value: 'v11-fp32', label: 'YOLOv11 FP32' },
  { value: 'v11-int8', label: 'YOLOv11 INT8' }
]

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  // 清空上次结果
  resultImage.value = ''
  detectResult.value = null
}

const handleDetect = async () => {
  if (!file.value) return
  
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('model_type', modelType.value)
    formData.append('conf_threshold', confThreshold.value)
    
    // 注意：request.post 封装了 axios，如果返回结构是 res.data，这里直接拿到 res
    // 假设 request.js 里直接返回 response.data
    const res = await request.post('/detect/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.code === 200) {
      detectResult.value = res.data
      resultImage.value = res.data.result_oss_url
      ElMessage.success('检测完成')
    } else {
      ElMessage.error(res.msg || '检测失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('网络请求失败')
  } finally {
    loading.value = false
  }
}

// --- 批量检测逻辑 ---
const batchFileList = ref([])
const batchLoading = ref(false)
const batchResults = ref([])

const handleBatchFileChange = (uploadFile, uploadFiles) => {
  // 限制最多 20 张
  if (uploadFiles.length > 20) {
    ElMessage.warning('最多只能上传 20 张图片')
    // 截取前20张
    batchFileList.value = uploadFiles.slice(-20)
  } else {
    batchFileList.value = uploadFiles
  }
}

const handleBatchRemove = (uploadFile, uploadFiles) => {
  batchFileList.value = uploadFiles
}

const handleBatchDetect = async () => {
  if (batchFileList.value.length === 0) return
  
  batchLoading.value = true
  batchResults.value = [] // 清空旧结果
  
  try {
    const formData = new FormData()
    batchFileList.value.forEach(fileItem => {
      formData.append('files', fileItem.raw)
    })
    formData.append('model_type', 'v11-nodecode-fp32')
    
    const res = await request.post('/detect/batch', formData, {
       headers: { 'Content-Type': 'multipart/form-data' },
       timeout: 60000 // 批量检测可能耗时较长
    })
    
    if (res.code === 200) {
       batchResults.value = res.data.results
       ElMessage.success(`批量检测完成，成功 ${res.data.success} 张`)
    } else {
       ElMessage.error(res.msg || '批量检测失败')
    }
  } catch (error) {
     console.error(error)
     ElMessage.error('批量检测请求异常')
  } finally {
     batchLoading.value = false
  }
}
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.upload-card, .result-card, .batch-card {
  height: 100%;
  min-height: 500px;
}

.preview-container, .result-image-container {
  margin-top: 20px;
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.preview-image, .result-image {
  max-width: 100%;
  max-height: 100%;
}

.upload-actions {
  margin-top: 20px;
  text-align: center;
}

.result-info {
  margin-top: 20px;
}

.empty-state {
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.demo-tabs > .el-tabs__content {
  padding: 32px;
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;
}
</style>
