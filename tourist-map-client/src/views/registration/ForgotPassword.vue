<template>
  <div class="reset-container d-flex align-items-center justify-content-center vh-100 bg-light">
    <div class="card shadow-sm p-4 bg-white rounded" style="width: 100%; max-width: 450px;">
      
      <div v-if="!isSent">
        <h3 class="mb-3 fw-bold text-dark text-center">Восстановление пароля</h3>
        <p class="text-secondary small text-center">Введите e-mail, указанный при регистрации, и мы отправим ссылку для сброса.</p>
        
        <form @submit.prevent="handleResetRequest">
          <div class="mb-3">
            <label class="form-label text-dark fw-semibold small">Email</label>
            <input 
              v-model="email" 
              type="email" 
              class="form-control" 
              required
            />
          </div>
          
          <div v-if="errorMessage" class="alert alert-danger p-2 small">
            {{ errorMessage }}
          </div>

          <button type="submit" class="btn btn-primary w-100 py-2" :disabled="isLoading">
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
            Сбросить пароль
          </button>
        </form>
      </div>

      <div v-else class="text-center py-3">
        <div class="mb-3 text-success" style="font-size: 3rem;">
          <i class="bi bi-envelope-check"></i>
        </div>
        <h4 class="fw-bold text-dark">Письмо отправлено!</h4>
        <p class="text-secondary mt-3">
          Мы отправили вам по электронной почте инструкции для смены пароля. 
          Если они не получены в течение нескольких минут, проверьте папку <strong>Спам</strong>.
        </p>
        <router-link to="/login" class="btn btn-outline-primary w-100 mt-3 py-2">Вернуться к входу</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const email = ref('');
const isSent = ref(false);
const isLoading = ref(false);
const errorMessage = ref('');

const handleResetRequest = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/password-reset/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value })
    });
    
    if (response.ok) {
      isSent.value = true;
    } else {
      const data = await response.json();
      errorMessage.value = data.message || 'Произошла ошибка. Попробуйте позже.';
    }
  } catch (error) {
    errorMessage.value = 'Ошибка сети. Проверьте соединение с бэкендом.';
    console.error(error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.reset-container {
  background-color: #f8f9fa;
}
</style>