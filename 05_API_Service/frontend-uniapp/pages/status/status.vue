<template>
  <div class="container">
    <!-- C++ 推理状态 -->
    <div class="card status-card">
        <div class="card-header">
            <text class="title">推理引擎 (C++/TRT)</text>
            <text class="badge" :class="cppStatus.status === 'running' ? 'success' : 'error'">
                {{ cppStatus.status || 'Unknown' }}
            </text>
        </div>
        <div class="row">
            <text class="label">模型</text>
            <text class="val">{{ cppStatus.model || '-' }}</text>
        </div>
        <div class="row">
            <text class="label">设备</text>
            <text class="val">{{ cppStatus.device || '-' }}</text>
        </div>
        <div v-if="cppStatus.error" class="error-msg">{{ cppStatus.error }}</div>
        
        <button class="refresh-mini" @click="fetchStatus" :loading="loading">刷新状态</button>
    </div>

    <!-- 数据统计 (代替 ECharts) -->
    <div class="card stats-card">
        <div class="card-header">
            <text class="title">今日检测概览</text>
        </div>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="num">{{ statsData.today_check_count || 0 }}</div>
                <div class="txt">检测总数</div>
            </div>
            <div class="stat-box">
                <div class="num warning">{{ statsData.total_defects || 0 }}</div>
                <div class="txt">发现缺陷</div>
            </div>
        </div>
        
        <div class="chart-list">
            <div class="chart-title">缺陷分布</div>
            <div class="bar-item" v-for="(val, key) in statsData.defect_distribution" :key="key">
                <div class="bar-label">{{ CLASSES_CN[key] || key }}</div>
                <div class="bar-track">
                    <div class="bar-fill" :style="{ width: getPercent(val) + '%' }"></div>
                </div>
                <div class="bar-num">{{ val }}</div>
            </div>
            <div v-if="!statsData.defect_distribution || Object.keys(statsData.defect_distribution).length === 0" class="no-data">
                今日暂无缺陷数据
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onPullDownRefresh } from '@dcloudio/uni-app';
import request from '@/utils/request';

const loading = ref(false);
const cppStatus = ref({});
const statsData = ref({});

const CLASSES_CN = {
  "insulator_broken": "绝缘子破损",
  "insulator_burn": "绝缘子烧蚀",
  "nest": "鸟巢",
  "ring_shifted": "均压环移位"
};

const fetchStatus = async () => {
    loading.value = true;
    try {
        // 1. C++ 状态
        const resCpp = await request.get('/stats/server');
        if (resCpp.code === 200) {
            cppStatus.value = resCpp.data;
        } else {
            cppStatus.value = { status: 'error', error: resCpp.msg };
        }
        
        // 3. 统计数据
        const resStats = await request.get('/stats/dashboard');
        if (resStats.code === 200) {
            statsData.value = resStats.data;
        }
        
    } catch(e) {
        console.error(e);
    } finally {
        loading.value = false;
        uni.stopPullDownRefresh();
    }
};

const getPercent = (val) => {
    const total = statsData.value.total_defects || 1;
    return Math.min((val / total) * 100, 100);
};

onMounted(() => {
    fetchStatus();
});

onPullDownRefresh(() => {
    fetchStatus();
});
</script>

<style>
.container { padding: 15px; background: #f5f7fa; min-height: 100vh; }
.card { background: #fff; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
.title { font-weight: bold; font-size: 16px; color: #333; }
.badge { font-size: 12px; padding: 2px 6px; border-radius: 4px; background: #eee; color: #666; }
.badge.success { background: #e1f3d8; color: #67c23a; }
.badge.error { background: #fef0f0; color: #f56c6c; }

.row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
.label { color: #666; }
.val { font-weight: 500; }
.error-msg { color: #f56c6c; font-size: 12px; margin-top: 5px; }

.refresh-mini { margin-top: 10px; font-size: 12px; background: #f0f9eb; color: #67c23a; border: 1px solid #e1f3d8; }

.stats-grid { display: flex; text-align: center; margin-bottom: 20px; }
.stat-box { flex: 1; border-right: 1px solid #eee; }
.stat-box:last-child { border: none; }
.num { font-size: 24px; font-weight: bold; color: #409EFF; }
.num.warning { color: #E6A23C; }
.txt { font-size: 12px; color: #999; margin-top: 5px; }

.chart-title { font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #666; }
.bar-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 12px; }
.bar-label { width: 70px; color: #666; }
.bar-track { flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; margin: 0 10px; overflow: hidden; }
.bar-fill { height: 100%; background: #409EFF; border-radius: 4px; }
.bar-num { width: 30px; text-align: right; color: #666; }
.no-data { text-align: center; color: #ccc; font-size: 12px; padding: 20px 0; }
</style>
