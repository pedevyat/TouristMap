<template>
  <div class="register-container d-flex align-items-center justify-content-center min-vh-100 bg-light py-4">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 400px;">
      <h2 class="text-center mb-4">Регистрация</h2>

      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>

      <div v-if="successMessage" class="alert alert-success" role="alert">
        {{ successMessage }}
      </div>

      <form @submit.prevent="handleRegister" class="needs-validation">
        <div class="mb-3">
          <label for="username" class="form-label">Имя пользователя</label>
          <input 
            v-model="registerForm.username"
            type="text" 
            id="username" 
            class="form-control" 
            required
          >
        </div>

        <div class="mb-3">
          <label for="email" class="form-label">Электронная почта</label>
          <input 
            v-model="registerForm.email"
            type="email" 
            id="email" 
            class="form-control" 
            required
          >
        </div>

        <div class="mb-3">
          <label for="password" class="form-label">Пароль</label>
          <input 
            v-model="registerForm.password"
            type="password" 
            id="password" 
            class="form-control" 
            required
          >
        </div>

        <div class="mb-4">
          <label for="passwordConfirm" class="form-label">Подтвердите пароль</label>
          <input 
            v-model="registerForm.passwordConfirm"
            type="password" 
            id="passwordConfirm" 
            class="form-control" 
            required
          >
        </div>

        <button type="submit" class="btn btn-success w-100" :disabled="isLoading">
          <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
          Зарегистрироваться
        </button>
      </form>
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
const successMessage = ref(null);

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  passwordConfirm: ''
});

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.withCredentials = true;

const handleRegister = async () => {
  // проверка совпадения паролей на фронтенде
  if (registerForm.password !== registerForm.passwordConfirm) {
    error.value = 'Пароли не совпадают!';
    return;
  }

  isLoading.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    const csrfToken = Cookies.get('csrftoken');
    const response = await axios.post('http://127.0.0.1:8000/api/register/', 
      {
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password
      },
      {
        headers: {
          'X-CSRFToken': csrfToken 
        },
        withCredentials: true
      }
    );
    
    if (response.data.status === 'ok') {
      successMessage.value = 'Загрузка...';
      if (response.data.username) {
        localStorage.setItem('username', response.data.username);
      }
      setTimeout(() => {
        router.push({ name: 'home' }).then(() => {
          location.reload(); 
        });
      }, 1500);
    }
  } catch (err) {
    console.error('Ошибка регистрации:', err.response);
    
    if (err.response && err.response.data && err.response.data.message) {
      error.value = err.response.data.message;
    } else if (err.response && err.response.data && err.response.data.error) {
      error.value = err.response.data.error;
    } else {
      error.value = 'Ошибка';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  background-color: #f8f9fa;
}
</style>