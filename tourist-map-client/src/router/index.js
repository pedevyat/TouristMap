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
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('@/components/registration/Registration.vue')
  },
  {
    path: '/favorite',
    name: 'favorite',
    component: () => import('@/components/Favorite.vue')
  },
  {
    path: '/place/:id',
    name: 'Place',
    component: () => import('@/components/Place.vue'),
    props: true
  },
  {
    path: '/selection',
    name: 'CityPlace',
    component: () => import('@/components/CityPlace.vue'),
    props: true
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router