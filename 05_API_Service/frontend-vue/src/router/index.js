import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/',
      component: () => import('@/views/LayoutView.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue')
        },
        {
          path: 'stream',
          name: 'stream',
          component: () => import('@/views/StreamView.vue')
        },
        {
          path: 'records',
          name: 'records',
          component: () => import('@/views/RecordsView.vue')
        },
        {
          path: 'server-status',
          name: 'server-status',
          component: () => import('@/views/ServerStatusView.vue')
        },
        {
          path: 'system',
          name: 'system',
          component: () => import('@/views/SystemView.vue'),
          meta: { requiresAdmin: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.meta.requiresAdmin && userStore.userInfo.role !== 'admin') {
    next('/') // 没权限，回首页
  } else {
    next()
  }
})

export default router
