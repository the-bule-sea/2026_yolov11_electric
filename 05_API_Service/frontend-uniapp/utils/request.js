// utils/request.js
// 适配 uni-app 的请求封装

// 默认地址（如果没有设置过，就用这个）
const DEFAULT_URL = 'http://127.0.0.1:5000/api/v1'; 

// 获取当前的基础 URL
const getBaseUrl = () => {
    // 从本地存储读取用户配置的地址
    let host = uni.getStorageSync('api_host');
    // 如果没配置过，使用默认值
    if (!host) {
        return DEFAULT_URL;
    }
    // 确保不以 / 结尾
    if (host.endsWith('/')) {
        host = host.slice(0, -1);
    }
    // 如果用户只输入了 IP (如 192.168.1.5:5000)，自动补全 http:// 和 /api/v1
    if (!host.startsWith('http')) {
        host = 'http://' + host;
    }
    // 简单的判断，如果用户没输入后缀 /api/v1，帮他加上
    // 这里假设用户通常只输入 http://ip:port
    if (!host.includes('/api/v1')) {
        host = host + '/api/v1';
    }
    return host;
};

const request = {
  // 基础配置
  config: {
    timeout: 60000
  },

  // 模拟 axios 的 request 拦截器
  interceptors: {
    request: (options) => {
      // 获取 token
      const userStore = uni.getStorageSync('user_info');
      if (userStore && userStore.token) {
        options.header = {
          ...options.header,
          'Authorization': `Bearer ${userStore.token}`
        };
      }
      return options;
    },
    response: (response) => {
      const { statusCode, data } = response;
      if (statusCode >= 200 && statusCode < 300) {
        return data;
      } else if (statusCode === 401) {
        uni.showToast({ title: '登录已过期', icon: 'none' });
        uni.removeStorageSync('user_info');
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/login/login' });
        }, 1500);
        return Promise.reject(data);
      } else {
        uni.showToast({ title: data.msg || '请求失败', icon: 'none' });
        return Promise.reject(data);
      }
    }
  },

  // 核心请求方法
  async httpRequest(method, url, data = {}, header = {}) {
    // 动态获取 Base URL
    const baseUrl = getBaseUrl();
    
    let options = {
      url: baseUrl + url, // 动态拼接
      method: method,
      data: data,
      header: header
    };

    options = this.interceptors.request(options);

    return new Promise((resolve, reject) => {
      uni.request({
        ...options,
        success: (res) => {
          try {
            const result = this.interceptors.response(res);
            resolve(result);
          } catch (e) {
            reject(e);
          }
        },
        fail: (err) => {
          uni.showToast({ 
              title: '连接失败，请检查服务器地址配置', 
              icon: 'none',
              duration: 3000
          });
          reject(err);
        }
      });
    });
  },

  get(url, data = {}) {
    return this.httpRequest('GET', url, data);
  },

  post(url, data = {}, header = {}) {
    return this.httpRequest('POST', url, data, header);
  },
  
  upload(url, filePath, formData = {}) {
    let header = {};
    const userStore = uni.getStorageSync('user_info');
    if (userStore && userStore.token) {
        header['Authorization'] = `Bearer ${userStore.token}`;
    }
    
    // 动态获取 Base URL
    const baseUrl = getBaseUrl();

    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: baseUrl + url,
        filePath: filePath,
        name: 'file',
        formData: formData,
        header: header,
        success: (uploadFileRes) => {
          let data;
          try {
             data = JSON.parse(uploadFileRes.data);
          } catch (e) {
             data = uploadFileRes.data;
          }
          
          if (uploadFileRes.statusCode === 200) {
            resolve(data);
          } else {
            reject(data);
          }
        },
        fail: (err) => {
          uni.showToast({ title: '上传失败，检查服务器配置', icon: 'none' });
          reject(err);
        }
      });
    });
  }
};

export default request;
