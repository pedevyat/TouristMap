<template>
  <div class="container scroll-container mt-4 text-dark">
    <h2 class="mb-4 text-black fw-bold">Отмеченные места</h2>
    
    <div v-if="isFetching" class="text-center my-5">
       <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="favorites.length === 0" class="alert alert-light border text-dark">
      Пока ничего не добавили
    </div>

    <div v-else class="table-responsive rounded shadow-sm">
      <table class="table table-hover align-middle bg-white">
        <thead>
          <tr>
            <th scope="col" style="width: 80px;">Фото</th>
            
            <th scope="col" @click="sortBy('name')" class="sortable-header">
              Место <span class="sort-icon">{{ getSortIcon('name') }}</span>
            </th>
            <th scope="col" @click="sortBy('city')" class="sortable-header">
              Местность <span class="sort-icon">{{ getSortIcon('city') }}</span>
            </th>
            <th scope="col" @click="sortBy('date')" class="sortable-header">
              Добавлено <span class="sort-icon">{{ getSortIcon('date') }}</span>
            </th>
            
            <th scope="col" class="text-end">Действие</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedFavorites" :key="item.id">
            <td>
              <img v-if="item.image" :src="item.image" 
                   class="rounded" 
                   style="width: 60px; height: 45px; object-fit: cover;">
              <div v-else class="bg-light rounded text-muted text-center" 
                   style="width: 60px; height: 45px; font-size: 10px; line-height: 45px;">
                ?
              </div>
            </td>
            <td>
              <span @click="goToPlace(item.id)" class="fw-bold text-dark place-title-link" style="cursor: pointer;">
                {{ item.name }}
              </span>
            </td>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const favorites = ref([]);
const isFetching = ref(true);

// Состояние сортировки
const currentSortKey = ref('');      
const currentSortOrder = ref('asc'); 

// Функция переключения сортировки
const sortBy = (key) => {
  if (currentSortKey.value === key) {
    currentSortOrder.value = currentSortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    currentSortKey.value = key;
    currentSortOrder.value = 'asc';
  }
};

// Возвращает стрелочку для отображения в заголовке таблицы
const getSortIcon = (key) => {
  if (currentSortKey.value === key) 
    return currentSortOrder.value === 'asc' ? '▲' : '▼';
};

// Вычисляемое свойство для фильтрации и сортировки
const sortedFavorites = computed(() => {
  if (!currentSortKey.value) return favorites.value;

  return [...favorites.value].sort((a, b) => {
    const modifier = currentSortOrder.value === 'asc' ? 1 : -1;
    
    let valA = a[currentSortKey.value];
    let valB = b[currentSortKey.value];

    // Сортировка дат
    if (currentSortKey.value === 'date') {
      const dateA = new Date(valA);
      const dateB = new Date(valB);
      if (!isNaN(dateA) && !isNaN(dateB)) {
        return (dateA - dateB) * modifier;
      }
    }

    valA = valA ? String(valA) : '';
    valB = valB ? String(valB) : '';
    return valA.localeCompare(valB, 'ru', { numeric: true, sensitivity: 'base' }) * modifier;
  });
});

// Функция для получения CSRF-токена
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
  isFetching.value = true;
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'GET',
      credentials: 'include'
    });

    if (response.status === 401 || response.status === 403) {
      alert("Для просмотра отмеченных мест необходимо войти в аккаунт");
      router.push({ name: 'login' });
      return;
    }

    if (response.ok) {
      favorites.value = await response.json();
    } else {
      console.error("Ошибка при получении данных с сервера");
    }
  } catch (error) {
    console.error("Сетевая ошибка:", error);
  } finally {
    isFetching.value = false;
  }
};

// Удаление через сервер
const removeFromFavorites = async (id) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
      body: JSON.stringify({ place_id: id })
    });

    if (response.status === 401) {
      router.push({ name: 'login' });
      return;
    }

    if (response.ok) {
      favorites.value = favorites.value.filter(fav => fav.id !== id);
    }
  } catch (error) {
    console.error("Ошибка при удалении:", error);
  }
};

const goToPlace = (id) => {
  router.push({ name: 'Place', params: { id: id } });
};

onMounted(loadFavorites);
</script>

<style scoped>
.scroll-container {
  max-height: 100vh;
  overflow-y: auto;     
  overflow-x: hidden;   
}

.scroll-container::-webkit-scrollbar {
  width: 6px;
}
.scroll-container::-webkit-scrollbar-track {
  background: transparent;
}
.scroll-container::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 4px;
}
.scroll-container::-webkit-scrollbar-thumb:hover {
  background-color: #aaa;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}
.sortable-header:hover {
  background-color: #f1f3f5;
}
.sort-icon {
  display: inline-block;
  margin-left: 5px;
  font-size: 12px;
  color: #6c757d;
}
</style>