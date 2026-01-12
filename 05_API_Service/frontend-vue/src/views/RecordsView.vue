<template>
  <div class="records-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>历史检测记录</span>
          <div class="header-right">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              @change="fetchData"
              style="margin-right: 10px;"
            />
            <el-button type="primary" @click="fetchData">刷新</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="tableData" style="width: 100%" v-loading="loading">
        <el-table-column prop="filename" label="文件名" width="180" />
        <el-table-column label="预览图" width="120">
          <template #default="scope">
            <el-image 
              style="width: 50px; height: 50px"
              :src="scope.row.oss_url"
              :preview-src-list="[scope.row.oss_url]"
              fit="cover"
            />
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="检测时间" width="180" />
        <el-table-column prop="defect_summary" label="检测结果" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="handleViewDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="检测详情" width="50%">
      <div v-if="currentRecord" class="detail-content">
        <el-image :src="currentRecord.result_oss_url || currentRecord.oss_url" class="detail-image" />
        <div class="detail-info">
          <p><strong>文件名:</strong> {{ currentRecord.filename }}</p>
          <p><strong>检测时间:</strong> {{ currentRecord.upload_time }}</p>
          <p><strong>耗时:</strong> {{ currentRecord.inference_time_ms }} ms</p>
          <p><strong>缺陷摘要:</strong> {{ currentRecord.defect_summary || '无' }}</p>
          <h4>缺陷详情列表:</h4>
          <ul v-if="parseObjects(currentRecord).length > 0">
            <li v-for="(obj, index) in parseObjects(currentRecord)" :key="index">
              {{ obj.label_cn || obj.label }} (置信度: {{ obj.confidence }})
            </li>
          </ul>
          <p v-else style="color: #909399; font-style: italic;">无详细检测对象数据</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dateRange = ref([])

const detailVisible = ref(false)
const currentRecord = ref(null)

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位",
  "unknown": "未知"
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_start = dateRange.value[0]
      params.date_end = dateRange.value[1]
    }
    
    const res = await request.get('/records/list', { params })
    if (res.code === 200) {
      tableData.value = res.data.list
      total.value = res.data.total
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const parseObjects = (record) => {
  if (!record || !record.objects) return []
  // 如果后端返回的是 JSON 字符串，需要解析
  let objects = record.objects
  if (typeof objects === 'string') {
    try {
      objects = JSON.parse(objects)
    } catch (e) {
      return []
    }
  }
  return objects.map(obj => ({
    ...obj,
    label_cn: CLASSES_CN[obj.label] || obj.label
  }))
}

const handleViewDetail = async (row) => {
  // 先展示现有数据
  currentRecord.value = row
  detailVisible.value = true
  
  // 异步获取完整详情（包含 objects 数据）
  try {
    const res = await request.get(`/records/detail/${row.id}`)
    if (res.code === 200) {
      currentRecord.value = res.data
    }
  } catch (error) {
    console.error("获取记录详情失败", error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.detail-content {
  display: flex;
  gap: 20px;
}

.detail-image {
  flex: 1;
  max-width: 60%;
}

.detail-info {
  flex: 1;
}
</style>
