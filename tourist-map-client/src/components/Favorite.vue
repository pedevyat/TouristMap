<template>
  <div class="container mt-4 text-dark">
    <h2 class="mb-4 text-black fw-bold">Отмеченные места</h2>
    
    <div v-if="isFetching" class="text-center my-5">
       <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="favorites.length === 0" class="alert alert-light border text-dark">
      Пока ничего не добавили
    </div>

    <div v-else class="table-responsive rounded shadow-sm">
      <div class="scroll-area" ref="scrollTarget">
        <table class="table table-hover align-middle bg-white">
          <thead class="table">
            <tr>
              <th scope="col" style="width: 80px;">Фото</th>
              <th scope="col">Место</th>
              <th scope="col">Город</th>
              <th scope="col">Добавлено</th>
              <th scope="col" class="text-end">Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in favorites" :key="item.id">
              <td>
                <img v-if="item.image" :src="item.image" 
                    class="rounded" 
                    style="width: 60px; height: 45px; object-fit: cover;">
                <div v-else class="bg-light rounded text-muted text-center" 
                    style="width: 60px; height: 45px; font-size: 10px; line-height: 45px;">
                  ?
                </div>
              </td>
              <td><span class="fw-bold text-dark">{{ item.name }}</span></td>
              <td><span class="text-secondary">{{ item.city }}</span></td>
              <td>
                <small class="text-muted">{{ item.date }}</small>
              </td>
              <td class="text-end">
                <button @click="removeFromFavorites(item.id)" class="btn btn-sm btn-outline-danger border-0">
                  <i class="bi bi-trash"></i> Удалить
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useFetch } from '@vueuse/core';
import { useCookies } from '@vueuse/integrations/useCookies';

const favorites = ref([]);
const scrollTarget = ref(null);   

// Функция для получения CSRF-токена (необходима для работы POST в Django)
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

// Загрузка данных с сервера
const loadFavorites = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'GET',
      credentials: 'include'
    });
    if (response.ok) {
      // Сервер должен вернуть массив объектов с полями: id, name, city, region, date, image
      favorites.value = await response.json();
    } else {
      console.error("Ошибка при получении данных с сервера");
    }
  } catch (error) {
    console.error("Сетевая ошибка:", error);
  }
};

// Удаление через сервер
const removeFromFavorites = async (id) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
      body: JSON.stringify({ place_id: id }) // Передаем ID места для удаления (toggle)
    });

    if (response.ok) {
      // Если на сервере удаление прошло успешно, обновляем локальный список
      favorites.value = favorites.value.filter(fav => fav.id !== id);
    }
  } catch (error) {
    console.error("Ошибка при удалении:", error);
  }
};

onMounted(loadFavorites);
</script>

<style scoped>
/* Стили для скролла */
.scroll-area {
  max-height: 100vh; /* Высота, после которой появится скролл */
  overflow-y: auto;  /* Включаем вертикальную прокрутку */
  overflow-x: hidden;
}

/* Фиксация шапки таблицы при скролле */
.sticky-top {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: #f8f9fa;
  box-shadow: inset 0 -1px 0 #dee2e6;
}

.no-photo {
  width: 60px; 
  height: 45px; 
  font-size: 10px; 
  line-height: 45px;
}

/* Красивый тонкий скроллбалл (для Chrome/Safari) */
.scroll-area::-webkit-scrollbar {
  width: 6px;
}
.scroll-area::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.scroll-area::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 10px;
}
.scroll-area::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>