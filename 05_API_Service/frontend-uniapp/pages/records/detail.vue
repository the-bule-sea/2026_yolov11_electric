<template>
  <div class="container">
    <div class="image-box">
      <image 
        :src="record.result_oss_url || record.oss_url" 
        mode="widthFix" 
        class="detail-img" 
        @click="previewImage(record.result_oss_url || record.oss_url)"
      ></image>
    </div>
    
    <div class="info-card">
      <div class="card-title">基本信息</div>
      <div class="info-row">
        <text class="label">文件名</text>
        <text class="val">{{ record.filename }}</text>
      </div>
      <div class="info-row">
        <text class="label">检测时间</text>
        <text class="val">{{ record.created_at || record.upload_time }}</text>
      </div>
      <div class="info-row">
        <text class="label">推理耗时</text>
        <text class="val">{{ record.inference_time_ms }} ms</text>
      </div>
    </div>
    
    <div class="info-card">
      <div class="card-title">缺陷详情 ({{ objects.length }})</div>
      <div class="defect-list">
        <div class="defect-item" v-for="(obj, idx) in objects" :key="idx">
          <div class="defect-left">
            <div class="defect-name">{{ obj.label_cn || obj.label }}</div>
            <div class="defect-conf">置信度: {{ (obj.confidence * 100).toFixed(1) }}%</div>
          </div>
          <!-- 如果有坐标信息，也可以显示 -->
        </div>
        <div v-if="objects.length === 0" class="no-defect">
          <text>图像正常，无明显缺陷</text>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import request from '@/utils/request';

const record = ref({});
const objects = ref([]);

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位",
  "unknown": "未知"
};

onLoad(async (options) => {
  if (options.id) {
    // 先显示列表传过来的简单数据（如果有）
    if (options.data) {
        try {
            const data = JSON.parse(decodeURIComponent(options.data));
            record.value = data;
            parseObjects(data);
        } catch(e) {}
    }
    
    // 异步获取完整详情
    try {
        const res = await request.get(`/records/detail/${options.id}`);
        if (res.code === 200) {
            record.value = { ...record.value, ...res.data };
            parseObjects(record.value);
        }
    } catch (e) {
        console.error(e);
    }
  }
});

const parseObjects = (rec) => {
    if (!rec || !rec.objects) return;
    let objs = rec.objects;
    if (typeof objs === 'string') {
        try { objs = JSON.parse(objs); } catch (e) { objs = []; }
    }
    objects.value = objs.map(obj => ({
        ...obj,
        label_cn: CLASSES_CN[obj.label] || obj.label
    }));
};

const previewImage = (url) => {
    if(url) uni.previewImage({ urls: [url] });
};
</script>

<style>
.container { min-height: 100vh; background: #f5f7fa; padding-bottom: 30px; }
.image-box { background: #000; display: flex; justify-content: center; align-items: center; min-height: 250px; }
.detail-img { width: 100%; }

.info-card { background: #fff; margin: 15px; border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; padding-left: 8px; border-left: 4px solid #409EFF; }

.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f9f9f9; font-size: 14px; }
.info-row:last-child { border: none; }
.label { color: #999; }
.val { color: #333; font-weight: 500; }

.defect-item { background: #f9fcff; border: 1px solid #e0eeff; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
.defect-name { font-weight: bold; color: #333; font-size: 15px; }
.defect-conf { color: #666; font-size: 12px; margin-top: 4px; }
.no-defect { text-align: center; color: #999; padding: 20px 0; font-size: 14px; }
</style>
