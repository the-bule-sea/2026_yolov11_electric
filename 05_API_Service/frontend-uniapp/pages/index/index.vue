<template>
  <div class="container">
    <!-- 顶部状态栏 -->
    <div class="nav-bar">
      <div class="user-info">Hi, {{ userStore.userInfo.username || '用户' }}</div>
      <div class="logout-btn" @click="handleLogout">
        <text class="logout-icon">⏻</text> 退出
      </div>
    </div>

    <div class="content">
      <!-- 选图区域 -->
      <div class="upload-area" @click="handleChooseImage">
        <div v-if="!imagePath" class="placeholder">
          <div class="icon">+</div>
          <div class="text">点击拍摄/选择图片</div>
        </div>
        <image v-else :src="imagePath" class="preview-img" mode="aspectFit"></image>
      </div>

      <!-- 操作按钮 -->
      <div class="btn-group">
          <button class="action-btn" @click="handleDetect" :disabled="!imagePath || loading" :class="{ disabled: !imagePath }" v-if="!result">
            {{ loading ? '检测中...' : '开始检测' }}
          </button>
          
          <button class="action-btn secondary" @click="clearResult" v-if="result">
            重新检测
          </button>
      </div>

      <!-- 检测结果 -->
      <div class="result-box" v-if="result">
        <div class="section-title">检测结果</div>
        
        <!-- 结果图 -->
        <img :src="result.result_oss_url" class="result-img" mode="widthFix" @click="previewImage(result.result_oss_url)" />
        
        <!-- 数据概览 -->
        <div class="stats-row">
          <div class="stat-item">
            <div class="num">{{ result.defect_count }}</div>
            <div class="label">缺陷数</div>
          </div>
          <div class="stat-item">
            <div class="num">{{ result.inference_time_ms }}ms</div>
            <div class="label">耗时</div>
          </div>
        </div>

        <!-- 详细列表 -->
        <div class="detail-list">
          <div class="detail-item" v-for="(obj, index) in result.objects" :key="index">
            <div class="tag">{{ obj.label }}</div>
            <div class="conf">置信度: {{ obj.confidence }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useUserStore } from '@/stores/user';
import request from '@/utils/request';

const userStore = useUserStore();
const imagePath = ref('');
const loading = ref(false);
const result = ref(null);

// 1. 选择图片
const handleChooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      imagePath.value = res.tempFilePaths[0];
      // 清空上次结果
      result.value = null;
    }
  });
};

// 2. 上传并检测
const handleDetect = async () => {
  if (!imagePath.value) return;
  
  loading.value = true;
  try {
    // 使用封装好的 upload 方法
    const res = await request.upload('/detect/image', imagePath.value, {
      model_type: 'v11-nodecode-fp32'
    });
    
    if (res.code === 200) {
      result.value = res.data;
      uni.showToast({ title: '检测完成' });
    } else {
      uni.showToast({ title: res.msg || '检测失败', icon: 'none' });
    }
  } catch (e) {
    console.error(e);
    uni.showToast({ title: '上传失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

// 3. 预览大图
const previewImage = (url) => {
  uni.previewImage({
    urls: [url]
  });
};

const clearResult = () => {
    imagePath.value = '';
    result.value = null;
};

const handleLogout = () => {
  userStore.logout();
  uni.reLaunch({ url: '/pages/login/login' });
};
</script>

<style>
.container {
  min-height: 100vh;
  background-color: #f8f8f8;
}
.nav-bar {
  height: 50px;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.user-info { font-weight: bold; font-size: 16px; color: #333; }
.logout-btn { 
    display: flex; 
    align-items: center; 
    color: #f56c6c; 
    font-size: 14px; 
    padding: 5px 10px;
    background: #fef0f0;
    border-radius: 15px;
}
.logout-icon { margin-right: 4px; font-size: 12px; }

.content { padding: 15px; }

.upload-area {
  height: 200px;
  background: #fff;
  border-radius: 8px;
  border: 2px dashed #ddd;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
}
.placeholder { text-align: center; color: #999; }
.icon { font-size: 40px; margin-bottom: 10px; }
.preview-img { width: 100%; height: 100%; object-fit: contain; }

.action-btn {
  margin-top: 20px;
  background-color: #409EFF;
  color: #fff;
  border-radius: 25px;
  width: 100%;
}
.action-btn.disabled { background-color: #a0cfff; }
.action-btn.secondary { background-color: #fff; color: #606266; border: 1px solid #dcdfe6; }

.btn-group { display: flex; gap: 10px; }

.result-box {
  margin-top: 20px;
  background: #fff;
  border-radius: 8px;
  padding: 15px;
}
.section-title { font-weight: bold; margin-bottom: 10px; border-left: 4px solid #409EFF; padding-left: 10px; }
.result-img { width: 100%; border-radius: 4px; margin-bottom: 10px; }

.stats-row { display: flex; text-align: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
.stat-item { flex: 1; }
.num { font-size: 18px; font-weight: bold; color: #333; }
.label { font-size: 12px; color: #999; }

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.tag { background: #ecf5ff; color: #409EFF; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.conf { font-size: 12px; color: #666; }
</style>
