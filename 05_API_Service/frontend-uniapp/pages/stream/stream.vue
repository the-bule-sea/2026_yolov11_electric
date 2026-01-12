<template>
  <div class="container">
    <!-- 顶部 Tab 切换 -->
    <div class="tab-header">
      <div 
        class="tab-item" 
        :class="{ active: currentTab === 'stream' }" 
        @click="currentTab = 'stream'"
      >实时监控</div>
      <div 
        class="tab-item" 
        :class="{ active: currentTab === 'upload' }" 
        @click="currentTab = 'upload'"
      >视频检测</div>
    </div>

    <!-- 模式 1: 实时监控 -->
    <div v-show="currentTab === 'stream'" class="content-wrapper">
      <div class="video-box">
        <image :src="streamUrl" mode="widthFix" class="video-stream" @error="handleStreamError"></image>
        <div class="status-badge">Live</div>
      </div>
      
      <div class="control-panel">
        <div class="panel-title">监控控制台</div>
        <div class="info-row">
          <text class="label">连接状态:</text>
          <text class="value">在线</text>
        </div>
        <div class="info-row">
          <text class="label">当前源:</text>
          <text class="value">默认摄像头</text>
        </div>
        
        <button class="action-btn primary" @click="refreshStream">刷新视频流</button>
      </div>
    </div>

    <!-- 模式 2: 视频上传检测 -->
    <div v-show="currentTab === 'upload'" class="content-wrapper">
      <div class="upload-section">
        <!-- 未选择视频时显示上传按钮 -->
        <div v-if="!selectedVideoPath && !resultVideoUrl" class="upload-placeholder" @click="chooseVideo">
          <div class="icon-camera">📹</div>
          <div class="text">点击拍摄或选择视频</div>
          <div class="sub-text">支持 MP4, AVI 格式</div>
        </div>

        <!-- 视频预览/结果播放 -->
        <div v-else class="video-preview-box">
          <video 
            id="videoPlayer"
            class="video-player"
            :src="resultVideoUrl || selectedVideoPath" 
            controls 
            autoplay
          ></video>
          <!-- 重新上传按钮 (右上角) -->
          <div class="close-btn" @click="resetVideo">×</div>
        </div>
      </div>

      <div class="control-panel">
        <div class="panel-title">检测控制台</div>
        
        <!-- 检测结果统计 -->
        <div v-if="detectResult" class="result-stats">
          <div class="stat-item">
            <text class="num">{{ detectResult.processed_frames }}</text>
            <text class="desc">总帧数</text>
          </div>
          <div class="stat-item">
            <text class="num">{{ detectResult.total_detections }}</text>
            <text class="desc">检出目标</text>
          </div>
          <div class="stat-item">
            <text class="num">{{ detectResult.average_fps ? detectResult.average_fps.toFixed(1) : '-' }}</text>
            <text class="desc">FPS</text>
          </div>
          <div class="stat-item">
            <text class="num warning">{{ (detectResult.processing_time_seconds || 0).toFixed(1) }}s</text>
            <text class="desc">耗时</text>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <button 
            v-if="selectedVideoPath && !isDetecting && !resultVideoUrl" 
            class="action-btn primary" 
            @click="startDetect"
          >开始检测</button>
          
          <button 
            v-if="isDetecting" 
            class="action-btn primary disabled" 
            disabled
          >检测中...</button>
          
          <button 
            v-if="resultVideoUrl" 
            class="action-btn secondary" 
            @click="resetVideo"
          >重新上传</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
const currentTab = ref('upload'); // 默认进入上传模式(因为是新功能)
const streamUrl = ref('');

// --- 通用配置获取 ---
const getApiHost = () => {
  const host = uni.getStorageSync('api_host') || 'http://127.0.0.1:5000';
  let baseUrl = host;
  if (!baseUrl.startsWith('http')) baseUrl = 'http://' + baseUrl;
  if (baseUrl.endsWith('/api/v1')) baseUrl = baseUrl.replace('/api/v1', '');
  if (baseUrl.endsWith('/')) baseUrl = baseUrl.slice(0, -1);
  return baseUrl;
};

// --- 实时监控逻辑 ---
const initStream = () => {
  const baseUrl = getApiHost();
  streamUrl.value = `${baseUrl}/video_feed`;
};

const refreshStream = () => {
  const baseUrl = getApiHost();
  streamUrl.value = `${baseUrl}/video_feed?t=${new Date().getTime()}`;
};

const handleStreamError = () => {
  // 只有在当前是监控 Tab 时才提示错误，避免初始化加载时的误报
  if (currentTab.value === 'stream') {
    // uni.showToast({ title: '视频流连接失败', icon: 'none' });
  }
};

// 初始化流地址
initStream();


// --- 视频上传逻辑 ---
const selectedVideoPath = ref('');
const resultVideoUrl = ref('');
const isDetecting = ref(false);
const detectResult = ref(null);

const chooseVideo = () => {
  uni.chooseVideo({
    sourceType: ['camera', 'album'],
    compressed: true,
    maxDuration: 60, // 限制60秒
    success: (res) => {
      console.log('Video selected:', res.tempFilePath);
      selectedVideoPath.value = res.tempFilePath;
      // 重置结果
      resultVideoUrl.value = '';
      detectResult.value = null;
    },
    fail: (err) => {
      console.error('Choose video failed:', err);
    }
  });
};

const resetVideo = () => {
  selectedVideoPath.value = '';
  resultVideoUrl.value = '';
  detectResult.value = null;
  isDetecting.value = false;
};

const startDetect = () => {
  if (!selectedVideoPath.value) return;
  
  isDetecting.value = true;
  uni.showLoading({ title: '视频上传检测中...', mask: true });

  const apiHost = uni.getStorageSync('api_host') || 'http://127.0.0.1:5000';
  let uploadUrl = apiHost;
  if (!uploadUrl.startsWith('http')) uploadUrl = 'http://' + uploadUrl;
  if (!uploadUrl.endsWith('/api/v1')) uploadUrl += '/api/v1';
  uploadUrl += '/detect/video';

  uni.uploadFile({
    url: uploadUrl,
    filePath: selectedVideoPath.value,
    name: 'file',
    formData: {
      'model_type': 'v11-nodecode-fp32',
      'conf_threshold': 0.25
    },
    header: {
      'Authorization': `Bearer ${userStore.token}`
    },
    timeout: 300000, // 5分钟超时
    success: (uploadFileRes) => {
      console.log('Upload result:', uploadFileRes.data);
      try {
        const data = JSON.parse(uploadFileRes.data);
        if (data.code === 200) {
          resultVideoUrl.value = data.data.result_oss_url;
          detectResult.value = data.data.processing;
          uni.showToast({ title: '检测完成', icon: 'success' });
        } else {
          uni.showToast({ title: data.msg || '检测失败', icon: 'none' });
        }
      } catch (e) {
        console.error('Parse error:', e);
        uni.showToast({ title: '返回数据解析失败', icon: 'none' });
      }
    },
    fail: (err) => {
      console.error('Upload failed:', err);
      uni.showToast({ title: '请求失败: ' + (err.errMsg || '未知错误'), icon: 'none' });
    },
    complete: () => {
      isDetecting.value = false;
      uni.hideLoading();
    }
  });
};
</script>

<style>
.container {
  min-height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* Tab Header */
.tab-header {
  display: flex;
  background-color: #fff;
  padding: 10px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  z-index: 100;
}
.tab-item {
  flex: 1;
  text-align: center;
  font-size: 16px;
  color: #666;
  padding: 10px 0;
  position: relative;
}
.tab-item.active {
  color: #409EFF;
  font-weight: bold;
}
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 3px;
  background-color: #409EFF;
  border-radius: 3px;
}

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Video Upload Section */
.upload-section {
  width: 100%;
  height: 300px;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.icon-camera {
  font-size: 40px;
  margin-bottom: 10px;
}
.text {
  font-size: 16px;
  margin-bottom: 5px;
}
.sub-text {
  font-size: 12px;
  color: #999;
}
.video-preview-box {
  width: 100%;
  height: 100%;
  position: relative;
}
.video-player {
  width: 100%;
  height: 100%;
}
.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  background-color: rgba(0,0,0,0.5);
  color: #fff;
  border-radius: 50%;
  text-align: center;
  line-height: 28px;
  font-size: 20px;
  z-index: 10;
}

/* Live Stream Styles */
.video-box {
  width: 100%;
  height: 300px;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.video-stream {
  width: 100%;
  height: 100%;
}
.status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: red;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  animation: blink 1s infinite;
}
@keyframes blink { 50% { opacity: 0.5; } }

/* Control Panel */
.control-panel {
  flex: 1;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 20px;
  margin-top: -20px;
  z-index: 10;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
}
.panel-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 20px;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}
.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  padding: 0 10px;
}
.label {
  color: #666;
}
.value {
  color: #333;
  font-weight: 500;
}

/* Result Stats */
.result-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-bottom: 20px;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 10px;
}
.stat-item {
  width: 48%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 15px;
}
.stat-item .num {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}
.stat-item .num.warning {
  color: #E6A23C;
}
.stat-item .desc {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

/* Action Buttons */
.action-buttons {
  margin-top: 20px;
}
.action-btn {
  width: 100%;
  height: 44px;
  line-height: 44px;
  border-radius: 22px;
  font-size: 16px;
  margin-bottom: 15px;
  border: none;
}
.action-btn.primary {
  background: linear-gradient(90deg, #409EFF, #337ECC);
  color: #fff;
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
}
.action-btn.primary.disabled {
  background: #a0cfff;
  box-shadow: none;
  opacity: 0.7;
}
.action-btn.secondary {
  background: #f0f2f5;
  color: #606266;
}
</style>