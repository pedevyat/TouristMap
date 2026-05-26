<template>
  <div class="container scroll-container pt-4 text-black d-flex flex-column" style="height: 100vh;">
    
    <div class="search-panel pb-3">
      <h2 class="mb-4 text-black fw-bold">Подборка мест</h2>
      
      <div class="row mb-4">
        <div class="col-md-8">
          <label for="cityInput" class="form-label text-muted">Введите город или название объекта (например, Щепкинский лес)</label>
          <div class="input-group">
            <input 
              v-model="cityQuery" 
              @keyup.enter="searchPlaces"
              type="text" 
              id="cityInput" 
              class="form-control" 
              :disabled="isLoading"
              placeholder="Поиск..."
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
          <div class="card h-100 shadow-sm border-0 position-relative">
            <img 
              :src="item.image" 
              class="card-img-top" 
              alt="Фото объекта"
              style="height: 200px; object-fit: cover;"
            />
            <div class="card-body d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="card-title fw-bold text-dark fs-6 mb-0 me-2">{{ item.name }}</h5>
                <span class="favorite-star" 
                      @click="toggleFavorite(item)"
                      :style="{ cursor: 'pointer', fontSize: '22px', color: dbFavoritesIds.has(item.id) ? '#ffc107' : '#ccc', lineHeight: '1' }"
                      title="Добавить в избранное">
                  ★
                </span>
              </div>
              
              <p class="card-text text-muted small flex-grow-1">{{ item.description }}</p>
              
              <div class="mt-2 d-flex justify-content-between align-items-center">
                <span class="badge bg-secondary opacity-75">{{ item.distance }} км</span>
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
</template>

<script setup>
import { ref, onActivated, onDeactivated } from 'vue';
import { useRouter } from 'vue-router'; 
import { sendToggleFavoriteRequest } from '@/api/favoriteApi.js'; 

const router = useRouter();

const cityQuery = ref('');
const places = ref([]);
const isLoading = ref(false);
const statusMessage = ref('');
const scrollPosition = ref(0);
const isAuthenticated = ref(false);
const dbFavoritesIds = ref(new Set());

// Загрузка избранного и проверка сессии
const fetchDbFavorites = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      credentials: 'include'
    });
    if (response.ok) {
      const data = await response.json();
      dbFavoritesIds.value = new Set(data.map(item => item.id.split('/').pop()));
      isAuthenticated.value = true;
    } else if (response.status === 401 || response.status === 403) {
      isAuthenticated.value = false;
      dbFavoritesIds.value = new Set();
    }
  } catch (e) {
    console.error("Не удалось подгрузить статус избранного:", e);
  }
};

// Срабатывает, когда пользователь вернулся на эту страницу
onActivated(async () => {
  await fetchDbFavorites();
  window.scrollTo({
    top: scrollPosition.value,
    behavior: 'auto'
  });
});

// Срабатывает, когда пользователь уходит с этой страницы
onDeactivated(() => {
  scrollPosition.value = window.scrollY || window.pageYOffset;
});

// Функция добавления/удаления
const toggleFavorite = async (item) => {
  if (!isAuthenticated.value) {
    alert("Для добавления в избранное, войдите в свой аккаунт или зарегистрируйтесь");
    router.push({ name: 'login' });
    return;
  }

  const apiPlaceParam = {
    place: { value: item.rawUri },
    placeLabel: { value: item.name },
    image: item.image && !item.image.includes('placehold.co') ? { value: item.image } : null,
    coord: { value: item.coord },
    cityLabel: { value: cityQuery.value.trim()  }
  };

  try {
    const result = await sendToggleFavoriteRequest(apiPlaceParam);

    if (result.status === 401) {
      isAuthenticated.value = false;
      dbFavoritesIds.value = new Set();
      alert("Сессия истекла. Пожалуйста, войдите снова");
      router.push({ name: 'login' });
      return;
    }

    if (result.ok) {
      if (result.data.status === 'added') {
        dbFavoritesIds.value.add(item.id);
      } else if (result.data.status === 'removed') {
        dbFavoritesIds.value.delete(item.id);
      }
    }
  } catch (e) {
    console.error("Сетевая ошибка при изменении избранного:", e);
    alert("Не удалось сохранить в избранное. Проверьте соединение с сервером");
  }
};

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

// Расчет углов
const getBoundingBox = (lat, lng, radiusInKm = 30) => {
  const latDelta = radiusInKm / 111;
  const lngDelta = radiusInKm / (111.32 * Math.cos(lat * Math.PI / 180));
  return {
    minLat: lat - latDelta,
    maxLat: lat + latDelta,
    minLng: lng - lngDelta,
    maxLng: lng + lngDelta
  };
};

// Поиск объектов напрямую по текстовому названию
const fetchPlacesByName = async (textQuery) => {
  const query = `
    SELECT DISTINCT ?place ?placeLabel ?coord ?image ?description WHERE {
      # Полнотекстовый поиск Wikidata по ключевым словам
      SERVICE wikibase:mwapi {
        bd:serviceParam wikibase:api "EntitySearch" .
        bd:serviceParam wikibase:endpoint "www.wikidata.org" .
        bd:serviceParam mwapi:search "${textQuery}" .
        bd:serviceParam mwapi:language "ru" .
        ?place wikibase:apiOutputItem mwapi:item .
      }
      
      ?place wdt:P17 wd:Q159 . 
      ?place wdt:P625 ?coord . 
      
      # Проверка соответствия категориям проекта
      VALUES ?type { 
        wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 wd:Q7075 # Музеи
        wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967          # Парки
        wd:Q862454 wd:Q15631416 wd:Q3840711                 # Набережные
        wd:Q11635 wd:Q153562 wd:Q1060165 wd:Q47928          # Культура
        wd:Q8502                                            # Смотровые
      }
      ?place wdt:P31 ?type .
      
      OPTIONAL { ?place wdt:P18 ?image . }
      OPTIONAL { ?place schema:description ?description . FILTER(LANG(?description) = "ru") }
      FILTER NOT EXISTS { ?place wdt:P576 ?demolished. }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru". }
    }
  `;

  const url = "https://query.wikidata.org/sparql";
  const params = new URLSearchParams({ query: query, format: 'json' });
  
  const response = await fetch(`${url}?${params}`);
  if (!response.ok) throw new Error(`Ошибка сервера Wikidata: ${response.status}`);
  
  const data = await response.json();
  return data.results.bindings;
};

// Запрос к Wikidata по радиусу
const fetchPlacesInRadius = async (lat, lng, radiusInKm = 30) => {
  const box = getBoundingBox(lat, lng, radiusInKm);

  const query = `
    SELECT DISTINCT ?place ?placeLabel ?coord ?image ?description WHERE {
      SERVICE wikibase:box {
        ?place wdt:P625 ?coord .
        bd:serviceParam wikibase:cornerSouthWest "Point(${box.minLng} ${box.minLat})"^^geo:wktLiteral .
        bd:serviceParam wikibase:cornerNorthEast "Point(${box.maxLng} ${box.maxLat})"^^geo:wktLiteral .
      }
      VALUES ?type { 
        wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 wd:Q7075 # Музеи
        wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967          # Парки
        wd:Q862454 wd:Q15631416 wd:Q3840711                 # Набережные
        wd:Q11635 wd:Q153562 wd:Q1060165 wd:Q47928          # Культура
        wd:Q8502                                            # Смотровые
      }
      ?place wdt:P31 ?type .
      ?place wdt:P18 ?image .  
      
      OPTIONAL { ?place schema:description ?description . FILTER(LANG(?description) = "ru") }
      FILTER NOT EXISTS { ?place wdt:P576 ?demolished. }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru". }
    }
  `;

  const url = "https://query.wikidata.org/sparql";
  const params = new URLSearchParams({ query: query, format: 'json' });
  
  const response = await fetch(`${url}?${params}`);
  if (!response.ok) throw new Error(`Ошибка сервера Wikidata: ${response.status}`);
  
  const data = await response.json();
  return data.results.bindings;
};

const processCoordinatesSearch = async (lat, lng, radiusInKm = 30) => {
  statusMessage.value = `Ищем интересные места в радиусе ${radiusInKm} км...`;
  
  const rawData = await fetchPlacesInRadius(lat, lng, radiusInKm);
  
  const filtered = [];
  for (const item of rawData) {
    if (!item.coord?.value) continue;
    
    const match = item.coord.value.match(/Point\(([-\d.]+)\s+([-\d.]+)\)/);
    if (match) {
      const itemLng = parseFloat(match[1]);
      const itemLat = parseFloat(match[2]);
      
      const distance = calculateDistance(lat, lng, itemLat, itemLng);
      
      if (distance <= radiusInKm) {
        filtered.push({
          id: item.place.value.split('/').pop(),
          name: item.placeLabel?.value,
          description: item.description?.value,
          image: item.image?.value || 'https://placehold.co/600x400?text=Нет+фото',
          distance: distance.toFixed(1),
          coord: item.coord.value,
          rawUri: item.place.value
        });
      }
    }
  }

  filtered.sort((a, b) => a.distance - b.distance);
  places.value = filtered;

  if (places.value.length === 0) {
    statusMessage.value = `Ничего не найдено`;
  } else {
    statusMessage.value = `Успешно найдено мест: ${places.value.length}`;
  }
};

const searchPlaces = async () => {
  const queryText = cityQuery.value.trim();
  if (!queryText) return;

  isLoading.value = true;
  statusMessage.value = 'Загрузка...';
  places.value = [];
  scrollPosition.value = 0;

  try {
    // сначала пробуем найти конкретные сущности по имени текстовым поиском Wikidata
    const rawNameData = await fetchPlacesByName(queryText);
    
    // параллельно запросим координаты через Яндекс для расчета расстояния до искомого объекта
    let refCoords = null;
    try {
      refCoords = await getCoordinates(queryText);
    } catch (err) {
      console.warn("Не удалось определить точку привязки координат для текста:", err);
    }

    if (rawNameData && rawNameData.length > 0) {
      const filtered = [];
      for (const item of rawNameData) {
        if (!item.coord?.value) continue;
        
        const match = item.coord.value.match(/Point\(([-\d.]+)\s+([-\d.]+)\)/);
        if (match) {
          const itemLng = parseFloat(match[1]);
          const itemLat = parseFloat(match[2]);
          
          // расстояние считаем от найденной геокодером точки объекта (будет около 0 км для точного совпадения)
          const distance = refCoords ? calculateDistance(refCoords.lat, refCoords.lng, itemLat, itemLng) : 0;
          
          filtered.push({
            id: item.place.value.split('/').pop(),
            name: item.placeLabel?.value,
            description: item.description?.value,
            image: item.image?.value || 'https://placehold.co/600x400?text=Нет+фото',
            distance: distance.toFixed(1),
            coord: item.coord.value,
            rawUri: item.place.value
          });
        }
      }
      
      places.value = filtered.sort((a, b) => a.distance - b.distance);
      statusMessage.value = `Найдено объектов по названию: ${filtered.length}`;
      isLoading.value = false;
      return; // Завершаем выполнение, так как нашли точечные объекты
    }

    // если текстовый поиск ничего не дал, значит ввели город
    statusMessage.value = 'Ищем интересные места в радиусе 30 км...';
    
    if (!refCoords) {
      statusMessage.value = 'Ничего не найдено';
      isLoading.value = false;
      return;
    }
    
    await processCoordinatesSearch(refCoords.lat, refCoords.lng, 30);

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
</style>