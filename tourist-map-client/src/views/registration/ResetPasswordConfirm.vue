<template>
  <div class="reset-container d-flex align-items-center justify-content-center vh-100 bg-light">
    <div class="card shadow-sm p-4 bg-white rounded" style="width: 100%; max-width: 450px;">
      
      <div v-if="!isCompleted">
        <h3 class="mb-3 fw-bold text-dark text-center">Новый пароль</h3>
        <p class="text-secondary small text-center">Пожалуйста, введите и подтвердите свой новый пароль.</p>
        
        <form @submit.prevent="handlePasswordConfirm">
          <div class="mb-3">
            <label class="form-label text-dark fw-semibold small">Новый пароль</label>
            <input v-model="password" type="password" class="form-control" required minlength="8" />
          </div>
          
          <div class="mb-3">
            <label class="form-label text-dark fw-semibold small">Подтвердите пароль</label>
            <input v-model="passwordConfirm" type="password" class="form-control" required />
          </div>

          <div v-if="errorMessage" class="alert alert-danger p-2 small">
            {{ errorMessage }}
          </div>

          <button type="submit" class="btn btn-success w-100 py-2" :disabled="isLoading">
            <span v-if="isLoading" class="spinner-border spinner-border-sm me-2"></span>
            Сохранить изменения
          </button>
        </form>
      </div>

      <div v-else class="text-center py-3">
        <div class="mb-3 text-success" style="font-size: 3rem;">
          <i class="bi bi-check-circle-fill"></i>
        </div>
        <h4 class="fw-bold text-dark">Пароль успешно изменен!</h4>
        <p class="text-secondary mt-2">Теперь вы можете войти в систему, используя новые учетные данные.</p>
        <router-link to="/login" class="btn btn-primary w-100 mt-3 py-2">Войти в аккаунт</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const password = ref('');
const passwordConfirm = ref('');
const isCompleted = ref(false);
const isLoading = ref(false);
const errorMessage = ref('');

// Достаем параметры из URL динамически через Vue Router
const uid = route.params.uid;
const token = route.params.token;

const handlePasswordConfirm = async () => {
  if (password.value !== passwordConfirm.value) {
    errorMessage.value = 'Пароли не совпадают!';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await fetch('http://127.0.0.1:8000/api/password-reset-confirm/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uid: uid,
        token: token,
        password: password.value
      })
    });

    if (response.ok) {
      isCompleted.value = true;
    } else {
      const data = await response.json();
      errorMessage.value = data.message || 'Ссылка недействительна или срок её действия истек.';
    }
  } catch (error) {
    errorMessage.value = 'Ошибка соединения с сервером.';
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