<template>
  <div class="container">
    <div class="header">
      <div class="title">电力巡检系统</div>
      <div class="subtitle">Mobile Client</div>
    </div>
    
    <div class="form-box">
      <!-- 登录/注册切换 -->
      <div class="tabs">
        <div class="tab" :class="{ active: isLogin }" @click="isLogin = true">登录</div>
        <div class="tab" :class="{ active: !isLogin }" @click="isLogin = false">注册</div>
      </div>
      
      <!-- 表单区域 -->
      <div class="input-group">
        <input class="input" type="text" v-model="form.username" placeholder="请输入用户名" />
      </div>
      
      <div class="input-group">
        <input class="input" type="password" v-model="form.password" placeholder="请输入密码" />
      </div>
      
      <div class="input-group" v-if="!isLogin">
        <input class="input" type="text" v-model="form.email" placeholder="请输入邮箱" />
      </div>
      
      <button class="submit-btn" @click="handleSubmit" :loading="loading">
        {{ isLogin ? '登 录' : '注 册' }}
      </button>
      
      <!-- 服务器配置入口 -->
      <div class="settings-link" @click="showSettings = true">
        ⚙️ 配置服务器地址
      </div>
    </div>
    
    <!-- 服务器配置弹窗 -->
    <div class="modal-mask" v-if="showSettings">
        <div class="modal-content">
            <div class="modal-title">服务器地址配置</div>
            <div class="modal-body">
                <input class="input" type="text" v-model="serverUrl" placeholder="例如 192.168.1.5:5000" />
                <div class="tip">请输入服务器 IP 和端口，无需加 /api/v1</div>
            </div>
            <div class="modal-footer">
                <button class="modal-btn cancel" @click="showSettings = false">取消</button>
                <button class="modal-btn confirm" @click="saveServerUrl">保存</button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import request from '@/utils/request';

const userStore = useUserStore();
const isLogin = ref(true);
const loading = ref(false);
const showSettings = ref(false);
const serverUrl = ref('');

const form = reactive({
  username: '',
  password: '',
  email: ''
});

onMounted(() => {
    const savedHost = uni.getStorageSync('api_host');
    if (savedHost) {
        serverUrl.value = savedHost;
    } else {
        serverUrl.value = 'http://127.0.0.1:5000';
    }
});

const saveServerUrl = () => {
    if (!serverUrl.value) {
        uni.showToast({ title: '地址不能为空', icon: 'none' });
        return;
    }
    uni.setStorageSync('api_host', serverUrl.value);
    uni.showToast({ title: '保存成功', icon: 'success' });
    showSettings.value = false;
};

const handleSubmit = async () => {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
    return;
  }
  
  loading.value = true;
  try {
    if (isLogin.value) {
      const res = await request.post('/auth/login', {
        username: form.username,
        password: form.password
      });
      
      if (res.code === 200) {
        userStore.setUserInfo(res.data);
        uni.showToast({ title: '登录成功' });
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/index/index' });
        }, 1000);
      }
    } else {
      const res = await request.post('/auth/register', {
        username: form.username,
        password: form.password,
        email: form.email
      });
      
      if (res.code === 201) {
        uni.showToast({ title: '注册成功，请登录' });
        isLogin.value = true;
      }
    }
  } catch (e) {
  } finally {
    loading.value = false;
  }
};
</script>

<style>
.container {
  padding: 40px 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}
.header {
  text-align: center;
  margin-bottom: 50px;
}
.title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}
.subtitle {
  font-size: 14px;
  color: #999;
  margin-top: 10px;
}
.form-box {
  background: #fff;
  border-radius: 10px;
  padding: 30px 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
.tabs {
  display: flex;
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
}
.tab {
  flex: 1;
  text-align: center;
  padding-bottom: 10px;
  font-size: 16px;
  color: #666;
}
.tab.active {
  color: #409EFF;
  border-bottom: 2px solid #409EFF;
  font-weight: bold;
}
.input-group {
  margin-bottom: 20px;
}
.input {
  width: 100%;
  height: 45px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 0 15px;
  box-sizing: border-box;
  font-size: 14px;
}
.submit-btn {
  width: 100%;
  height: 45px;
  background-color: #409EFF;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  margin-top: 10px;
}
.submit-btn:active {
  background-color: #66b1ff;
}
.settings-link {
    text-align: center;
    margin-top: 20px;
    color: #909399;
    font-size: 14px;
    padding: 10px;
}
/* 弹窗样式 */
.modal-mask {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999;
}
.modal-content {
    background: #fff;
    width: 80%;
    border-radius: 8px;
    padding: 20px;
}
.modal-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; }
.tip { font-size: 12px; color: #999; margin-top: 5px; }
.modal-footer { display: flex; margin-top: 20px; justify-content: flex-end; gap: 10px; }
.modal-btn { font-size: 14px; padding: 5px 15px; border-radius: 4px; border: none; }
.modal-btn.cancel { background: #f0f2f5; color: #606266; }
.modal-btn.confirm { background: #409EFF; color: #fff; }
</style>
