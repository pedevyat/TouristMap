<template>
  <aside id="sidebar" class="sidebar bg-white border-end vh-100 d-flex flex-column justify-content-between">
    <div class="w-100"> <div class="sidebar-header p-4 d-flex align-items-center mb-4"> <router-link to="/" class="d-flex align-items-center link-dark text-decoration-none">
          <img src="../assets/images/logo.png" width="40" class="me-2">
          <span class="fs-5 fw-bold">Туристическая карта</span>
        </router-link>
      </div>
      
      <ul class="nav nav-pills flex-column gap-2 px-3"> <li class="nav-item">
          <router-link to="/" class="nav-link link-dark d-flex align-items-center">
            <img src="../assets/images/map-main-page.svg" width="24" class="me-2">
            <span>Карта</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="#" class="nav-link link-dark d-flex align-items-center">
            <img src="../assets/images/museum-list.svg" width="24" class="me-2">
            <span>Отмеченные места</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="#" class="nav-link link-dark d-flex align-items-center">
            <img src="../assets/images/star.svg" width="24" class="me-2">
            <span>Подборка мест</span>
          </router-link>
        </li>
      </ul>
    </div>
    <div class="p-4 border-top">
      <router-link v-if="!username" to="/login" class="nav-link link-dark d-flex align-items-center">
        <strong>Войти</strong>
      </router-link>

      <div v-else class="d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center">
          <span class="nav-link link-dark">{{ username }}</span>
        </div>
        <button @click="logout" class="btn btn-sm btn-outline-danger border-0">
             Выйти
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';

  const router = useRouter();
  const username = ref(null);

  onMounted(() => {
    username.value = localStorage.getItem('username');
  });

  const logout = () => {
    localStorage.removeItem('username');
    username.value = null;
    router.push('/');
  };
</script>

<style scoped>
.sidebar {
  width: 300px;
  flex-shrink: 0;
}

.nav-link:hover {
  background-color: #f8f9fa;
}

.nav-link.active {
  background-color: #e9ecef;
  color: black;
}
</style>