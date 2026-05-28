<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';
import { useRouter } from 'vue-router';
import { sendToggleFavoriteRequest } from '@/api/favoriteApi.js';
import { placesApi } from '@/api/placesApi.js';

const router = useRouter();

let myMap = null;
let mainClusterer = null;
const isInitialized = ref(false);
const dbFavoritesIds = ref(new Set());
const isAuthenticated = ref(false);
const mapRef = ref(null); 
let mapResizeObserver = null;

// Списки объектов теперь будут хранить чистые плоские массивы от Django
let museumsData = [];
let parksData = [];
let embankmentsData = [];
let culturalData = [];
let viewsData = [];

const categoryPresets = {
  museums: 'islands#redLeisureCircleIcon',
  parks: 'islands#greenParkCircleIcon',
  embankments: 'islands#blueWaterParkCircleIcon',
  cultural: 'islands#brownTheaterCircleIcon',
  views: 'islands#violetObservationCircleIcon'
};

const activeCategories = {
  museums: true,
  parks: true,
  embankments: true,
  cultural: true,
  views: true
};

// --- ЛОГИКА API ---

// Загрузка избранного из Django (сохраняем, очистив ID до QID)
const fetchDbFavorites = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      // Храним чистые QID (например, 'Q12345'), как и в SelectionView
      dbFavoritesIds.value = new Set(data.map(item => item.id.split('/').pop()));
      isAuthenticated.value = true;
    } else if (response.status === 401 || response.status === 403) {
      isAuthenticated.value = false;
      dbFavoritesIds.value = new Set();
    }
  } catch (e) {
    console.error("Не удалось подгрузить избранное:", e);
    isAuthenticated.value = false;
  }
};

// Переключение избранного (адаптировано под плоскую структуру)
async function toggleFavorite(place, starElement) {
  if (!isAuthenticated.value) {
    alert("Для добавления в избранное, войдите в свой аккаунт или зарегистрируйтесь");
    router.push({ name: 'login' });
    return;
  }

  // Приводим объект к формату, который ожидает твоя функция sendToggleFavoriteRequest
  const apiPlaceParam = {
    place: { value: `http://www.wikidata.org/entity/${place.id}` },
    placeLabel: { value: place.name },
    image: place.image && !place.image.includes('placehold.co') ? { value: place.image } : null,
    coord: { value: place.coord },
    cityLabel: { value: place.city || "Неизвестно" }
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
        starElement.style.color = '#ffc107';
        dbFavoritesIds.value.add(place.id);
      } else if (result.data.status === 'removed') {
        starElement.style.color = '#ccc';
        dbFavoritesIds.value.delete(place.id);
      }
    }
  } catch (e) {
    console.error("Сетевая ошибка при добавлении в избранное:", e);
    alert("Не удалось сохранить в избранное. Проверьте соединение с сервером");
  }
}

// --- КАРТА ---

onMounted(() => {
  if (isInitialized.value) return;

  const mapContainer = document.getElementById('map');
  if (mapContainer) {
    mapResizeObserver = new ResizeObserver(() => {
      if (typeof myMap !== 'undefined' && myMap && myMap.container) {
        myMap.container.fitToViewport();
      }
    });
    mapResizeObserver.observe(mapContainer);
  }

  ymaps.ready(async () => {
    try {
      const authCheck = await fetch('http://127.0.0.1:8000/api/login/', { credentials: 'include' });
      if (authCheck.ok) {
        const userData = await authCheck.json();
        if (userData.username) {
          isAuthenticated.value = true;
        }
      }
    } catch (e) {
      console.log("Пользователь не авторизован");
    }
    
    await fetchDbFavorites();

    myMap = new ymaps.Map("map", {
      center: [47.24, 39.71],
      zoom: 11,
      controls: ['zoomControl', 'typeSelector']
    }, {
      autoFitToViewport: 'always'
    });

    mainClusterer = new ymaps.Clusterer({
      preset: 'islands#invertedOliveClusterIcons', 
      groupByCoordinates: false,
      clusterDisableClickZoom: false,
      clusterHideIconOnBalloonOpen: false,
      geoObjectHideIconOnBalloonOpen: false
    });

    myMap.geoObjects.add(mainClusterer);
    const allPlacemarks = [];

    // 2. РЕФАКТОРИНГ: Отрисовка работает с плоскими полями (без .value)
    const renderPlaces = (data, categoryKey) => {
      const placemarksToAddToCluster = [];

      data.forEach(item => {
        const placeId = item.id; // Чистый QID
        const match = item.coord.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
        if (!match) return;

        const isFav = dbFavoritesIds.value.has(placeId);
        const starColor = isFav ? '#ffc107' : '#ccc';

        const html = `
          <div style="max-width: 200px; font-family: sans-serif;">
            <div style="display: flex; justify-content: space-between;">
              <strong style="font-size: 14px;">${item.name}</strong>
              <span class="favorite-star" data-id="${placeId}" 
                    style="cursor: pointer; font-size: 20px; color: ${starColor};">★</span>
            </div>
            ${item.image ? `<img src="${item.image}" class="balloon-img" style="width:100%; margin-top:8px; border-radius:4px;"/>` : ''}
            <div style="margin-top: 10px;">
              <a href="#" class="detail-link" data-qid="${placeId}" style="color: #007bff; font-size: 13px; text-decoration: none;">Подробнее</a>
            </div>
          </div>`;

        const placemark = new ymaps.Placemark(
          [parseFloat(match[2]), parseFloat(match[1])],
          { balloonContent: html },
          { preset: categoryPresets[categoryKey] }
        );

        placemark.categoryId = categoryKey;
        allPlacemarks.push(placemark);
        placemarksToAddToCluster.push(placemark);
      });

      mainClusterer.add(placemarksToAddToCluster);
    };

    const updateClustererFilter = () => {
      mainClusterer.removeAll();
      const filteredPlacemarks = allPlacemarks.filter(pm => activeCategories[pm.categoryId]);
      mainClusterer.add(filteredPlacemarks);
    };

    const createMenuItem = (label, categoryKey) => {
      const item = new ymaps.control.ListBoxItem({ 
        data: { content: label }, 
        state: { selected: true }
      });

      item.events.add('click', () => {
        activeCategories[categoryKey] = !item.isSelected();
        updateClustererFilter();
      });
      return item;
    };

    const listBox = new ymaps.control.ListBox({
      data: { content: 'Категории' },
      items: [
        createMenuItem('Музеи', 'museums'),
        createMenuItem('Парки', 'parks'),
        createMenuItem('Набережные', 'embankments'),
        createMenuItem('Культурные места', 'cultural'),
        createMenuItem('Смотровые площадки', 'views'),
      ],
      options: { float: 'right' }
    });
    myMap.controls.add(listBox);

    // Делегирование кликов в балунах
    document.addEventListener('click', async (e) => {
      const starBtn = e.target.closest('.favorite-star');
      if (starBtn) {
        e.stopPropagation();
        const placeId = starBtn.getAttribute('data-id');
        const allData = [...museumsData, ...parksData, ...embankmentsData, ...culturalData, ...viewsData];
        const place = allData.find(p => p.id === placeId);
        if (place) await toggleFavorite(place, starBtn);
        return;
      }

      const detailLink = e.target.closest('.detail-link');
      if (detailLink) {
        e.preventDefault();
        const qid = detailLink.getAttribute('data-qid');
        router.push({ name: 'Place', params: { id: qid } });
      }
    });

    // Загрузка данных: теперь строго по очереди, чтобы не перегружать Wikidata
    try {
      // 1. Музеи
      museumsData = await placesApi.getByCategory('Q33506');
      if (museumsData.length) renderPlaces(museumsData, 'museums');

      // 2. Парки
      parksData = await placesApi.getByCategory('Q11742');
      if (parksData.length) renderPlaces(parksData, 'parks');

      // 3. Набережные
      embankmentsData = await placesApi.getByCategory('Q862454');
      if (embankmentsData.length) renderPlaces(embankmentsData, 'embankments');

      // 4. Культурные места
      culturalData = await placesApi.getByCategory('Q24354');
      if (culturalData.length) renderPlaces(culturalData, 'cultural');

      // 5. Смотровые площадки
      viewsData = await placesApi.getByCategory('Q2035041');
      if (viewsData.length) renderPlaces(viewsData, 'views');

      isInitialized.value = true;
    } catch (err) {
      console.error("Ошибка при поочередной загрузке данных:", err);
    }
  });
});

onBeforeUnmount(() => {
  if (mapResizeObserver) {
    mapResizeObserver.disconnect();
  }
});
</script>

<style scoped>
#map {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}

:deep(.balloon-img) {
    background: url('https://i.gifer.com/ZKZg.gif') center center no-repeat;
    background-size: 30px;
    min-height: 100px;
    display: block;
}
</style>