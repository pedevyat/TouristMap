<template>
  <div class="container scroll-container pt-4 text-black d-flex flex-column" style="height: 100vh;">
    
    <div class="search-panel pb-3">
      <h2 class="mb-4 text-black fw-bold">Подборка мест</h2>
      
      <div class="row mb-4">
        <div class="col-md-8">
          <label for="cityInput" class="form-label text-muted">Введите город или определите свое местоположение</label>
          <div class="input-group">
            <input 
              v-model="cityQuery" 
              @keyup.enter="searchPlaces"
              type="text" 
              id="cityInput" 
              class="form-control" 
              :disabled="isLoading"
            />
            <button 
              @click="searchPlaces" 
              class="btn btn-primary" 
              type="button"
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="spinner-border spinner-border-sm me-1" role="status"></span>
              Поиск
            </button>
            <button 
              @click="searchByGeolocation" 
              class="btn btn-outline-secondary" 
              type="button"
              :disabled="isLoading"
              title="Определить моё местоположение"
            >
              Где я?
            </button>
          </div>
        </div>
      </div>

      <div v-if="statusMessage" class="alert alert-info py-2 small" style="max-width: 600px;">
        {{ statusMessage }}
      </div>
    </div>

    <div class="flex-grow-1 pe-2" v-if="places.length > 0">
      <div class="row row-cols-1 row-cols-md-3 g-4 pb-4">
        <div class="col" v-for="item in places" :key="item.id">
          <div class="card h-100 shadow-sm border-0 place-card">
            <img 
              :src="item.image" 
              class="card-img-top" 
              alt="Фото объекта"
              style="height: 200px; object-fit: cover;"
            />
            <div class="card-body d-flex flex-column">
              <h5 class="card-title fw-bold text-dark fs-6">{{ item.name }}</h5>
              <p class="card-text text-muted small flex-grow-1">{{ item.description }}</p>
              
              <div class="mt-2 d-flex justify-content-between align-items-center">
                <span class="badge bg-secondary opacity-75">{{ item.distance }} км</span>
                
                <div class="d-flex align-items-center gap-2">
                  <button 
                    @click="toggleFavorite(item)" 
                    class="btn btn-star-favorite"
                    :class="{ 'is-active': item.isFavorite }"
                    title="Добавить в избранное"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" :fill="item.isFavorite ? '#ffc107' : 'none'" :stroke="item.isFavorite ? '#ffc107' : '#ccc'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                  </button>

                  <router-link 
                    :to="{ name: 'Place', params: { id: item.id }}" 
                    class="btn btn-sm btn-outline-primary"
                  >
                    Подробнее
                  </router-link>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onActivated, onDeactivated } from 'vue';
import { sendToggleFavoriteRequest } from '@/api/favoriteApi'; 

const cityQuery = ref('');
const places = ref([]);
const isLoading = ref(false);
const statusMessage = ref('');
const scrollPosition = ref(0);

onActivated(() => {
  window.scrollTo({
    top: scrollPosition.value,
    behavior: 'auto'
  });
});

onDeactivated(() => {
  scrollPosition.value = window.scrollY || window.pageYOffset;
});

// Геокодер Яндекса
const getCoordinates = async (cityName) => {
  if (typeof ymaps === 'undefined') {
    throw new Error('Яндекс.Карты не загружены на странице');
  }
  const res = await ymaps.geocode(cityName);
  const firstGeoObject = res.geoObjects.get(0);
  if (!firstGeoObject) return null;
  
  const coords = firstGeoObject.geometry.getCoordinates();
  return { lat: coords[0], lng: coords[1] };
};

// Формула Хаверсина 
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

// Запрос к Wikidata через Django Бэкенд 
const fetchPlacesInRadius = async (lat, lng, radiusInKm = 30) => {
  const url = `/api/search-places/?lat=${lat}&lng=${lng}&radius=${radiusInKm}`;
  
  const response = await fetch(url);
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.error || `Ошибка сервера: ${response.status}`);
  }
  
  return await response.json(); 
};

// Получение списка текущих QID в избранном у пользователя
const getUserFavoriteIds = async () => {
  try {
    const response = await fetch('/api/toggle-favorite/');
    
    // Проверяем, что сервер вернул именно JSON, а не HTML страницу ошибки
    const contentType = response.headers.get("content-type");
    if (response.ok && contentType && contentType.includes("application/json")) {
      const favs = await response.json();
      return favs.map(f => f.id);
    } else {
      console.error("Сервер вернул некорректный ответ или ошибку:", response.status);
    }
  } catch (e) {
    console.error("Не удалось загрузить избранное пользователя:", e);
  }
  return [];
};

// Переключение статуса избранного
const toggleFavorite = async (item) => {
  try {
    const res = await sendToggleFavoriteRequest(item.rawWikidata);

    if (res.status === 401) {
      alert('Для добавления в избранное необходимо авторизоваться.');
      return;
    }

    if (res.ok && res.data) {
      if (res.data.status === 'added') {
        item.isFavorite = true;
      } else if (res.data.status === 'removed') {
        item.isFavorite = false;
      }
    }
  } catch (error) {
    console.error("Ошибка при изменении статуса избранного:", error);
  }
};

const processCoordinatesSearch = async (lat, lng, radiusInKm = 30) => {
  statusMessage.value = `Ищем интересные места в радиусе ${radiusInKm} км...`;
  
  try {
    const rawData = await fetchPlacesInRadius(lat, lng, radiusInKm);
    const favoriteIds = await getUserFavoriteIds();
    
    const filtered = [];
    for (const item of rawData) {
      if (!item || !item.coord || !item.coord.value) continue;
      
      const match = item.coord.value.match(/Point\(([-\d.]+)\s+([-\d.]+)\)/);
      if (match) {
        const itemLng = parseFloat(match[1]);
        const itemLat = parseFloat(match[2]);
        
        const distance = calculateDistance(lat, lng, itemLat, itemLng);
        
        if (distance <= radiusInKm) {
          let secureImageUrl = 'https://placehold.co/600x400?text=Нет+фото';
          if (item.image && item.image.value) {
            secureImageUrl = item.image.value.replace(/^http:\/\//i, 'https://');
          }

          const qid = item.place && item.place.value ? item.place.value.split('/').pop() : Math.random().toString();
          if (!item.cityLabel) {
            item.cityLabel = { value: cityQuery.value || "Неизвестно" };
          }

          filtered.push({
            id: qid,
            name: item.placeLabel && item.placeLabel.value ? item.placeLabel.value : 'Без названия',
            description: item.description && item.description.value ? item.description.value : ' ',
            image: secureImageUrl,
            distance: distance.toFixed(1),
            isFavorite: favoriteIds.includes(qid),
            
            // Сохраняем исходный объект Wikidata, чтобы его прочитала sendToggleFavoriteRequest
            rawWikidata: item 
          });
        }
      }
    }

    filtered.sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance));
    places.value = filtered;

    if (places.value.length === 0) {
      statusMessage.value = `Ничего не найдено`;
    } else {
      statusMessage.value = `Успешно найдено мест: ${places.value.length}`;
    }
  } catch (error) {
    console.error("Ошибка при обработке результатов поиска:", error);
    statusMessage.value = error.message || 'Ошибка при поиске мест.';
    throw error;
  }
};

const searchPlaces = async () => {
  if (!cityQuery.value.trim()) return;

  isLoading.value = true;
  statusMessage.value = 'Определяем координаты города...';
  places.value = [];
  scrollPosition.value = 0;

  try {
    const targetCoords = await getCoordinates(cityQuery.value.trim());
    if (!targetCoords) {
      statusMessage.value = 'Город не найден';
      isLoading.value = false;
      return;
    }
    await processCoordinatesSearch(targetCoords.lat, targetCoords.lng, 30);
  } catch (error) {
    console.error(error);
    statusMessage.value = 'Не удалось загрузить данные. Попробуйте позже.';
  } finally {
    isLoading.value = false;
  }
};

const searchByGeolocation = () => {
  if (!navigator.geolocation) {
    statusMessage.value = 'Геолокация не поддерживается вашим браузером.';
    return;
  }

  isLoading.value = true;
  statusMessage.value = 'Запрашиваем доступ к GPS/геолокации...';
  places.value = [];
  cityQuery.value = '';
  scrollPosition.value = 0; 

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords;
      try {
        await processCoordinatesSearch(latitude, longitude, 30);
      } catch (error) {
        console.error(error);
        statusMessage.value = 'Ошибка при поиске мест вокруг вас.';
      } finally {
        isLoading.value = false;
      }
    },
    (error) => {
      isLoading.value = false;
      if (error.code === 1) {
        statusMessage.value = 'Вы запретили доступ к местоположению устройства.';
      } else {
        statusMessage.value = 'Не удалось определить ваше местоположение.';
      }
    },
    { enableHighAccuracy: true, timeout: 8000 }
  );
};
</script>

<style scoped>
.scroll-container {
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

.btn-star-favorite {
  background: none;
  border: none;
  padding: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.btn-star-favorite:hover {
  transform: scale(1.15);
}

.btn-star-favorite svg {
  transition: fill 0.2s ease, stroke 0.2s ease;
}
</style>