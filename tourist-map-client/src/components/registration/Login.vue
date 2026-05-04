<template>
  <div class="login-container d-flex align-items-center justify-content-center vh-100 bg-light">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 400px;">
      <h2 class="text-center mb-4">Вход</h2>

      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>

      <form @submit.prevent="handleLogin" class="needs-validation">
        <div class="mb-3">
          <label for="username" class="form-label">Имя пользователя</label>
          <input 
            v-model="loginForm.username"
            type="text" 
            id="username" 
            class="form-control" 
            required
          >
        </div>

        <div class="mb-3">
          <label for="password" class="form-label">Пароль</label>
          <input 
            v-model="loginForm.password"
            type="password" 
            id="password" 
            class="form-control" 
            required
          >
        </div>

        <div class="mb-3 form-check">
          <input 
            v-model="loginForm.remember"
            type="checkbox" 
            class="form-check-input" 
            id="rememberMe"
          >
          <label class="form-check-label" for="rememberMe">Запомнить меня</label>
        </div>

        <button type="submit" class="btn btn-primary w-100" :disabled="isLoading">
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
          Вход
        </button>
      </form>

      <div class="mt-3 text-center">
        <a href="http://127.0.0.1:8000/accounts/password_reset/" class="text-decoration-none">
          Утерян пароль?
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios';
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import Cookies from 'js-cookie';

const router = useRouter();
const isLoading = ref(false);
const error = ref(null);

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
});

// Настройка для работы с CSRF-токенами Django
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.withCredentials = true;


const handleLogin = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    // Получаем токен из кук вручную
    const csrfToken = Cookies.get('csrftoken');

    const response = await axios.post('http://127.0.0.1:8000/api/login/', 
      {
        username: loginForm.username,
        password: loginForm.password
      },
      {
        headers: {
          'X-CSRFToken': csrfToken 
        },
        withCredentials: true
      }
    );
    
   if (response.data.status === 'ok') {
      localStorage.setItem('username', response.data.username);
      router.push({ name: 'home' }).then(() => {
        location.reload();
      });
    }
  } catch (err) {
    console.error(err.response);
    error.value = 'Ошибка входа: проверьте логин или пароль';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  /* Центрирование на весь экран */
  background-color: #f8f9fa;
}
</style>