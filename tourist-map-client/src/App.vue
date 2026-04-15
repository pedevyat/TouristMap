<template>
  <div class="d-flex vh-100 vw-100 overflow-hidden">
    
    <Sidebar :user="currentUser" />

    <main class="flex-grow-1 position-relative">
      <router-view />
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Sidebar from './components/Sidebar.vue';

const currentUser = ref(null);

onMounted(async () => {
  // Запрос к Django API: fetch('/api/user-info/')
  // currentUser.value = await response.json();
});

const handleLogout = () => {
  // Логика выхода
};
</script>

<style>
@import "./assets/styles.css";
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
</style>