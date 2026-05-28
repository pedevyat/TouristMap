<template>
  <div class="verify-container d-flex align-items-center justify-content-center min-vh-100 bg-light py-4">
    <div class="card p-4 shadow-sm text-center" style="width: 100%; max-width: 450px;">
      
      <div class="mb-4 text-success">
        <i v-if="isProcessing" class="spinner-border text-success" style="width: 3rem; height: 3rem;" role="status"></i>
        <span v-else-if="successMessage" class="fs-1">✅</span>
        <span v-else-if="errorMessage" class="fs-1">❌</span>
        <span v-else class="fs-1">✉️</span>
      </div>

      <h2 class="mb-3">{{ titleText }}</h2>

      <div v-if="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="alert alert-success" role="alert">
        {{ successMessage }}
      </div>

      <div class="card-body p-0 text-muted">
        <p v-if="!hasToken" class="mb-4">
          Мы отправили письмо со ссылкой для подтверждения на указанный вами адрес электронной почты. 
          Пожалуйста, проверьте входящие сообщения (и папку «Спам», если письма долго нет) и перейдите по ссылке для активации аккаунта.
        </p>

        <p v-if="hasToken && isProcessing" class="mb-4">
          Проверяем вашу ссылку активации, пожалуйста, подождите...
        </p>

        <p v-if="successMessage" class="mb-4 text-dark font-weight-bold">
          Перенаправляем на страницу авторизации...
        </p>
      </div>

      <div class="mt-3">
        <router-link :to="{ name: 'login' }" class="btn btn-outline-success w-100">
          Перейти к авторизации
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

const isProcessing = ref(false);
const errorMessage = ref(null);
const successMessage = ref(null);

// Проверяем, есть ли токен в параметрах URL (?token=...)
const token = route.query.token;
const hasToken = computed(() => !!token);

// Динамический заголовок в зависимости от состояния
const titleText = computed(() => {
  if (isProcessing.value) return 'Активация аккаунта';
  if (successMessage.value) return 'Успешно!';
  if (errorMessage.value) return 'Ошибка активации';
  return 'Подтвердите ваш Email';
});

// Настройка Axios (чтобы сессия создалась при авто-логине после активации)
axios.defaults.withCredentials = true;

onMounted(async () => {
  // Если токен есть в URL, значит пользователь пришел из письма — запускаем верификацию
  if (token) {
    isProcessing.value = true;
    errorMessage.value = null;
    successMessage.value = null;

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/verify-email/', {
        token: token
      });

      if (response.data.status === 'ok') {
        successMessage.value = response.data.message;
        
        // Поскольку бэкенд сразу делает login(), перенаправляем на главную страницу (или карту) через 3 секунды
        setTimeout(() => {
          router.push({ name: 'login' }); // Или имя роута твоей карты/главной, например 'home'
        }, 3500);
      }
    } catch (err) {
      console.error('Ошибка верификации:', err.response);
      if (err.response && err.response.data && err.response.data.message) {
        errorMessage.value = err.response.data.message;
      } else {
        errorMessage.value = 'Не удалось подтвердить почту. Ссылка недействительна или устарела.';
      }
    } finally {
      isProcessing.value = false;
    }
  }
});
</script>

<style scoped>
.verify-container {
  background-color: #f8f9fa;
}
.fs-1 {
  font-size: 3.5rem;
}
</style>