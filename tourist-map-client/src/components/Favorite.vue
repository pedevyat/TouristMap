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

    const loadFavorites = () => {
    const data = localStorage.getItem('favorites');
    favorites.value = data ? JSON.parse(data) : [];
    };

    const removeFromFavorites = (id) => {
    favorites.value = favorites.value.filter(fav => fav.id !== id);
    localStorage.setItem('favorites', JSON.stringify(favorites.value));
    };

    onMounted(loadFavorites);
</script>