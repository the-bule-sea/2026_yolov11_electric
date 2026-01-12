<template>
  <div class="container">
    <!-- 列表区域 -->
    <div class="record-list">
      <div class="record-card" v-for="(item, index) in list" :key="index" @click="showDetail(item)">
        <div class="card-left">
          <div v-if="isVideo(item.filename)" class="video-thumb">
            <text class="video-icon">▶</text>
          </div>
          <image v-else :src="item.oss_url" mode="aspectFill" class="thumb-img"></image>
        </div>
        <div class="card-right">
          <div class="filename">{{ item.filename }}</div>
          <div class="time">{{ item.created_at || item.upload_time }}</div>
          <div class="tags">
            <div class="tag error" v-if="item.defect_count > 0">{{ item.defect_count }} 处缺陷</div>
            <div class="tag success" v-else>正常</div>
            <div class="summary" v-if="item.defect_summary">{{ item.defect_summary }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div class="loading-more">
      {{ loading ? '加载中...' : (hasMore ? '上拉加载更多' : '没有更多数据了') }}
    </div>

    <!-- 详情弹窗 (优化版) -->
    <div class="detail-mask" v-if="detailItem" @click.stop="">
        <div class="detail-box">
            <!-- 顶部标题栏 -->
            <div class="detail-header">
                <text class="header-title">记录详情</text>
                <div class="close-icon" @click="closeDetail">×</div>
            </div>
            
            <scroll-view scroll-y class="detail-scroll">
                <!-- 视频播放器 -->
                <video 
                    v-if="isVideo(detailItem.filename)"
                    :src="detailItem.result_oss_url || detailItem.oss_url" 
                    controls
                    class="detail-video"
                ></video>
                <!-- 图片预览 -->
                <image 
                    v-else
                    :src="detailItem.result_oss_url || detailItem.oss_url" 
                    mode="widthFix" 
                    class="detail-img" 
                    @click="previewImage(detailItem.result_oss_url || detailItem.oss_url)"
                ></image>
                
                <div class="detail-info">
                    <div class="info-row">
                        <text class="label">文件名:</text>
                        <text class="val">{{ detailItem.filename }}</text>
                    </div>
                    <div class="info-row">
                        <text class="label">时间:</text>
                        <text class="val">{{ detailItem.created_at }}</text>
                    </div>
                    <div class="info-row">
                        <text class="label">耗时:</text>
                        <text class="val">{{ detailItem.inference_time_ms }} ms</text>
                    </div>
                    
                    <div class="defect-title">缺陷列表:</div>
                    <div class="defect-list-box">
                         <div class="defect-item" v-for="(obj, idx) in parseObjects(detailItem)" :key="idx">
                             <text class="defect-name">{{ obj.label_cn || obj.label }}</text>
                             <text class="defect-conf">{{ obj.confidence }}</text>
                         </div>
                         <div v-if="parseObjects(detailItem).length === 0" class="no-defect">无缺陷详情</div>
                    </div>
                </div>
            </scroll-view>
            
            <!-- 底部大按钮 -->
            <div class="detail-footer">
                <button class="close-btn-large" @click="closeDetail">关闭详情</button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onPullDownRefresh, onReachBottom, onBackPress } from '@dcloudio/uni-app';
import request from '@/utils/request';

const list = ref([]);
const page = ref(1);
const pageSize = 10;
const hasMore = ref(true);
const loading = ref(false);
const detailItem = ref(null);

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位",
  "unknown": "未知"
};

// 监听物理返回键 (只在APP端有效，H5端不支持此生命周期)
onBackPress((e) => {
    if (detailItem.value) {
        detailItem.value = null;
        return true; // 阻止默认返回（即不退出APP）
    }
});

const loadData = async (refresh = false) => {
    if (loading.value) return;
    loading.value = true;
    
    if (refresh) {
        page.value = 1;
        hasMore.value = true;
    }
    
    try {
        const res = await request.get('/records/list', {
            page: page.value,
            page_size: pageSize
        });
        
        if (res.code === 200) {
            const newItems = res.data.list;
            if (refresh) {
                list.value = newItems;
            } else {
                list.value = [...list.value, ...newItems];
            }
            
            if (newItems.length < pageSize) {
                hasMore.value = false;
            } else {
                page.value++;
            }
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
        if (refresh) uni.stopPullDownRefresh();
    }
};

onMounted(() => {
    loadData(true);
});

onPullDownRefresh(() => {
    loadData(true);
});

onReachBottom(() => {
    if (hasMore.value) {
        loadData(false);
    }
});

const showDetail = async (item) => {
    detailItem.value = item;
    // 异步获取完整详情
    try {
        const res = await request.get(`/records/detail/${item.id}`);
        if (res.code === 200) {
            detailItem.value = { ...item, ...res.data };
        }
    } catch(e) {}
};

const closeDetail = () => {
    detailItem.value = null;
};

const parseObjects = (record) => {
  if (!record || !record.objects) return [];
  let objects = record.objects;
  if (typeof objects === 'string') {
    try {
      objects = JSON.parse(objects);
    } catch (e) {
      return [];
    }
  }
  return objects.map(obj => ({
    ...obj,
    label_cn: CLASSES_CN[obj.label] || obj.label
  }));
};

const previewImage = (url) => {
    if(url) uni.previewImage({ urls: [url] });
};

const isVideo = (filename) => {
    if (!filename) return false;
    return /\.(mp4|avi|mov|mkv)$/i.test(filename);
};
</script>

<style>
.container { min-height: 100vh; background: #f5f7fa; padding-bottom: 20px; }
.record-list { padding: 10px; }
.record-card {
    background: #fff;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 10px;
    display: flex;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.card-left { width: 80px; height: 80px; margin-right: 10px; position: relative; }
.thumb-img { width: 100%; height: 100%; border-radius: 4px; background: #eee; }
.video-thumb { 
    width: 100%; height: 100%; 
    border-radius: 4px; 
    background: #000; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
}
.video-icon { color: #fff; font-size: 24px; }

.card-right { flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
.filename { font-size: 14px; font-weight: bold; color: #333; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.time { font-size: 12px; color: #999; }
.tags { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.tag { font-size: 10px; padding: 2px 5px; border-radius: 3px; }
.tag.error { background: #fef0f0; color: #f56c6c; border: 1px solid #fde2e2; }
.tag.success { background: #f0f9eb; color: #67c23a; border: 1px solid #e1f3d8; }
.summary { font-size: 11px; color: #666; margin-left: 5px; }

.loading-more { text-align: center; padding: 15px; color: #999; font-size: 13px; }

/* 弹窗样式 */
.detail-mask {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.6);
    z-index: 999;
    display: flex;
    justify-content: center;
    align-items: center;
}
.detail-box {
    width: 90%;
    height: 80%;
    background: #fff;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.detail-header {
    height: 50px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 15px;
    border-bottom: 1px solid #eee;
    background: #fff;
}
.header-title { font-size: 16px; font-weight: bold; }
.close-icon { font-size: 24px; color: #999; padding: 0 10px; }

.detail-scroll { flex: 1; padding: 15px; box-sizing: border-box; }
.detail-img { width: 100%; border-radius: 4px; margin-bottom: 15px; background: #000; }
.detail-video { width: 100%; height: 240px; border-radius: 4px; margin-bottom: 15px; background: #000; }

.info-row { display: flex; margin-bottom: 8px; font-size: 14px; }
.info-row .label { color: #999; width: 60px; }
.info-row .val { flex: 1; word-break: break-all; }

.defect-title { font-weight: bold; margin: 15px 0 10px; padding-left: 8px; border-left: 3px solid #409EFF; }
.defect-item { display: flex; justify-content: space-between; border-bottom: 1px solid #f0f0f0; padding: 8px 0; font-size: 14px; }
.defect-conf { color: #999; font-size: 12px; }
.no-defect { text-align: center; color: #999; font-size: 14px; padding: 10px 0; }

.detail-footer {
    padding: 15px;
    border-top: 1px solid #eee;
    background: #fff;
}
.close-btn-large {
    background: #f5f7fa;
    color: #606266;
    border: none;
    border-radius: 20px;
    font-size: 14px;
}
.close-btn-large:active { background: #e4e7ed; }
</style>
