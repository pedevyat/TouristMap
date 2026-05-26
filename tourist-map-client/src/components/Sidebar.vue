<template>
  <aside 
    id="sidebar" 
    class="sidebar bg-white border-end vh-100"
    :class="{ 'collapsed': isCollapsed }"
  >
    <button 
      @click="isCollapsed = !isCollapsed" 
      class="toggle-btn shadow-sm border border-start-0 bg-white rounded-end d-flex align-items-center justify-content-center"
      :title="isCollapsed ? 'Развернуть панель' : 'Свернуть панель'"
    >
      <svg 
        width="8" 
        height="12" 
        viewBox="0 0 8 12" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        class="arrow-icon"
        :style="{ transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }"
      >
        <path 
          d="M6.5 11L1.5 6L6.5 1" 
          stroke="currentColor" 
          stroke-width="2.5" 
          stroke-linecap="round" 
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <div class="sidebar-inner d-flex flex-column justify-content-between h-100 w-100">
      <div class="w-100"> 
        <div class="sidebar-header p-4 d-flex align-items-center mb-4"> 
          <router-link to="/" class="d-flex align-items-center link-dark text-decoration-none">
            <img src="../assets/images/logo.png" width="40" class="me-2">
            <span class="fs-5 fw-bold">Туристическая карта</span>
          </router-link>
        </div>
        
        <ul class="nav nav-pills flex-column gap-2 px-3"> 
          <li class="nav-item">
            <router-link to="/" class="nav-link link-dark d-flex align-items-center">
              <img src="../assets/images/map-main-page.svg" width="24" class="me-2">
              <span>Карта</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/favorite" class="nav-link link-dark d-flex align-items-center">
              <img src="../assets/images/museum-list.svg" width="24" class="me-2">
              <span>Отмеченные места</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link to="/selection" class="nav-link link-dark d-flex align-items-center">
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
            <span class="nav-link link-dark px-0">{{ username }}</span>
          </div>
          <button @click="logout" class="btn btn-sm btn-outline-danger border-0">
               Выйти
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';

  const router = useRouter();
  const username = ref(null);
  const isCollapsed = ref(false);

  onMounted(() => {
    username.value = localStorage.getItem('username');
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const logout = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/logout/', {
        method: 'POST',
        credentials: 'include', 
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') 
        }
      });

      if (response.ok) {
        localStorage.removeItem('username');
        username.value = null;
        router.push({ name: 'login' });
      }
    } catch (error) {
      console.error('Ошибка сети при выходе:', error);
    }
  };
</script>

<style scoped>
.sidebar {
  width: 300px;
  flex-shrink: 0;
  position: relative; 
  z-index: 1050; /* сайдбар должен быть выше карты */
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* При схлопывании обнуляем ширину, чтобы main занял всё пространство */
.sidebar.collapsed {
  width: 0;
  border-right: none !important; /* Прячем рамку, чтобы не двоилась */
}

/* Внутренний блок всегда сохраняет ширину 300px и просто сдвигается за экран */
.sidebar-inner {
  width: 300px;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.sidebar.collapsed .sidebar-inner {
  transform: translateX(-300px);
}

/* Кнопка переключения */
.toggle-btn {
  position: absolute;
  right: -24px;       
  top: 20px;           
  width: 24px;
  height: 44px;
  z-index: 1060;      
  color: #000000;      
  filter: drop-shadow(0px 0px 1px rgba(0, 0, 0, 0.5));
  
  padding: 0;
  background-color: #ffffff;
  border: 1px solid #dee2e6;
  border-left: none;
  transition: background-color 0.2s, color 0.2s, filter 0.2s;
}

.toggle-btn:hover {
  color: #000000;
  filter: drop-shadow(0px 0px 2px rgba(0, 0, 0, 0.8)); 
  background-color: #f8f9fa;
}

.arrow-icon {
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}


.nav-link.active {
  background-color: #e9ecef;
  color: black;
}
</style>