<script>
export default {
  onLaunch: function() {
    console.log('App Launch');
    // 检查登录状态
    const userStore = uni.getStorageSync('user_info');
    if (!userStore || !userStore.token) {
      uni.reLaunch({
        url: '/pages/login/login'
      });
    }
  },
  onShow: function() {
    console.log('App Show');
  },
  onHide: function() {
    console.log('App Hide');
  }
}
</script>

<style>
/* 每个页面公共css */
view, text, image, input, button {
  box-sizing: border-box;
}
</style>
