// stores/user.js
import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => {
    // 从本地存储初始化
    const userInfo = uni.getStorageSync('user_info');
    return {
      token: userInfo ? userInfo.token : '',
      userInfo: userInfo ? userInfo.user_info : {}
    };
  },
  
  actions: {
    setUserInfo(data) {
      this.token = data.token;
      this.userInfo = data.user_info;
      
      // 持久化存储
      uni.setStorageSync('user_info', data);
    },
    
    logout() {
      this.token = '';
      this.userInfo = {};
      uni.removeStorageSync('user_info');
    }
  }
});
