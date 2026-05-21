<template>
  <div id="map" class="w-100 h-100"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();

let myMap = null;
let mainClusterer = null;
const isInitialized = ref(false);
const dbFavoritesIds = ref(new Set());
const isAuthenticated = ref(false);

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

// Функция для получения CSRF-токена из куки
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

// Загрузка избранного из Django
const fetchDbFavorites = async () => {
  // Если  пользователь не залогинен, не отправляем запрос
  if (!isAuthenticated.value) {
    dbFavoritesIds.value = new Set();
    return;
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/');
    if (response.ok) {
      const data = await response.json();
      dbFavoritesIds.value = new Set(data.map(item => item.id));
    } else if (response.status === 401 || response.status === 403) {
      isAuthenticated.value = false;
      dbFavoritesIds.value = new Set();
    }
  } catch (e) {
    console.error("Не удалось подгрузить избранное:", e);
  }
};

// Загрузка данных из Wikidata
async function loadPlacesFromWikidata(classQID) {
  let categoryFilter;
  if (classQID === 'Q11742') {
    categoryFilter = `VALUES ?type { wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967 } ?place wdt:P31 ?type.`;
  } else if (classQID === 'Q862454') {
    categoryFilter = `VALUES ?type { wd:Q862454 wd:Q15631416 wd:Q3840711 } ?place wdt:P31 ?type.`;
  } else if (classQID === 'Q33506') {
    categoryFilter = `VALUES ?type { wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 wd:Q7075 } ?place wdt:P31 ?type.`;
   } else if (classQID === 'Q24354') {
    categoryFilter = `VALUES ?type { wd:Q11635 wd:Q153562 wd:Q1060165 wd:Q47928 wd:Q11812394 wd:Q16889960 } ?place wdt:P31 ?type.`;
  } else if (classQID === 'Q2035041') {
    categoryFilter = `VALUES ?type { wd:Q8502 } ?place wdt:P31 ?type.`;
  }

  const query = `
    SELECT DISTINCT ?place ?placeLabel ?coord ?image ?cityLabel WHERE {
      ?place wdt:P17 wd:Q159 . 
      ?place wdt:P625 ?coord .
      ${categoryFilter}
      ?place wdt:P18 ?image . 
      OPTIONAL { ?place wdt:P131 ?city. }
      FILTER NOT EXISTS { ?place wdt:P576 ?demolished. }
      FILTER NOT EXISTS { ?place wdt:P31/wdt:P279* wd:Q12269557. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru". }
    }
  `;

  const url = "https://query.wikidata.org/sparql";
  const params = new URLSearchParams({ query: query, format: 'json' });
  
  try {
    const response = await fetch(`${url}?${params}`);
    if (response.status === 429) return [];
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return data.results.bindings;
  } catch (e) {
    console.error("Ошибка Wikidata:", e);
    return [];
  }
}

// Переключение избранного
async function toggleFavorite(place, starElement) {

  if (!isAuthenticated.value) {
    alert("Для добавления в избранное, войдите в свой аккаунт или зарегистрируйтесь");
    router.push({ name: 'login' }); // Перенаправляем на страницу входа
    return;
  }

  const cityName = place.cityLabel ? place.cityLabel.value : "Неизвестно";
  try {
    const response = await fetch('http://127.0.0.1:8000/api/favorites/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'include',
      body: JSON.stringify({
        place_id: place.place.value,
        title: place.placeLabel.value,
        image_url: place.image ? place.image.value : null,
        coordinate: place.coord.value,
        city: cityName
      })
    });

    const result = await response.json();
    if (response.status === 401) {
      isAuthenticated.value = false;
      dbFavoritesIds.value = new Set();
      alert("Сессия истекла. Пожалуйста, войдите снова");
      return;
    }
    if (response.ok) {
      if (result.status === 'added') {
        starElement.style.color = '#ffc107';
        dbFavoritesIds.value.add(place.place.value);
      } else if (result.status === 'removed') {
        starElement.style.color = '#ccc';
        dbFavoritesIds.value.delete(place.place.value);
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
    });

    mainClusterer = new ymaps.Clusterer({
      preset: 'islands#invertedOliveClusterIcons', 
      groupByCoordinates: false,          // Не группировать только строго совпадающие координаты
      clusterDisableClickZoom: false,     // Зум при клике на кластер включен
      clusterHideIconOnBalloonOpen: false,
      geoObjectHideIconOnBalloonOpen: false
    });

    myMap.geoObjects.add(mainClusterer);
    const allPlacemarks = [];

    // Функция отрисовки
    const renderPlaces = (data, categoryKey) => {
      const placemarksToAddToCluster = [];

      data.forEach(item => {
        const placeId = item.place.value;
        const match = item.coord.value.match(/Point\(([-0-9.]+) ([-0-9.]+)\)/);
        if (!match) return;

        const isFav = dbFavoritesIds.value.has(placeId);
        const starColor = isFav ? '#ffc107' : '#ccc';
        const qid = item.place.value.split('/').pop();

        const html = `
          <div style="max-width: 200px; font-family: sans-serif;">
            <div style="display: flex; justify-content: space-between;">
              <strong style="font-size: 14px;">${item.placeLabel.value}</strong>
              <span class="favorite-star" data-id="${placeId}" 
                    style="cursor: pointer; font-size: 20px; color: ${starColor};">★</span>
            </div>
            ${item.image ? `<img src="${item.image.value}" class="balloon-img" style="width:100%; margin-top:8px; border-radius:4px;"/>` : ''}
            <div style="margin-top: 10px;">
              <a href="#" class="detail-link" data-qid="${qid}" style="color: #007bff; font-size: 13px; text-decoration: none;">Подробнее</a>
            </div>
          </div>`;

        // Создаем метку и задаем ей персональный иконку-пресет категории
        const placemark = new ymaps.Placemark(
          [parseFloat(match[2]), parseFloat(match[1])],
          { balloonContent: html },
          { preset: categoryPresets[categoryKey] }
        );

        // Сохраняем категорию прямо внутри параметров метки для фильтрации
        placemark.categoryId = categoryKey;

        allPlacemarks.push(placemark);
        placemarksToAddToCluster.push(placemark);
      });

      // Добавляем пачку меток в наш общий кластер
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

    // Делегирование
    document.addEventListener('click', async (e) => {
      const starBtn = e.target.closest('.favorite-star');
      if (starBtn) {
        e.stopPropagation();
        const placeId = starBtn.getAttribute('data-id');
        const allData = [...museumsData, ...parksData, ...embankmentsData, ...culturalData, ...viewsData];
        const place = allData.find(p => p.place.value === placeId);
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

    // Загрузка данных
    const sleep = (ms) => new Promise(res => setTimeout(res, ms));
    
    try {
      museumsData = await loadPlacesFromWikidata('Q33506');
      renderPlaces(museumsData, 'museums');
      await sleep(1000); 

      parksData = await loadPlacesFromWikidata('Q11742');
      renderPlaces(parksData, 'parks');
      await sleep(1000);

      embankmentsData = await loadPlacesFromWikidata('Q862454');
      renderPlaces(embankmentsData, 'embankments');
      await sleep(1000);

      culturalData = await loadPlacesFromWikidata('Q24354');
      renderPlaces(culturalData, 'cultural');
      await sleep(1000);

      viewsData = await loadPlacesFromWikidata('Q2035041');
      renderPlaces(viewsData, 'views');
      await sleep(1000);

      isInitialized.value = true;
    } catch (err) {
      console.error("Ошибка данных:", err);
    }
  });
});
</script>

<style>
:deep(.balloon-img) {
    background: url('https://i.gifer.com/ZKZg.gif') center center no-repeat;
    background-size: 30px;
    min-height: 100px;
    display: block;
}
</style>