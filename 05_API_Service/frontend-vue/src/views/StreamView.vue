<template>
  <div class="stream-container">
    <el-alert
      title="功能开发中"
      type="warning"
      description="当前后端版本仅支持单帧图片检测 API，实时流功能待接入 WebSocket 服务。"
      show-icon
      :closable="false"
      style="margin-bottom: 20px;"
    />
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>摄像头源</span>
            </div>
          </template>
          <div class="video-placeholder">
            <el-icon :size="50"><VideoCamera /></el-icon>
            <p>等待接入...</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实时检测结果</span>
            </div>
          </template>
          <div class="video-placeholder">
            <el-icon :size="50"><VideoCamera /></el-icon>
            <p>等待接入...</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { VideoCamera } from '@element-plus/icons-vue'
</script>

<style scoped>
.video-placeholder {
  height: 400px;
  background-color: #000;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
}
</style>
