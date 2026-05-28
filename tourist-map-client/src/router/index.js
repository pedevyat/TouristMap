import { createRouter, createWebHistory } from 'vue-router'
import MapView from '../views/MapView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: MapView
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/registration/Login.vue')
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('@/views/registration/Registration.vue')
  },
  {
    path: '/favorite',
    name: 'favorite',
    component: () => import('@/views/Favorite.vue')
  },
  {
    path: '/place/:id',
    name: 'Place',
    component: () => import('@/views/Place.vue'),
    props: true
  },
  {
    path: '/selection',
    name: 'CityPlace',
    component: () => import('@/views/CityPlace.vue'),
    props: true
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmailView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/registration/ForgotPassword.vue'),
  },
  {
    path: '/reset-password-confirm/:uid/:token',
    name: 'reset-password-confirm',
    component: () => import('@/views/registration/ResetPasswordConfirm.vue'),
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router