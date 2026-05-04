import { createRouter, createWebHistory } from 'vue-router'
import MapView from '../components/MapView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: MapView
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/components/registration/Login.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router