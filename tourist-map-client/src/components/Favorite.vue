<template>
  <div class="container mt-4 text-dark">
    <h2 class="mb-4 text-black fw-bold">Отмеченные места</h2>
    
    <div v-if="favorites.length === 0" class="alert alert-light border text-dark">
      Пока ничего не добавили
    </div>

    <div v-else class="table-responsive rounded">
      <table class="table table-hover align-middle bg-white">
        <thead class="table">
          <tr>
            <th scope="col" style="width: 80px;">Фото</th>
            <th scope="col">Название</th>
            <th scope="col">Город</th>
            <th scope="col">Область</th>
            <th scope="col">Дата добавления</th>
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
            <td>
              <span class="text-dark">{{ item.name }}</span>
            </td>
            <td>
              <span class="text-secondary">{{ item.city  }}</span>
            </td>
            <td>
              <span class="text-secondary">{{ item.region }}</span>
            </td>
            <td>
              <span class="text-muted">{{ item.date  }}</span>
            </td>
            <td class="text-end">
              <span @click="removeFromFavorites(item.id)">
                <i class="bi bi-trash"></i> Х
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const favorites = ref([]);

// Загрузка данных с сервера
const loadFavorites = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/');
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
      headers: { 'Content-Type': 'application/json' },
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